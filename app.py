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
from threading import Semaphore
import psutil

# Memory protection
MAX_CONCURRENT_PROCESSING = 2
processing_semaphore = Semaphore(MAX_CONCURRENT_PROCESSING)

print("Starting voice donation API...")

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def check_memory_usage():
    """Check current memory usage"""
    try:
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        return memory_mb
    except:
        return 0

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
    """Multi-task processing with memory management"""

    # ACQUIRE SEMAPHORE FOR WHOLE DONATION
    processing_semaphore.acquire()

    try:
        print(f"Background processing started: {donation_id}")
        memory_start = check_memory_usage()
        print(f"Memory at start: {memory_start:.1f} MB")

        if donation_id not in pending_submissions:
            print(f"ERROR: No submissions for {donation_id}")
            return

        tasks = pending_submissions[donation_id]

        # PROCESS TASKS SEQUENTIALLY - Not parallel
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

                # PROCESS IMMEDIATELY WITHOUT NEW THREAD
                from utils.feature_extraction import extract_all_features
                features_result = extract_all_features(
                    task_data['audio_data'],
                    task_data['filename'],
                    task_data['request_info']
                )

                if features_result.get('summary', {}).get('processing_successful', False):
                    from utils.database import save_voice_donation_features
                    save_voice_donation_features(
                        recording_id=task_data['recording_id'],
                        audio_features=features_result,
                        questionnaire_data=task_data['questionnaire_result']['data'],
                        metadata=features_result['metadata']
                    )

                print(f"Completed task {task_num}")

                # CLEANUP BETWEEN TASKS
                import gc
                gc.collect()

            except Exception as e:
                print(f"Task {task_num} error: {e}")

        del pending_submissions[donation_id]
        print(f"Completed all tasks for donation: {donation_id}")

    except Exception as e:
        print(f"Background processing error: {e}")

    finally:
        # ALWAYS RELEASE
        processing_semaphore.release()

        import gc
        gc.collect()

        memory_end = check_memory_usage()
        print(f"Memory at end: {memory_end:.1f} MB")


def process_audio_background(recording_id, audio_data, filename, questionnaire_result, request_info):
    """Background audio processing with memory limits"""

    # ACQUIRE SEMAPHORE - Wait if too many processing
    processing_semaphore.acquire()

    try:
        print(f"Starting audio processing for {recording_id}")
        memory_before = check_memory_usage()
        print(f"Memory before processing: {memory_before:.1f} MB")

        # MEMORY CHECK - Don't start if already high
        if memory_before > 700:  # 700MB threshold
            print(f"Memory too high ({memory_before:.1f}MB), delaying processing")
            import time
            time.sleep(5)  # Wait 5 seconds

        from utils.feature_extraction import extract_all_features
        features_result = extract_all_features(audio_data, filename, request_info)

        memory_after = check_memory_usage()
        print(f"Memory after processing: {memory_after:.1f} MB")

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

        # UPDATE DATABASE WITH ERROR
        try:
            from utils.database import update_voice_donation_status
            update_voice_donation_status(recording_id, 'failed', str(e))
        except:
            pass

    finally:
        # ALWAYS RELEASE SEMAPHORE
        processing_semaphore.release()

        # FORCE CLEANUP
        import gc
        gc.collect()

        memory_final = check_memory_usage()
        print(f"Final memory after cleanup: {memory_final:.1f} MB")


# Dashboard
@app.route('/dashboard')
def dashboard():
    """Serve the dashboard HTML"""
    return send_from_directory('static', 'dashboard.html')


