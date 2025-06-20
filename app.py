# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import traceback
import threading
import uuid
from datetime import datetime
from dotenv import load_dotenv
from flask import send_from_directory

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Basic configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


@app.route('/')
def home():
    return send_from_directory('static', 'index.html')


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Voice Donation API is running'
    })


# Test endpoint
@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        'message': 'API is working!',
        'aws_configured': bool(os.getenv('AWS_ACCESS_KEY_ID'))
    })


# AWS connection test
@app.route('/api/test-aws', methods=['GET'])
def test_aws():
    from utils.aws_helpers import test_s3_connection
    result = test_s3_connection()
    return jsonify(result)


# Database connection test
@app.route('/api/test-database', methods=['GET'])
def test_database():
    from utils.database import test_database_connection
    result = test_database_connection()
    return jsonify(result)


# Create database tables
@app.route('/api/setup-database', methods=['POST'])
def setup_database():
    from utils.database import create_tables
    result = create_tables()
    return jsonify(result)


# Get questionnaire schema
@app.route('/api/questionnaire-schema', methods=['GET'])
def get_questionnaire_schema():
    from utils.questionnaire import get_questionnaire_schema
    schema = get_questionnaire_schema()
    return jsonify({"schema": schema})


# Audio upload endpoint
@app.route('/api/upload-audio', methods=['POST'])
def upload_audio():
    try:
        # Check if file is in request
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        file = request.files['audio']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Upload to S3
        from utils.aws_helpers import upload_audio_file
        result = upload_audio_file(file.read(), file.filename)

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500

    except Exception as e:
        print(f"UPLOAD ERROR: {e}")
        print(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'message': 'Failed to process audio upload'
        }), 500


def process_audio_background(recording_id, audio_data, filename, questionnaire_result, request_info):
    """Background function to process audio features"""
    try:
        print(f"Starting background processing for {recording_id}")

        # Extract features from audio
        from utils.feature_extraction import extract_all_features

        # Process audio and extract features
        features_result = extract_all_features(audio_data, filename, request_info)

        if not features_result.get('summary', {}).get('processing_successful', False):
            # Update database with failed status
            from utils.database import update_voice_donation_status
            update_voice_donation_status(recording_id, 'failed', error=features_result.get('processing_error'))
            print(f"Audio processing failed for {recording_id}: {features_result.get('processing_error')}")
            return

        # Save complete record to database
        from utils.database import save_voice_donation_features
        db_result = save_voice_donation_features(
            recording_id=recording_id,
            audio_features=features_result,
            questionnaire_data=questionnaire_result['data'],
            metadata=features_result['metadata']
        )

        if db_result['success']:
            print(f"Successfully completed processing for {recording_id}")
        else:
            print(f"Database save failed for {recording_id}: {db_result['error']}")
            # Update status to failed
            from utils.database import update_voice_donation_status
            update_voice_donation_status(recording_id, 'failed', error=db_result['error'])

    except Exception as e:
        print(f"Background processing error for {recording_id}: {e}")
        print(traceback.format_exc())
        # Update database with failed status
        try:
            from utils.database import update_voice_donation_status
            update_voice_donation_status(recording_id, 'failed', error=str(e))
        except:
            pass  # Avoid infinite error loops


