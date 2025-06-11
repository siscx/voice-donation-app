#app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import traceback  # Added for debugging
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


# Complete voice donation endpoint (audio + questionnaire)
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

        # Extract features from audio
        from utils.feature_extraction import extract_all_features

        # Prepare request info for metadata
        request_info = {
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'unknown'),
            'method': request.method
        }

        # Process audio and extract features
        print("Processing audio...")
        audio_data = file.read()
        features_result = extract_all_features(audio_data, file.filename, request_info)

        if not features_result.get('summary', {}).get('processing_successful', False):
            print(f"Audio processing failed: {features_result.get('processing_error', 'Unknown error')}")
            return jsonify({
                'error': 'Audio processing failed',
                'details': features_result.get('processing_error', 'Unknown error')
            }), 500

        # Save complete record to database
        from utils.database import save_voice_donation
        recording_id = features_result['metadata']['recording_id']

        print(f"Saving to database with recording_id: {recording_id}")
        db_result = save_voice_donation(
            recording_id=recording_id,
            audio_features=features_result,
            questionnaire_data=questionnaire_result['data'],
            metadata=features_result['metadata']
        )

        if db_result['success']:
            print("SUCCESS: Voice donation completed")
            return jsonify({
                'success': True,
                'recording_id': recording_id,
                'message': 'Voice donation completed successfully',
                'features_extracted': features_result['summary']['total_features_extracted'],
                'audio_quality': features_result['quality_metrics']['signal_quality']
            }), 200
        else:
            print(f"Database save failed: {db_result['error']}")
            return jsonify({
                'error': 'Failed to save data',
                'details': db_result['error']
            }), 500

    except Exception as e:
        print(f"VOICE DONATION ERROR: {e}")
        print("Full traceback:")
        print(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'message': 'Failed to process voice donation'
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)