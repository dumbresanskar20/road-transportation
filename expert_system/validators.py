"""
Validators for Transportation Expert System.
Handles validation for user input facts and rule definitions.
"""

from typing import Dict, Any, Tuple

VALID_FACT_OPTIONS = {
    'traffic': ['Low', 'Moderate', 'Heavy'],
    'weather': ['Clear', 'Rainy', 'Foggy'],
    'road_condition': ['Good', 'Damaged', 'Slippery'],
    'road_status': ['Open', 'Closed', 'Under Construction'],
    'vehicle_condition': ['Normal', 'Breakdown'],
    'fuel': ['Sufficient', 'Low'],
    'accident_reported': ['Yes', 'No'],
    'emergency_reported': ['Yes', 'No']
}

FIELD_LABELS = {
    'traffic': 'Traffic Condition',
    'weather': 'Weather Condition',
    'road_condition': 'Road Condition',
    'road_status': 'Road Status',
    'vehicle_condition': 'Vehicle Condition',
    'fuel': 'Fuel Level',
    'accident_reported': 'Accident Reported',
    'emergency_reported': 'Emergency Reported'
}

VALID_PRIORITIES = ['High', 'Medium', 'Low']
VALID_OPERATORS = ['AND', 'OR']

def validate_input_facts(raw_data: Dict[str, Any]) -> Tuple[bool, Dict[str, str], Dict[str, str]]:
    """
    Validates user submitted facts for transportation assessment.
    
    Returns:
        is_valid: Boolean indicating if all fields are valid.
        sanitized_facts: Cleaned dictionary of valid facts.
        errors: Dictionary mapping field name to error message.
    """
    sanitized = {}
    errors = {}

    if not isinstance(raw_data, dict):
        return False, {}, {"general": "Invalid data format. Expected key-value dictionary."}

    for field, valid_options in VALID_FACT_OPTIONS.items():
        val = raw_data.get(field)
        
        if val is None or str(val).strip() == "":
            errors[field] = f"{FIELD_LABELS.get(field, field)} is required. Please select a valid option."
            continue
            
        str_val = str(val).strip()
        
        # Case-insensitive matching to canonical title case
        matched = None
        for option in valid_options:
            if str_val.lower() == option.lower():
                matched = option
                break
                
        if matched is None:
            allowed_str = ", ".join(valid_options)
            errors[field] = f"Invalid value '{str_val}' for {FIELD_LABELS.get(field, field)}. Allowed values: {allowed_str}."
        else:
            sanitized[field] = matched

    is_valid = len(errors) == 0
    return is_valid, sanitized, errors


def validate_rule_schema(rule: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validates the structure and attributes of an expert system rule.
    
    Returns:
        is_valid: Boolean
        error_msg: Description of failure if invalid, empty string otherwise.
    """
    if not isinstance(rule, dict):
        return False, "Rule must be a dictionary object."

    required_keys = [
        'id', 'name', 'category', 'description', 
        'conditions', 'operator', 'recommendation', 
        'explanation', 'priority', 'enabled'
    ]

    for key in required_keys:
        if key not in rule:
            return False, f"Rule is missing required field: '{key}'."

    if not isinstance(rule['id'], str) or not rule['id'].strip():
        return False, "Rule 'id' must be a non-empty string."

    if not isinstance(rule['name'], str) or not rule['name'].strip():
        return False, "Rule 'name' must be a non-empty string."

    if not isinstance(rule['category'], str) or not rule['category'].strip():
        return False, "Rule 'category' must be a non-empty string."

    if not isinstance(rule['conditions'], dict) or len(rule['conditions']) == 0:
        return False, "Rule 'conditions' must be a non-empty dictionary."

    operator = str(rule['operator']).upper()
    if operator not in VALID_OPERATORS:
        return False, f"Rule 'operator' must be one of {VALID_OPERATORS}, got '{rule['operator']}'."

    priority = str(rule['priority']).capitalize()
    if priority not in VALID_PRIORITIES:
        return False, f"Rule 'priority' must be one of {VALID_PRIORITIES}, got '{rule['priority']}'."

    if not isinstance(rule['enabled'], bool):
        return False, "Rule 'enabled' must be a boolean (True/False)."

    if not isinstance(rule['recommendation'], str) or not rule['recommendation'].strip():
        return False, "Rule 'recommendation' must be a non-empty string."

    if not isinstance(rule['explanation'], str) or not rule['explanation'].strip():
        return False, "Rule 'explanation' must be a non-empty string."

    # Validate condition fields against recognized domain attributes
    for cond_key, cond_val in rule['conditions'].items():
        if cond_key not in VALID_FACT_OPTIONS:
            return False, f"Condition key '{cond_key}' is not a recognized fact attribute."
            
        valid_opts = VALID_FACT_OPTIONS[cond_key]
        if isinstance(cond_val, list):
            for v in cond_val:
                if v not in valid_opts:
                    return False, f"Invalid value '{v}' for condition '{cond_key}'."
        elif isinstance(cond_val, str):
            if cond_val not in valid_opts:
                return False, f"Invalid value '{cond_val}' for condition '{cond_key}'."
        else:
            return False, f"Condition value for '{cond_key}' must be a string or list of strings."

    return True, ""