# Complete voice donation endpoint (audio + questionnaire) - ASYNC VERSION
@app.route('/api/voice-donation', methods=['POST'])
def voice_donation():
    try:
        print("=== VOICE DONATION REQUEST RECEIVED ===")

        # Debug: Print request details
        print(f"Content-Type: {request.content_type}")
        print(f"Form keys: {list(request.form.keys())}")
        print(f"Files: {list(request.files.keys())}")

        # Check if file is in request
        if 'audio' not in request.files:
            print("ERROR: No audio file in request")
            return jsonify({'error': 'No audio file provided'}), 400

        file = request.files['audio']
        if file.filename == '':
            print("ERROR: Empty filename")
            return jsonify({'error': 'No file selected'}), 400

        print(f"Audio file received: {file.filename}, size: {file.content_length}")

        # Get questionnaire data
        questionnaire_data = request.form.get('questionnaire')
        if not questionnaire_data:
            print("ERROR: No questionnaire data")
            return jsonify({'error': 'No questionnaire data provided'}), 400

        print(f"Questionnaire data received: {questionnaire_data}")

        # Parse questionnaire JSON
        import json
        try:
            questionnaire_json = json.loads(questionnaire_data)
            print(f"Parsed questionnaire: {questionnaire_json}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return jsonify({'error': 'Invalid questionnaire data format'}), 400

        # Validate questionnaire
        from utils.questionnaire import process_questionnaire_data
        print("Processing questionnaire data...")
        questionnaire_result = process_questionnaire_data(questionnaire_json)
        print(f"Questionnaire result: {questionnaire_result}")

        if not questionnaire_result['success']:
            print(f"Questionnaire validation failed: {questionnaire_result['errors']}")
            return jsonify({
                'error': 'Invalid questionnaire data',
                'details': questionnaire_result['errors']
            }), 400

        # Generate unique recording ID
        recording_id = str(uuid.uuid4())

        # NEW: Extract or generate donation ID
        questionnaire_json = json.loads(questionnaire_data)
        task_metadata = questionnaire_json.get('task_metadata', {})
        donation_id = task_metadata.get('donation_id', recording_id)  # Use recording_id as fallback

        print(f"Generated recording_id: {recording_id}, donation_id: {donation_id}")

        # Read audio data
        audio_data = file.read()
        if len(audio_data) == 0:
            return jsonify({'error': 'Empty audio file'}), 400

        # Create initial database record with "processing" status
        from utils.database import save_initial_voice_donation

        # Prepare request info for metadata
        request_info = {
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'unknown'),
            'method': request.method
        }

        # Save initial record
        initial_result = save_initial_voice_donation(
            recording_id=recording_id,
            questionnaire_data=questionnaire_result['data'],
            audio_filename=file.filename,
            audio_size=len(audio_data),
            request_info=request_info
        )

        if not initial_result['success']:
            print(f"Failed to save initial record: {initial_result['error']}")
            return jsonify({
                'error': 'Failed to save initial data',
                'details': initial_result['error']
            }), 500

        # Start background processing thread
        processing_thread = threading.Thread(
            target=process_audio_background,
            args=(recording_id, audio_data, file.filename, questionnaire_result, request_info),
            daemon=True
        )
        processing_thread.start()

        print("SUCCESS: Voice donation submitted, processing started in background")

        # BACKGROUND: Return success immediately - user can leave
        return jsonify({
            'success': True,
            'recording_id': recording_id,
            'donation_id': donation_id,
            'message': 'Thank you! Your voice donation has been submitted successfully.',
            'status': 'submitted',  # Changed from 'processing'
            'processing_info': 'Your recordings are being processed to help advance medical research.',
            'task_info': task_metadata if task_metadata else None
        }), 200

    except Exception as e:
        print(f"VOICE DONATION ERROR: {e}")
        print("Full traceback:")
        print(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'message': 'Failed to process voice donation'
        }), 500


# Donation status check
@app.route('/api/donation-status/<donation_id>', methods=['GET'])
def check_donation_status(donation_id):
    """Check status of all recordings in a donation"""
    try:
        from utils.database import get_donation_recordings_status

        result = get_donation_recordings_status(donation_id)

        if not result['success']:
            return jsonify({
                'error': 'Donation not found',
                'donation_id': donation_id
            }), 404

        return jsonify({
            'donation_id': donation_id,
            'recordings': result['recordings'],
            'donation_status': result['donation_status'],
            'completed_count': result['completed_count'],
            'total_count': result['total_count']
        }), 200

    except Exception as e:
        print(f"DONATION STATUS CHECK ERROR: {e}")
        return jsonify({
            'error': str(e),
            'message': 'Failed to check donation status'
        }), 500

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)

# Cloud Run
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))  # Cloud Run uses PORT env variable
    app.run(debug=False, host='0.0.0.0', port=port)