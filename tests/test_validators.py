"""
Unit Tests for Input Facts Validation and Rule Schema Validation.
"""

import pytest
from expert_system.validators import validate_input_facts, validate_rule_schema

def test_valid_input_facts():
    """Valid facts should pass validation and be normalized."""
    valid_data = {
        'traffic': 'Heavy',
        'weather': 'Rainy',
        'road_condition': 'Slippery',
        'road_status': 'Open',
        'vehicle_condition': 'Normal',
        'fuel': 'Sufficient',
        'accident_reported': 'No',
        'emergency_reported': 'No'
    }
    is_valid, sanitized, errors = validate_input_facts(valid_data)
    assert is_valid is True
    assert len(errors) == 0
    assert sanitized['traffic'] == 'Heavy'
    assert sanitized['weather'] == 'Rainy'

def test_missing_input_facts():
    """Case 11: Missing user inputs must be rejected with helpful error messages."""
    incomplete_data = {
        'traffic': 'Heavy',
        # weather missing
        'road_condition': 'Good',
        'road_status': 'Open',
        'vehicle_condition': 'Normal',
        'fuel': '', # empty
        'accident_reported': 'No',
        'emergency_reported': 'No'
    }
    is_valid, sanitized, errors = validate_input_facts(incomplete_data)
    assert is_valid is False
    assert 'weather' in errors
    assert 'fuel' in errors

def test_invalid_input_fact_values():
    """Unrecognized input options must be rejected."""
    bad_data = {
        'traffic': 'SuperHeavySpeedy',
        'weather': 'Tornado',
        'road_condition': 'Good',
        'road_status': 'Open',
        'vehicle_condition': 'Normal',
        'fuel': 'Sufficient',
        'accident_reported': 'Maybe',
        'emergency_reported': 'No'
    }
    is_valid, sanitized, errors = validate_input_facts(bad_data)
    assert is_valid is False
    assert 'traffic' in errors
    assert 'weather' in errors
    assert 'accident_reported' in errors

def test_case_insensitive_fact_normalization():
    """Fact validation should accept lowercase inputs and convert to canonical titlecase."""
    data = {
        'traffic': 'heavy',
        'weather': 'rainy',
        'road_condition': 'slippery',
        'road_status': 'closed',
        'vehicle_condition': 'breakdown',
        'fuel': 'low',
        'accident_reported': 'yes',
        'emergency_reported': 'yes'
    }
    is_valid, sanitized, errors = validate_input_facts(data)
    assert is_valid is True
    assert sanitized['traffic'] == 'Heavy'
    assert sanitized['road_status'] == 'Closed'

def test_rule_schema_valid():
    """Valid rule dictionary passes schema validation."""
    rule = {
        "id": "R100",
        "name": "Test Rule",
        "category": "Road Safety",
        "description": "Test description",
        "conditions": {"weather": "Rainy"},
        "operator": "AND",
        "recommendation": "Drive carefully in the rain.",
        "explanation": "Rain reduces traction.",
        "priority": "Medium",
        "enabled": True
    }
    is_valid, err = validate_rule_schema(rule)
    assert is_valid is True
    assert err == ""

def test_rule_schema_invalid():
    """Case 10: Invalid rule structures are handled safely and rejected."""
    # Missing required 'recommendation'
    bad_rule_1 = {
        "id": "R101",
        "name": "Test Rule",
        "category": "Road Safety",
        "description": "Test",
        "conditions": {"weather": "Rainy"},
        "operator": "AND",
        "priority": "Medium",
        "enabled": True
    }
    is_valid, err = validate_rule_schema(bad_rule_1)
    assert is_valid is False
    assert "recommendation" in err

    # Invalid operator
    bad_rule_2 = {
        "id": "R102",
        "name": "Test Rule",
        "category": "Road Safety",
        "description": "Test",
        "conditions": {"weather": "Rainy"},
        "operator": "XOR", # invalid
        "recommendation": "Test",
        "explanation": "Test",
        "priority": "Medium",
        "enabled": True
    }
    is_valid, err = validate_rule_schema(bad_rule_2)
    assert is_valid is False
    assert "operator" in err
