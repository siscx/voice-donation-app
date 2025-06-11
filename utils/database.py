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


def save_voice_donation(recording_id, audio_features, questionnaire_data, metadata):
    """Save complete voice donation record to DynamoDB"""
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