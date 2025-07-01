# debug_dynamodb.py - Quick script to see actual DynamoDB structure

import boto3
import json
from decimal import Decimal
from dotenv import load_dotenv
import os

load_dotenv()


def convert_decimal_to_float(obj):
    """Convert DynamoDB Decimal types to float"""
    if isinstance(obj, dict):
        return {key: convert_decimal_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj


def debug_dynamodb_structure():
    """Debug the actual structure of your DynamoDB data"""

    dynamodb = boto3.resource(
        'dynamodb',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    table = dynamodb.Table('voice-donations')

    print("🔍 DEBUGGING DYNAMODB STRUCTURE")
    print("=" * 50)

    # Get first few items
    response = table.scan(Limit=3)
    items = response.get('Items', [])

    for i, item in enumerate(items):
        item = convert_decimal_to_float(item)

        print(f"\n📋 RECORD {i + 1}:")
        print(f"Recording ID: {item.get('recording_id', 'N/A')}")
        print(f"Donation ID: {item.get('donation_id', 'N/A')}")
        print(f"Status: {item.get('status', 'N/A')}")

        # Check task metadata
        task_metadata = item.get('task_metadata', {})
        if task_metadata:
            print(f"Task Number: {task_metadata.get('task_number', 'N/A')}")
            print(f"Task Type: {task_metadata.get('task_type', 'N/A')}")

        # Check audio_features structure
        if 'audio_features' in item:
            audio_features = item['audio_features']
            print(f"\n🎵 AUDIO_FEATURES structure:")
            print(f"Type: {type(audio_features)}")

            if isinstance(audio_features, dict):
                print(f"Top-level keys: {list(audio_features.keys())}")

                # Check nested audio_features
                if 'audio_features' in audio_features:
                    nested_features = audio_features['audio_features']
                    print(f"Nested audio_features type: {type(nested_features)}")
                    if isinstance(nested_features, dict):
                        feature_names = list(nested_features.keys())
                        print(f"Number of features: {len(feature_names)}")
                        print(f"Sample feature names: {feature_names[:10]}")

                        # Show a sample feature value
                        if feature_names:
                            sample_feature = feature_names[0]
                            sample_value = nested_features[sample_feature]
                            print(f"Sample: {sample_feature} = {sample_value}")
                    else:
                        print(f"Nested audio_features content: {nested_features}")

                # Check other possible locations
                for key in ['features', 'extracted_features', 'voice_features']:
                    if key in audio_features:
                        print(f"Found '{key}': {type(audio_features[key])}")
                        if isinstance(audio_features[key], dict):
                            print(f"  Contains {len(audio_features[key])} items")
            else:
                print(f"Audio features content: {audio_features}")
        else:
            print("❌ No 'audio_features' found in this record")

        print("-" * 50)


if __name__ == "__main__":
    debug_dynamodb_structure()