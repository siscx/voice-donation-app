from decimal import Decimal
import json
import numpy as np


def convert_floats_to_decimal(obj):
    """
    Recursively convert all float values to Decimal for DynamoDB compatibility
    Also handles special object types that can't be serialized
    """
    if isinstance(obj, dict):
        return {key: convert_floats_to_decimal(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    elif isinstance(obj, tuple):
        return [convert_floats_to_decimal(item) for item in obj]  # Convert tuples to lists
    elif isinstance(obj, float):
        # Convert float to Decimal, handling special cases
        if str(obj).lower() in ('nan', 'inf', '-inf'):
            return str(obj)  # Store as string for special float values
        return Decimal(str(obj))  # Convert to string first to avoid precision issues
    elif isinstance(obj, np.floating):
        # Handle numpy float types
        if np.isnan(obj) or np.isinf(obj):
            return str(obj)
        return Decimal(str(float(obj)))
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()  # Convert numpy arrays to lists
    elif hasattr(obj, '__dict__') and not isinstance(obj, (str, int, float, bool)):
        # Handle complex objects (like Parselmouth objects) by converting to string
        return str(obj)
    elif obj is None:
        return None
    elif isinstance(obj, (str, int, bool)):
        return obj
    else:
        # For any other unknown type, convert to string as fallback
        try:
            return str(obj)
        except:
            return "Unsupported_Object_Type"


def prepare_for_dynamodb(data):
    """
    Prepare data for DynamoDB storage by converting floats and handling edge cases
    """
    # First convert the data using our converter
    converted_data = convert_floats_to_decimal(data)

    # Additional cleanup for DynamoDB constraints
    def clean_item(item):
        if isinstance(item, dict):
            cleaned = {}
            for key, value in item.items():
                # DynamoDB doesn't allow empty strings or None values in certain contexts
                if value == '' or value is None:
                    continue  # Skip empty values
                cleaned[key] = clean_item(value)
            return cleaned
        elif isinstance(item, list):
            return [clean_item(i) for i in item if i is not None and i != '']
        else:
            return item

    return clean_item(converted_data)


# Test function to verify conversion works
def test_conversion():
    test_data = {
        "float_value": 3.14159,
        "nested": {
            "another_float": 2.71828,
            "int_value": 42,
            "string_value": "hello"
        },
        "float_list": [1.1, 2.2, 3.3],
        "mixed_list": [1, 2.5, "string", {"nested_float": 4.7}]
    }

    converted = convert_floats_to_decimal(test_data)
    print("Original:", test_data)
    print("Converted:", converted)
    return converted


if __name__ == "__main__":
    test_conversion()