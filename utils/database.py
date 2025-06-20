#database.py
import boto3
import os
import json
from datetime import datetime
from botocore.exceptions import ClientError
from .dynamodb_helper import prepare_for_dynamodb


def get_dynamodb_resource():
    """Create and return DynamoDB resource"""
    return boto3.resource(
        'dynamodb',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )


def create_tables():
    """Create DynamoDB tables for voice donation data"""
    dynamodb = get_dynamodb_resource()

    # Table for complete voice donations (features + questionnaire)
    table_name = 'voice-donations'

    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'recording_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'recording_id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand pricing (perfect for startup)
        )

        # Wait for table to be created
        table.wait_until_exists()
        return {'success': True, 'message': f'Table {table_name} created successfully'}

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            return {'success': True, 'message': f'Table {table_name} already exists'}
        else:
            return {'success': False, 'error': str(e)}


def save_initial_voice_donation(recording_id, questionnaire_data, audio_filename, audio_size, request_info):
    """Save initial voice donation record with multi-task support"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table('voice-donations')

    # Extract task metadata
    task_metadata = questionnaire_data.get('task_metadata', {})
    donation_id = task_metadata.get('donation_id', recording_id)  # Fallback to recording_id

    # Prepare the initial record
    record = {
        'recording_id': recording_id,
        'donation_id': donation_id,  # NEW: User-facing donation ID
        'created_at': datetime.utcnow().isoformat(),
        'status': 'processing',
        'questionnaire': questionnaire_data,
        'audio_info': {
            'filename': audio_filename,
            'size_bytes': audio_size
        },
        'request_info': request_info,
        'processing_started_at': datetime.utcnow().isoformat()
    }

    # NEW: Add task metadata if present
    if task_metadata:
        record['task_metadata'] = task_metadata
        record['task_number'] = task_metadata.get('task_number', 1)
        record['task_type'] = task_metadata.get('task_type', 'unknown')
        record['total_tasks_in_donation'] = task_metadata.get('total_tasks', 1)

    try:
        # Convert floats to Decimals for DynamoDB compatibility
        dynamodb_record = prepare_for_dynamodb(record)
        table.put_item(Item=dynamodb_record)

        return {
            'success': True,
            'message': 'Initial voice donation record saved successfully',
            'donation_id': donation_id
        }
    except ClientError as e:
        return {'success': False, 'error': str(e)}


def save_voice_donation_features(recording_id, audio_features, questionnaire_data, metadata):
    """Update voice donation record with extracted features and mark as completed"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table('voice-donations')

    try:
        # Prepare update data
        update_data = {
            'status': 'completed',
            'audio_features': audio_features,
            'metadata': metadata,
            'completed_at': datetime.utcnow().isoformat(),
            'features_extracted': audio_features.get('summary', {}).get('total_features_extracted', 0)
        }

        # Convert floats to Decimals for DynamoDB compatibility
        dynamodb_update_data = prepare_for_dynamodb(update_data)

        # Build update expression
        update_expression = "SET #status = :status, audio_features = :audio_features, metadata = :metadata, completed_at = :completed_at, features_extracted = :features_extracted"
        expression_attribute_names = {
            '#status': 'status'  # 'status' is a reserved word in DynamoDB
        }
        expression_attribute_values = {
            ':status': dynamodb_update_data['status'],
            ':audio_features': dynamodb_update_data['audio_features'],
            ':metadata': dynamodb_update_data['metadata'],
            ':completed_at': dynamodb_update_data['completed_at'],
            ':features_extracted': dynamodb_update_data['features_extracted']
        }

        # Update the record
        table.update_item(
            Key={'recording_id': recording_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )

        return {'success': True, 'message': 'Voice donation features saved successfully'}
    except ClientError as e:
        return {'success': False, 'error': str(e)}


def update_voice_donation_status(recording_id, status, error=None):
    """Update voice donation status (for failed processing)"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table('voice-donations')

    try:
        update_data = {
            'status': status,
            'updated_at': datetime.utcnow().isoformat()
        }

        if error:
            update_data['error_message'] = str(error)

        # Convert floats to Decimals for DynamoDB compatibility
        dynamodb_update_data = prepare_for_dynamodb(update_data)

        # Build update expression
        update_expression = "SET #status = :status, updated_at = :updated_at"
        expression_attribute_names = {
            '#status': 'status'
        }
        expression_attribute_values = {
            ':status': dynamodb_update_data['status'],
            ':updated_at': dynamodb_update_data['updated_at']
        }

        if error:
            update_expression += ", error_message = :error_message"
            expression_attribute_values[':error_message'] = dynamodb_update_data['error_message']

        # Update the record
        table.update_item(
            Key={'recording_id': recording_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )

        return {'success': True, 'message': f'Status updated to {status}'}
    except ClientError as e:
        return {'success': False, 'error': str(e)}


def get_voice_donation_status(recording_id):
    """Get the current status of a voice donation"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table('voice-donations')

    try:
        response = table.get_item(Key={'recording_id': recording_id})
        if 'Item' in response:
            item = response['Item']
            return {
                'success': True,
                'data': {
                    'status': item.get('status', 'unknown'),
                    'created_at': item.get('created_at'),
                    'completed_at': item.get('completed_at'),
                    'error_message': item.get('error_message'),
                    'features_extracted': item.get('features_extracted', 0)
                }
            }
        else:
            return {'success': False, 'error': 'Recording not found'}
    except ClientError as e:
        return {'success': False, 'error': str(e)}


def save_voice_donation(recording_id, audio_features, questionnaire_data, metadata):
    """Save complete voice donation record to DynamoDB (LEGACY - for backward compatibility)"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table('voice-donations')

    # Prepare the complete record
    record = {
        'recording_id': recording_id,
        'created_at': datetime.utcnow().isoformat(),
        'audio_features': audio_features,
        'questionnaire': questionnaire_data,
        'metadata': metadata,
        'status': 'completed'
    }

    try:
        # Convert floats to Decimals for DynamoDB compatibility
        dynamodb_record = prepare_for_dynamodb(record)

        table.put_item(Item=dynamodb_record)
        return {'success': True, 'message': 'Voice donation saved successfully'}
    except ClientError as e:
        return {'success': False, 'error': str(e)}


def get_voice_donation(recording_id):
    """Retrieve a voice donation record by ID"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table('voice-donations')

    try:
        response = table.get_item(Key={'recording_id': recording_id})
        if 'Item' in response:
            return {'success': True, 'data': response['Item']}
        else:
            return {'success': False, 'error': 'Record not found'}
    except ClientError as e:
        return {'success': False, 'error': str(e)}


def test_database_connection():
    """Test DynamoDB connection and table access"""
    try:
        dynamodb = get_dynamodb_resource()

        # List tables to test connection
        client = boto3.client(
            'dynamodb',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )

        tables = client.list_tables()

        return {
            'success': True,
            'message': 'DynamoDB connection successful',
            'tables': tables['TableNames']
        }

    except ClientError as e:
        return {'success': False, 'error': str(e)}


def get_donation_recordings_status(donation_id):
    """Get status of all recordings in a donation"""
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table('voice-donations')

    try:
        # Query all recordings for this donation
        response = table.scan(
            FilterExpression='donation_id = :donation_id',
            ExpressionAttributeValues={':donation_id': donation_id}
        )

        recordings = response.get('Items', [])

        if not recordings:
            return {'success': False, 'error': 'Donation not found'}

        # Analyze donation status
        statuses = [r.get('status', 'unknown') for r in recordings]
        completed_count = statuses.count('completed')
        failed_count = statuses.count('failed')

        # Determine overall donation status
        if failed_count > 0:
            donation_status = 'failed'
        elif completed_count == len(recordings):
            donation_status = 'completed'
        else:
            donation_status = 'processing'

        return {
            'success': True,
            'recordings': recordings,
            'donation_status': donation_status,
            'completed_count': completed_count,
            'total_count': len(recordings)
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}