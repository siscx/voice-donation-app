# questionnaire.py - Updated schema for enhanced medical conditions
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

    "native_language": {
        "type": "single_choice",
        "required": False,
        "depends_on": {"donation_language": "english"},
        "options": ["english", "spanish", "french", "arabic", "hindi", "chinese", "other"],
        "question": "What is your native language?"
    },

    "arabic_dialect": {
        "type": "single_choice",
        "required": False,
        "depends_on": {"donation_language": "arabic"},
        "options": ["egyptian", "levantine", "gulf", "maghrebi", "iraqi", "sudanese", "yemeni", "hejazi", "najdi", "msa"],
        "question": "Which Arabic dialect do you speak?"
    },

    "age_group": {
        "type": "single_choice",
        "required": True,
        "options": ["18-25", "26-35", "36-45", "46-55", "56-65", "66-75", "76+"],
        "question": "What is your age group?"
    },

    # ENHANCED: New health conditions structure
    "health_conditions": {
        "type": "multiple_choice",
        "required": True,
        "options": [
            # None option
            "none",

            # Neurological conditions
            "alzheimers", "dementia", "mci", "als", "huntingtons", "parkinsons",

            # Respiratory conditions
            "asthma", "chronic_cough", "copd", "respiratory_other",

            # Mood/Psychiatric conditions
            "depression", "anxiety", "substance_use", "bipolar", "autism", "adhd", "mood_other",

            # Metabolic/Endocrine conditions
            "diabetes_type1", "diabetes_type2", "prediabetes", "thyroid", "obesity",

            # Voice problems
            "vocal_fold_paralysis", "muscle_tension_dysphonia", "spasmodic_dysphonia",
            "vocal_lesions", "laryngitis", "laryngeal_cancer", "voice_other",

            # General other
            "other_general"
        ],
        "question": "Do you have any diagnosed health conditions?",
        "option_labels": {
            "none": "None - I have no diagnosed health conditions",
            "alzheimers": "Alzheimer's",
            "dementia": "Dementia",
            "mci": "Mild Cognitive Impairment",
            "als": "ALS",
            "huntingtons": "Huntington's disease",
            "parkinsons": "Parkinson's disease",
            "asthma": "Asthma",
            "chronic_cough": "Chronic cough",
            "copd": "COPD",
            "respiratory_other": "Other respiratory condition",
            "depression": "Depression disorder",
            "anxiety": "Anxiety disorder",
            "substance_use": "Alcohol or substance use disorder",
            "bipolar": "Bipolar disorder",
            "autism": "Autism spectrum disorder",
            "adhd": "ADHD",
            "mood_other": "Other mood/psychiatric condition",
            "diabetes_type1": "Diabetes type 1",
            "diabetes_type2": "Diabetes type 2",
            "prediabetes": "Prediabetes",
            "thyroid": "Thyroid Disorder",
            "obesity": "Obesity",
            "vocal_fold_paralysis": "Unilateral vocal fold paralysis",
            "muscle_tension_dysphonia": "Muscle Tension Dysphonia",
            "spasmodic_dysphonia": "Spasmodic Dysphonia/laryngeal tremor",
            "vocal_lesions": "Lesions (vocal polyp, nodules etc)",
            "laryngitis": "Laryngitis",
            "laryngeal_cancer": "Laryngeal cancer",
            "voice_other": "Other voice problem",
            "other_general": "Other condition (please specify)"
        },
        "exclusive_options": ["none"]
    },

    # ENHANCED: Severity selections for each condition
    "condition_severities": {
        "type": "object",
        "required": False,
        "question": "Severity levels for selected conditions",
        "valid_severities": ["mild", "medium", "severe", "unknown"],
        "conditions_requiring_severity": [
            "alzheimers", "dementia", "mci", "als", "huntingtons", "parkinsons",
            "asthma", "chronic_cough", "copd",
            "depression", "anxiety", "substance_use", "bipolar", "autism", "adhd",
            "diabetes_type1", "diabetes_type2", "prediabetes", "thyroid", "obesity",
            "vocal_fold_paralysis", "muscle_tension_dysphonia", "spasmodic_dysphonia",
            "vocal_lesions", "laryngitis", "laryngeal_cancer"
        ]
    },

    # ENHANCED: Text specifications for "other" conditions
    "condition_specifications": {
        "type": "object",
        "required": False,
        "question": "Specifications for 'other' conditions",
        "conditions_requiring_specification": [
            "respiratory_other", "mood_other", "voice_other", "other_general"
        ],
        "specification_labels": {
            "respiratory_other": "specify_respiratory_other",
            "mood_other": "specify_mood_other",
            "voice_other": "specify_voice_other",
            "other_general": "otherGeneralCondition"
        }
    }
}


