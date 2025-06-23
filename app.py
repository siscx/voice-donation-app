# app.py - Clean version for Railway deployment

# Basic imports
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import traceback
import threading
import uuid
import json
from datetime import datetime
from dotenv import load_dotenv

print("Starting voice donation API...")

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


# Test AWS connection function
def test_aws_connection():
    """Test AWS connectivity"""
    try:
        import boto3

        # Check credentials
        aws_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_REGION')

        print(f"AWS credentials present: {bool(aws_key and aws_secret)}")
        print(f"AWS region: {aws_region}")

        if not all([aws_key, aws_secret, aws_region]):
            return False, "Missing AWS credentials"

        # Simple connection test
        try:
            dynamodb = boto3.resource('dynamodb',
                                      aws_access_key_id=aws_key,
                                      aws_secret_access_key=aws_secret,
                                      region_name=aws_region)

            # Quick test - just check if we can list one table
            tables = list(dynamodb.tables.limit(1))
            print("AWS connection successful")
            return True, "Connected"

        except Exception as e:
            print(f"AWS connection failed: {e}")
            return False, str(e)

    except Exception as e:
        print(f"AWS test error: {e}")
        return False, str(e)


# Test AWS on startup
aws_connected, aws_message = test_aws_connection()
print(f"AWS Status: {aws_connected} - {aws_message}")

# In-memory storage for pending multi-task submissions
pending_submissions = {}


# Routes
@app.route('/')
def home():
    return send_from_directory('static', 'index.html')


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


@app.route('/health-basic', methods=['GET'])
def health_check_basic():
    return jsonify({
        'status': 'healthy',
        'message': 'Basic app running',
        'aws_connected': aws_connected
    })


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Voice Donation API is running',
        'aws_status': aws_message
    })


@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        'message': 'API is working!',
        'aws_configured': bool(os.getenv('AWS_ACCESS_KEY_ID')),
        'aws_connected': aws_connected
    })


# AWS-dependent routes (only if AWS is connected)
if aws_connected:
    @app.route('/api/test-aws', methods=['GET'])
    def test_aws():
        from utils.aws_helpers import test_s3_connection
        result = test_s3_connection()
        return jsonify(result)


    @app.route('/api/test-database', methods=['GET'])
    def test_database():
        from utils.database import test_database_connection
        result = test_database_connection()
        return jsonify(result)


    @app.route('/api/setup-database', methods=['POST'])
    def setup_database():
        from utils.database import create_tables
        result = create_tables()
        return jsonify(result)


    @app.route('/api/questionnaire-schema', methods=['GET'])
    def get_questionnaire_schema():
        from utils.questionnaire import get_questionnaire_schema
        schema = get_questionnaire_schema()
        return jsonify({"schema": schema})


    @app.route('/api/upload-audio', methods=['POST'])
    def upload_audio():
        try:
            if 'audio' not in request.files:
                return jsonify({'error': 'No audio file provided'}), 400

            file = request.files['audio']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400

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


    # Voice donation endpoint
    @app.route('/api/voice-donation', methods=['POST'])
    def voice_donation():
        try:
            print("Voice donation request received")

            if 'audio' not in request.files:
                return jsonify({'error': 'No audio file provided'}), 400

            file = request.files['audio']
            questionnaire_data = request.form.get('questionnaire')

            if not questionnaire_data:
                return jsonify({'error': 'No questionnaire data provided'}), 400

            questionnaire_json = json.loads(questionnaire_data)

            # Validate questionnaire
            from utils.questionnaire import process_questionnaire_data
            questionnaire_result = process_questionnaire_data(questionnaire_json)

            if not questionnaire_result['success']:
                return jsonify({
                    'error': 'Invalid questionnaire data',
                    'details': questionnaire_result['errors']
                }), 400

            # Generate IDs
            recording_id = str(uuid.uuid4())
            task_metadata = questionnaire_json.get('task_metadata', {})
            donation_id = task_metadata.get('donation_id', recording_id)

            # Read audio data
            audio_data = file.read()
            if len(audio_data) == 0:
                return jsonify({'error': 'Empty audio file'}), 400

            # Request info for metadata
            request_info = {
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'unknown'),
                'method': request.method
            }

            # Check if multi-task
            is_multi_task = task_metadata.get('total_tasks', 1) > 1

            if is_multi_task:
                # Store task submission
                success = store_task_submission(
                    recording_id=recording_id,
                    donation_id=donation_id,
                    audio_data=audio_data,
                    filename=file.filename,
                    questionnaire_result=questionnaire_result,
                    request_info=request_info
                )

                if not success:
                    return jsonify({'error': 'Failed to store task submission'}), 500

                # Check if all tasks submitted
                if should_start_processing(donation_id, task_metadata.get('total_tasks', 2)):
                    print(f"Starting background processing for {donation_id}")
                    start_multi_task_processing(donation_id)
            else:
                # Single task processing
                from utils.database import save_initial_voice_donation
                save_initial_voice_donation(
                    recording_id=recording_id,
                    questionnaire_data=questionnaire_result['data'],
                    audio_filename=file.filename,
                    audio_size=len(audio_data),
                    request_info=request_info
                )

                processing_thread = threading.Thread(
                    target=process_audio_background,
                    args=(recording_id, audio_data, file.filename, questionnaire_result, request_info),
                    daemon=True
                )
                processing_thread.start()

            print(f"Returning response for {donation_id}")

            return jsonify({
                'success': True,
                'recording_id': recording_id,
                'donation_id': donation_id,
                'message': 'Voice donation submitted successfully',
                'status': 'submitted'
            }), 200

        except Exception as e:
            print(f"Voice donation error: {e}")
            print(traceback.format_exc())
            return jsonify({
                'error': str(e),
                'message': 'Failed to process voice donation'
            }), 500


    @app.route('/api/donation-status/<donation_id>', methods=['GET'])
    def check_donation_status(donation_id):
        try:
            from utils.database import get_donation_recordings_status
            result = get_donation_recordings_status(donation_id)

            if not result['success']:
                return jsonify({'error': 'Donation not found'}), 404

            return jsonify({
                'donation_id': donation_id,
                'recordings': result['recordings'],
                'donation_status': result['donation_status'],
                'completed_count': result['completed_count'],
                'total_count': result['total_count']
            }), 200

        except Exception as e:
            print(f"Donation status error: {e}")
            return jsonify({'error': str(e)}), 500

