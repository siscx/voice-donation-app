import boto3
import os
import uuid
from datetime import datetime
from botocore.exceptions import ClientError


def get_s3_client():
    """Create and return S3 client"""
    return boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )


def upload_audio_file(file_data, filename):
    """Upload audio file to S3 and return the file URL"""
    try:
        s3_client = get_s3_client()
        bucket_name = os.getenv('S3_BUCKET_NAME')

        # Create unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        s3_filename = f"audio/{timestamp}_{unique_id}_{filename}"

        # Upload file
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_filename,
            Body=file_data,
            ContentType='audio/wav'  # Adjust based on your audio format
        )

        # Return file info
        file_url = f"https://{bucket_name}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{s3_filename}"

        return {
            'success': True,
            'file_url': file_url,
            'filename': s3_filename,
            'message': 'Audio file uploaded successfully'
        }

    except ClientError as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to upload audio file'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Unexpected error uploading file'
        }


def test_s3_connection():
    """Test if we can connect to S3 and access our bucket"""
    try:
        s3_client = get_s3_client()
        bucket_name = os.getenv('S3_BUCKET_NAME')

        # Try to list objects in bucket (this tests both connection and permissions)
        response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)

        return {
            'success': True,
            'message': f'Successfully connected to S3 bucket: {bucket_name}',
            'region': os.getenv('AWS_REGION')
        }
    except ClientError as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to connect to S3'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Unexpected error connecting to S3'
        }