def validate_questionnaire_data(data):
    """Enhanced validation for new questionnaire structure"""
    errors = []
    warnings = []

    # Check required fields
    for field_name, field_config in QUESTIONNAIRE_SCHEMA.items():
        if field_config["required"]:
            if field_name not in data or not data[field_name]:
                errors.append(f"Required field '{field_name}' is missing")

            # Special handling for health_conditions
            elif field_name == "health_conditions":
                if not isinstance(data[field_name], list) or len(data[field_name]) == 0:
                    errors.append(f"Required field '{field_name}' must have at least one selection")

    # Validate health conditions exclusivity
    if "health_conditions" in data:
        health_conditions = data["health_conditions"]
        if isinstance(health_conditions, list):
            if "none" in health_conditions and len(health_conditions) > 1:
                errors.append("'None' cannot be selected with other health conditions")

    # Validate condition severities
    if "health_conditions" in data and "condition_severities" in data:
        health_conditions = data["health_conditions"]
        severities = data["condition_severities"]

        severity_config = QUESTIONNAIRE_SCHEMA["condition_severities"]
        conditions_requiring_severity = severity_config["conditions_requiring_severity"]

        for condition in health_conditions:
            if condition in conditions_requiring_severity:
                if condition not in severities or not severities[condition]:
                    errors.append(f"Severity required for condition '{condition}'")
                elif severities[condition] not in severity_config["valid_severities"]:
                    errors.append(f"Invalid severity '{severities[condition]}' for condition '{condition}'")

    # Validate condition specifications
    if "health_conditions" in data and "condition_specifications" in data:
        health_conditions = data["health_conditions"]
        specifications = data["condition_specifications"]

        spec_config = QUESTIONNAIRE_SCHEMA["condition_specifications"]
        conditions_requiring_spec = spec_config["conditions_requiring_specification"]

        for condition in health_conditions:
            if condition in conditions_requiring_spec:
                spec_field = spec_config["specification_labels"][condition]
                if spec_field not in specifications or not specifications[spec_field]:
                    errors.append(f"Specification required for condition '{condition}'")

    # NEW: Validate conditional language fields
    donation_language = data.get("donation_language")

    if donation_language == "english":
        # Native language should be provided when donation language is English
        if "native_language" not in data or not data["native_language"]:
            warnings.append("Native language recommended when donating in English")

        # Arabic dialect should not be provided
        if data.get("arabic_dialect"):
            errors.append("Arabic dialect should not be selected when donation language is English")

    elif donation_language == "arabic":
        # Arabic dialect should be provided when donation language is Arabic
        if "arabic_dialect" not in data or not data["arabic_dialect"]:
            warnings.append("Arabic dialect recommended when donating in Arabic")

        # Native language should not be provided
        if data.get("native_language"):
            errors.append("Native language should not be selected when donation language is Arabic")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def process_questionnaire_data(raw_data):
    """Enhanced processing for new questionnaire structure"""

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
        "data_version": "3.0"  # Updated for enhanced medical conditions
    }

    # ENHANCED: Add derived analysis flags
    health_conditions = cleaned_data.get("health_conditions", [])
    if isinstance(health_conditions, str):
        health_conditions = [health_conditions]

    processed_data["analysis_flags"] = {
        # Language flags
        "donation_language": cleaned_data.get("donation_language", "unknown"),
        "is_english_donation": cleaned_data.get("donation_language") == "english",
        "is_arabic_donation": cleaned_data.get("donation_language") == "arabic",

        # General health flags
        "has_any_condition": "none" not in health_conditions and len(health_conditions) > 0,
        "has_multiple_conditions": len([c for c in health_conditions if c != "none"]) > 1,

        # Category flags
        "has_neurological_condition": any(c in health_conditions for c in
                                          ["alzheimers", "dementia", "mci", "als", "huntingtons", "parkinsons"]),
        "has_respiratory_condition": any(c in health_conditions for c in
                                         ["asthma", "chronic_cough", "copd", "respiratory_other"]),
        "has_mood_condition": any(c in health_conditions for c in
                                  ["depression", "anxiety", "substance_use", "bipolar", "autism", "adhd",
                                   "mood_other"]),
        "has_metabolic_condition": any(c in health_conditions for c in
                                       ["diabetes_type1", "diabetes_type2", "prediabetes", "thyroid", "obesity"]),
        "has_voice_condition": any(c in health_conditions for c in
                                   ["vocal_fold_paralysis", "muscle_tension_dysphonia", "spasmodic_dysphonia",
                                    "vocal_lesions", "laryngitis", "laryngeal_cancer", "voice_other"]),

        # Specific condition flags (for research)
        "has_dementia_related": any(c in health_conditions for c in ["alzheimers", "dementia", "mci"]),
        "has_movement_disorder": any(c in health_conditions for c in ["parkinsons", "huntingtons"]),
        "has_diabetes": any(c in health_conditions for c in ["diabetes_type1", "diabetes_type2", "prediabetes"]),

        # Data quality flags
        "requires_follow_up": any(c in health_conditions for c in
                                  ["respiratory_other", "mood_other", "voice_other", "other_general"]),
        "has_severity_data": "condition_severities" in cleaned_data and len(
            cleaned_data.get("condition_severities", {})) > 0,
        "has_specification_data": "condition_specifications" in cleaned_data and len(
            cleaned_data.get("condition_specifications", {})) > 0,

        # Language and dialect flags
        "native_language": cleaned_data.get("native_language", "unknown"),
        "arabic_dialect": cleaned_data.get("arabic_dialect", "unknown"),
        "is_native_english_speaker": cleaned_data.get("native_language") == "en",
        "is_multilingual": (
                cleaned_data.get("donation_language") == "english" and
                cleaned_data.get("native_language") not in ["en", "", None]),
        "has_language_accent_data": bool(
            cleaned_data.get("native_language") or cleaned_data.get("arabic_dialect")),

        # Dialect-specific flags for research
        "speaks_egyptian_arabic": cleaned_data.get("arabic_dialect") == "egyptian",
        "speaks_gulf_arabic": cleaned_data.get("arabic_dialect") == "gulf",
        "speaks_levantine_arabic": cleaned_data.get("arabic_dialect") == "levantine",
        "speaks_maghrebi_arabic": cleaned_data.get("arabic_dialect") == "maghrebi",

        # Cross-language analysis flags
        "donation_matches_native": (
                (cleaned_data.get("donation_language") == "english" and cleaned_data.get("native_language") == "en") or
                (cleaned_data.get("donation_language") == "arabic" and cleaned_data.get("native_language") == "ar"))
    }

    return {
        "success": True,
        "data": processed_data,
        "warnings": validation["warnings"]
    }


def get_questionnaire_schema():
    """Return the questionnaire schema for frontend"""
    return QUESTIONNAIRE_SCHEMA