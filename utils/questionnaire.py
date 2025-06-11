# questionnaire.py - Questionnaire structure and validation
from datetime import datetime

QUESTIONNAIRE_SCHEMA = {
    "donation_language": {
        "type": "single_choice",
        "required": True,
        "options": ["english", "arabic"],
        "question": "What language will you be speaking in your voice recording?",
        "option_labels": {
            "english": "English",
            "arabic": "Arabic"
        }
    },

    "age_group": {
        "type": "single_choice",
        "required": True,
        "options": ["18-25", "26-35", "36-45", "46-55", "56-65", "66-75", "76+"],
        "question": "What is your age group?"
    },

    "chronic_conditions": {
        "type": "multiple_choice",  # Changed from single_choice to multiple_choice
        "required": True,
        "options": ["respiratory", "neurological", "cardiovascular", "other", "none"],
        # Updated neurologic to neurological
        "question": "Do you have any diagnosed chronic conditions?",
        "option_labels": {
            "respiratory": "Respiratory condition (asthma, COPD, etc.)",
            "neurological": "Neurological condition (Parkinson's, MS, etc.)",  # Updated label
            "cardiovascular": "Cardiovascular condition (heart disease, etc.)",
            "other": "Other chronic condition",
            "none": "None"
        },
        "exclusive_options": ["none"]  # "none" cannot be selected with other options
    },

    "other_condition": {  # Updated field name to match frontend
        "type": "text",
        "required": False,
        "depends_on": {"chronic_conditions": "other"},
        "question": "Please specify your chronic condition:",
        "max_length": 200
    },

    "respiratory_severity": {
        "type": "single_choice",
        "required": False,
        "depends_on": {"chronic_conditions": "respiratory"},
        "options": ["mild", "medium", "severe"],  # Updated "moderate" to "medium" to match frontend
        "question": "Please select the severity of your respiratory condition:",
        "option_labels": {
            "mild": "Mild",
            "medium": "Medium",  # Updated to match frontend
            "severe": "Severe"
        }
    },

    "voice_problems": {
        "type": "single_choice",
        "required": True,
        "options": ["vocal_nodules", "vocal_polyps", "vocal_paralysis", "chronic_laryngitis", "other", "none"],
        "question": "Are you facing any diagnosed voice problems?",
        "option_labels": {
            "vocal_nodules": "Vocal nodules",
            "vocal_polyps": "Vocal polyps",
            "vocal_paralysis": "Vocal cord paralysis",
            "chronic_laryngitis": "Chronic laryngitis",
            "other": "Other voice problem",
            "none": "None"
        }
    },

    "other_voice_problem": {  # Updated field name to match frontend
        "type": "text",
        "required": False,
        "depends_on": {"voice_problems": "other"},
        "question": "Please specify your voice problem:",
        "max_length": 200
    }
}


def validate_questionnaire_data(data):
    """Validate questionnaire responses against schema"""
    errors = []
    warnings = []

    # Check required fields
    for field_name, field_config in QUESTIONNAIRE_SCHEMA.items():
        if field_config["required"]:
            if field_name not in data or not data[field_name]:
                errors.append(f"Required field '{field_name}' is missing")

            # Special handling for multiple choice fields
            elif field_config["type"] == "multiple_choice":
                if not isinstance(data[field_name], list) or len(data[field_name]) == 0:
                    errors.append(f"Required field '{field_name}' must have at least one selection")

        # Check conditional requirements
        if "depends_on" in field_config:
            dependency_field, dependency_value = list(field_config["depends_on"].items())[0]

            # Handle multiple choice dependencies
            if dependency_field in data:
                dependency_met = False
                if isinstance(data[dependency_field], list):
                    dependency_met = dependency_value in data[dependency_field]
                else:
                    dependency_met = data[dependency_field] == dependency_value

                if dependency_met:
                    if field_config.get("required") and (field_name not in data or not data[field_name]):
                        errors.append(
                            f"Field '{field_name}' is required when {dependency_field} includes '{dependency_value}'")

    # Validate field values
    for field_name, value in data.items():
        if field_name in QUESTIONNAIRE_SCHEMA:
            field_config = QUESTIONNAIRE_SCHEMA[field_name]

            # Validate single choice options
            if field_config["type"] == "single_choice":
                if value and value not in field_config["options"]:
                    errors.append(f"Invalid option '{value}' for field '{field_name}'")

            # Validate multiple choice options
            elif field_config["type"] == "multiple_choice":
                if isinstance(value, list):
                    # Check for exclusive options (like "none")
                    if "exclusive_options" in field_config:
                        exclusive_selected = [opt for opt in value if opt in field_config["exclusive_options"]]
                        if exclusive_selected and len(value) > 1:
                            errors.append(
                                f"Exclusive option(s) {exclusive_selected} cannot be selected with other options for '{field_name}'")

                    # Validate each selected option
                    for option in value:
                        if option not in field_config["options"]:
                            errors.append(f"Invalid option '{option}' for field '{field_name}'")
                else:
                    errors.append(f"Field '{field_name}' must be a list")

            # Validate text length
            elif field_config["type"] == "text":
                if value and "max_length" in field_config and len(str(value)) > field_config["max_length"]:
                    errors.append(f"Field '{field_name}' exceeds maximum length of {field_config['max_length']}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def process_questionnaire_data(raw_data):
    """Process and clean questionnaire data"""

    # Clean data - remove None values and handle special cases
    cleaned_data = {}
    for key, value in raw_data.items():
        if value is not None:
            cleaned_data[key] = value

    # Validate data
    validation = validate_questionnaire_data(cleaned_data)

    if not validation["valid"]:
        return {
            "success": False,
            "errors": validation["errors"],
            "warnings": validation["warnings"]
        }

    # Process and structure the data
    processed_data = {
        "responses": cleaned_data,
        "processed_at": datetime.now().isoformat(),
        "data_version": "2.1"  # Updated version for language selection support
    }

    # Add derived fields for analysis
    chronic_conditions = cleaned_data.get("chronic_conditions", [])
    if isinstance(chronic_conditions, str):
        chronic_conditions = [chronic_conditions]  # Handle legacy single value

    processed_data["analysis_flags"] = {
        "donation_language": cleaned_data.get("donation_language", "unknown"),
        "is_english_donation": cleaned_data.get("donation_language") == "english",
        "is_arabic_donation": cleaned_data.get("donation_language") == "arabic",
        "has_chronic_condition": "none" not in chronic_conditions and len(chronic_conditions) > 0,
        "has_respiratory_condition": "respiratory" in chronic_conditions,
        "has_neurological_condition": "neurological" in chronic_conditions,
        "has_cardiovascular_condition": "cardiovascular" in chronic_conditions,
        "has_multiple_conditions": len([c for c in chronic_conditions if c != "none"]) > 1,
        "has_voice_problems": cleaned_data.get("voice_problems") != "none",
        "requires_follow_up": "other" in chronic_conditions or cleaned_data.get("voice_problems") == "other"
    }

    return {
        "success": True,
        "data": processed_data,
        "warnings": validation["warnings"]
    }


def get_questionnaire_schema():
    """Return the questionnaire schema for frontend"""
    return QUESTIONNAIRE_SCHEMA