else:
    # AWS not available - provide error endpoints
    @app.route('/api/voice-donation', methods=['POST'])
    def voice_donation_no_aws():
        return jsonify({
            'error': 'AWS services unavailable',
            'message': f'Cannot process donations: {aws_message}'
        }), 503


# Helper functions
def store_task_submission(recording_id, donation_id, audio_data, filename, questionnaire_result, request_info):
    try:
        if donation_id not in pending_submissions:
            pending_submissions[donation_id] = {}

        task_num = questionnaire_result['data']['task_metadata']['task_number']
        pending_submissions[donation_id][task_num] = {
            'recording_id': recording_id,
            'audio_data': audio_data,
            'filename': filename,
            'questionnaire_result': questionnaire_result,
            'request_info': request_info,
            'submitted_at': datetime.utcnow().isoformat()
        }

        print(f"Stored task {task_num} for donation {donation_id}")
        return True
    except Exception as e:
        print(f"Error storing task: {e}")
        return False


def should_start_processing(donation_id, total_tasks):
    if donation_id not in pending_submissions:
        return False
    submitted_tasks = len(pending_submissions[donation_id])
    print(f"Donation {donation_id}: {submitted_tasks}/{total_tasks} tasks submitted")
    return submitted_tasks >= total_tasks


def start_multi_task_processing(donation_id):
    processing_thread = threading.Thread(
        target=process_multi_task_background,
        args=(donation_id,),
        daemon=True
    )
    processing_thread.start()


def process_multi_task_background(donation_id):
    try:
        print(f"Background processing started: {donation_id}")

        if donation_id not in pending_submissions:
            print(f"ERROR: No submissions for {donation_id}")
            return

        tasks = pending_submissions[donation_id]

        for task_num in sorted(tasks.keys()):
            task_data = tasks[task_num]
            print(f"Processing task {task_num}")

            try:
                from utils.database import save_initial_voice_donation
                save_initial_voice_donation(
                    recording_id=task_data['recording_id'],
                    questionnaire_data=task_data['questionnaire_result']['data'],
                    audio_filename=task_data['filename'],
                    audio_size=len(task_data['audio_data']),
                    request_info=task_data['request_info']
                )

                process_audio_background(
                    task_data['recording_id'],
                    task_data['audio_data'],
                    task_data['filename'],
                    task_data['questionnaire_result'],
                    task_data['request_info']
                )

                print(f"Completed task {task_num}")
            except Exception as e:
                print(f"Task {task_num} error: {e}")

        del pending_submissions[donation_id]
        print(f"Completed all tasks for donation: {donation_id}")
    except Exception as e:
        print(f"Background processing error: {e}")


def process_audio_background(recording_id, audio_data, filename, questionnaire_result, request_info):
    try:
        print(f"Starting audio processing for {recording_id}")

        from utils.feature_extraction import extract_all_features
        features_result = extract_all_features(audio_data, filename, request_info)

        if features_result.get('summary', {}).get('processing_successful', False):
            from utils.database import save_voice_donation_features
            db_result = save_voice_donation_features(
                recording_id=recording_id,
                audio_features=features_result,
                questionnaire_data=questionnaire_result['data'],
                metadata=features_result['metadata']
            )
            print(f"Processing completed for {recording_id}: {db_result['success']}")
        else:
            print(f"Feature extraction failed for {recording_id}")
    except Exception as e:
        print(f"Audio processing error for {recording_id}: {e}")


print("All routes configured")

if __name__ == '__main__':
    # Force port 5000 to match Railway networking config
    port = 5000
    host = '0.0.0.0'

    print(f"Starting server on {host}:{port}")
    app.run(debug=False, host=host, port=port, threaded=True)