@app.route('/api/dashboard-data')
def get_dashboard_data():
    """Simple dashboard data without pandas dependency"""
    try:
        import boto3
        from decimal import Decimal

        # Direct DynamoDB query without validation script
        dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        table = dynamodb.Table('voice-donations')

        # Get all items
        response = table.scan()
        items = response['Items']

        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])

        # Convert Decimal to float
        def convert_decimal(obj):
            if isinstance(obj, dict):
                return {k: convert_decimal(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimal(i) for i in obj]
            elif isinstance(obj, Decimal):
                return float(obj)
            return obj

        items = [convert_decimal(item) for item in items]

        # Simple counting
        total_recordings = len(items)
        completed_recordings = len([item for item in items if item.get('status') == 'completed'])

        # Count unique donations
        donations = {}
        for item in items:
            donation_id = item.get('donation_id', item['recording_id'])
            if donation_id not in donations:
                donations[donation_id] = {'recordings': [], 'completed': 0}
            donations[donation_id]['recordings'].append(item)
            if item.get('status') == 'completed':
                donations[donation_id]['completed'] += 1

        total_donations = len(donations)
        completed_donations = len([d for d in donations.values() if d['completed'] >= 3])

        # Calculate success rate
        success_rate = (completed_donations / total_donations * 100) if total_donations > 0 else 0

        # Count demographics from unique donations only
        english_count = 0
        arabic_count = 0
        healthy_count = 0
        conditions_count = 0
        age_groups = {}

        seen_donations = set()
        for item in items:
            donation_id = item.get('donation_id', item['recording_id'])
            if donation_id in seen_donations:
                continue
            seen_donations.add(donation_id)

            questionnaire = item.get('questionnaire', {})
            responses = questionnaire.get('responses', {})
            flags = questionnaire.get('analysis_flags', {})

            # Language
            lang = responses.get('donation_language', 'unknown')
            if lang == 'english':
                english_count += 1
            elif lang == 'arabic':
                arabic_count += 1

            # Health
            has_condition = flags.get('has_any_condition', False)
            if has_condition:
                conditions_count += 1
            else:
                healthy_count += 1

            # Age
            age = responses.get('age_group', 'unknown')
            age_groups[age] = age_groups.get(age, 0) + 1

        # Average features
        feature_counts = []
        for item in items:
            if item.get('status') == 'completed' and 'audio_features' in item:
                features = item['audio_features'].get('audio_features', {})
                if features:
                    feature_counts.append(len(features))

        avg_features = sum(feature_counts) / len(feature_counts) if feature_counts else 0

        return jsonify({
            'overview': {
                'total_recordings': total_recordings,
                'total_donations': total_donations,
                'completed_recordings': completed_recordings,
                'donation_success_rate': round(success_rate, 1),
                'recording_success_rate': round(
                    (completed_recordings / total_recordings * 100) if total_recordings > 0 else 0, 1),
            },
            'quality': {
                'avg_features_extracted': round(avg_features, 1),
                'avg_duration_seconds': 0,
                'excellent_quality_count': 0,
                'excellent_quality_rate': 0
            },
            'tasks': {
                'maximum_phonation_time': 0,
                'picture_description': 0,
                'weekend_question': 0,
                'unknown': 0
            },
            'demographics': {
                'english_count': english_count,
                'arabic_count': arabic_count,
                'healthy_count': healthy_count,
                'conditions_count': conditions_count,
                'age_groups': age_groups
            },
            'system_health_score': round(success_rate, 1),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"Dashboard data error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to load dashboard data: {str(e)}'}), 500


@app.route('/api/donation-data')
def get_donation_data():
    """Simple donation data endpoint without pandas dependency"""
    try:
        import boto3
        from decimal import Decimal

        # Direct DynamoDB query
        dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        table = dynamodb.Table('voice-donations')

        # Get all items
        response = table.scan()
        items = response['Items']

        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])

        # Convert Decimal to float
        def convert_decimal(obj):
            if isinstance(obj, dict):
                return {k: convert_decimal(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimal(i) for i in obj]
            elif isinstance(obj, Decimal):
                return float(obj)
            return obj

        items = [convert_decimal(item) for item in items]

        # Process items into donation records
        donations = {}
        for item in items:
            donation_id = item.get('donation_id', item['recording_id'])

            if donation_id not in donations:
                questionnaire = item.get('questionnaire', {})
                responses = questionnaire.get('responses', {})
                flags = questionnaire.get('analysis_flags', {})

                donations[donation_id] = {
                    'donation_id': donation_id,
                    'language': responses.get('donation_language', 'unknown'),
                    'age': responses.get('age_group', 'unknown'),
                    'health': 'Healthy' if not flags.get('has_any_condition', True) else 'Has Conditions',
                    'tasks': {}
                }

            # Add task data with features
            task_metadata = item.get('task_metadata', {})
            task_number = task_metadata.get('task_number', 1)
            task_type = task_metadata.get('task_type', 'unknown')

            # Convert float task numbers to integers for consistency
            if isinstance(task_number, float):
                task_number = int(task_number)

            status = 'completed' if item.get('status') == 'completed' else 'missing'
            features = {}

            if status == 'completed' and 'audio_features' in item:
                audio_features_data = item['audio_features']
                if isinstance(audio_features_data, dict) and 'audio_features' in audio_features_data:
                    features = audio_features_data['audio_features']
                    print(f"Task {task_number} for {donation_id}: found {len(features)} features")

            donations[donation_id]['tasks'][task_number] = {
                'type': task_type,
                'status': status,
                'features': features
            }

        # Convert to list
        donation_list = list(donations.values())
        print(f"Returning {len(donation_list)} donations")

        return jsonify(donation_list)

    except Exception as e:
        print(f"Donation data error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to load donation data: {str(e)}'}), 500

@app.route('/api/test-validation')
def test_validation():
    try:
        from tools.validate_voice_data import VoiceDataValidatorV3
        validator = VoiceDataValidatorV3()
        return jsonify({'success': True, 'message': 'Validation import works'})
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

print("All routes configured")

if __name__ == '__main__':
    # Force port 5000 to match Railway networking config
    port = 5000
    host = '0.0.0.0'

    print(f"Starting server on {host}:{port}")
    app.run(debug=False, host=host, port=port, threaded=True)