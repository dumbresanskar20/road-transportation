"""
Comprehensive Unit Tests for Rule-Based Inference Engine and Knowledge Base.
Validates forward-chaining deduction, AND/OR logic, conflict resolution,
and safety invariants.
"""

import pytest
from expert_system.rule_engine import RuleEngine
from expert_system.rule_loader import RuleLoader

@pytest.fixture
def engine():
    """Initializes the RuleEngine with the production knowledge base."""
    loader = RuleLoader('knowledge_base/transportation_rules.json')
    return RuleEngine(loader)

@pytest.fixture
def baseline_facts():
    """Default baseline facts where road conditions are normal and clear."""
    return {
        'traffic': 'Low',
        'weather': 'Clear',
        'road_condition': 'Good',
        'road_status': 'Open',
        'vehicle_condition': 'Normal',
        'fuel': 'Sufficient',
        'accident_reported': 'No',
        'emergency_reported': 'No'
    }

def test_1_heavy_traffic_activates_correct_rule(engine, baseline_facts):
    """Case 1: Heavy traffic activates the correct rule (R001)."""
    facts = {**baseline_facts, 'traffic': 'Heavy'}
    result = engine.evaluate(facts)
    assert result['success'] is True
    assert 'R001' in result['activated_rules']
    rec = next(r for r in result['recommendations'] if r['rule_id'] == 'R001')
    assert 'prolonged transit delays' in rec['recommendation'].lower() or 'traffic' in rec['recommendation'].lower()

def test_2_rainy_weather_activates_correct_rule(engine, baseline_facts):
    """Case 2: Rainy weather activates the correct rule (R003)."""
    facts = {**baseline_facts, 'weather': 'Rainy'}
    result = engine.evaluate(facts)
    assert result['success'] is True
    assert 'R003' in result['activated_rules']
    assert any('wipers' in r['recommendation'].lower() or 'rain' in r['recommendation'].lower() for r in result['recommendations'])

def test_3_slippery_road_activates_correct_rule(engine, baseline_facts):
    """Case 3: Slippery roads activate the correct rule (R005)."""
    facts = {**baseline_facts, 'road_condition': 'Slippery'}
    result = engine.evaluate(facts)
    assert result['success'] is True
    assert 'R005' in result['activated_rules']
    rec = next(r for r in result['recommendations'] if r['rule_id'] == 'R005')
    assert 'braking' in rec['recommendation'].lower() or 'traction' in rec['explanation'].lower()

def test_4_closed_road_activates_appropriate_warning(engine, baseline_facts):
    """Case 4: A closed road activates the appropriate warning (R007)."""
    facts = {**baseline_facts, 'road_status': 'Closed'}
    result = engine.evaluate(facts)
    assert result['success'] is True
    assert 'R007' in result['activated_rules']
    assert result['has_closure'] is True
    rec = next(r for r in result['recommendations'] if r['rule_id'] == 'R007')
    assert 'DO NOT ENTER' in rec['recommendation'].upper()
    assert 'detour' in rec['recommendation'].lower()

def test_5_low_fuel_activates_correct_recommendation(engine, baseline_facts):
    """Case 5: Low fuel activates the appropriate recommendation (R010)."""
    facts = {**baseline_facts, 'fuel': 'Low'}
    result = engine.evaluate(facts)
    assert result['success'] is True
    assert 'R010' in result['activated_rules']
    rec = next(r for r in result['recommendations'] if r['rule_id'] == 'R010')
    assert 'fuel' in rec['recommendation'].lower() or 'fueling station' in rec['recommendation'].lower()

def test_6_multiple_applicable_rules_activate_together(engine, baseline_facts):
    """Case 6: Multiple applicable rules activate together."""
    facts = {
        **baseline_facts,
        'traffic': 'Heavy',
        'weather': 'Rainy',
        'road_condition': 'Slippery'
    }
    result = engine.evaluate(facts)
    assert result['success'] is True
    assert len(result['activated_rules']) >= 4
    assert 'R001' in result['activated_rules']
    assert 'R003' in result['activated_rules']
    assert 'R005' in result['activated_rules']
    assert result['highest_priority'] == 'High'

def test_7_rules_with_multiple_and_conditions_evaluated_correctly(engine, baseline_facts):
    """Case 7: Rules with multiple AND conditions are evaluated correctly."""
    # R013 requires BOTH traffic == 'Heavy' AND weather == 'Rainy'
    facts_partial = {**baseline_facts, 'traffic': 'Heavy', 'weather': 'Clear'}
    res_partial = engine.evaluate(facts_partial)
    assert 'R013' not in res_partial['activated_rules']

    facts_full = {**baseline_facts, 'traffic': 'Heavy', 'weather': 'Rainy'}
    res_full = engine.evaluate(facts_full)
    assert 'R013' in res_full['activated_rules']

def test_8_rules_with_or_conditions_evaluated_correctly(engine, baseline_facts):
    """Case 8: Rules with OR conditions are evaluated correctly."""
    # R021 activates if weather in ['Rainy', 'Foggy']
    facts_rain = {**baseline_facts, 'weather': 'Rainy'}
    res_rain = engine.evaluate(facts_rain)
    assert 'R021' in res_rain['activated_rules']

    facts_fog = {**baseline_facts, 'weather': 'Foggy'}
    res_fog = engine.evaluate(facts_fog)
    assert 'R021' in res_fog['activated_rules']

    facts_clear = {**baseline_facts, 'weather': 'Clear'}
    res_clear = engine.evaluate(facts_clear)
    assert 'R021' not in res_clear['activated_rules']

def test_9_disabled_rules_are_not_activated(engine, baseline_facts):
    """Case 9: Disabled rules are not activated."""
    # R025 is an experimental rule with enabled == False
    facts = {**baseline_facts, 'traffic': 'Heavy'}
    result = engine.evaluate(facts)
    assert 'R025' not in result['activated_rules']

def test_12_duplicate_recommendations_handled_correctly(engine, baseline_facts):
    """Case 12: Duplicate recommendations are handled correctly and deduplicated."""
    facts = {**baseline_facts, 'traffic': 'Heavy', 'weather': 'Rainy'}
    result = engine.evaluate(facts)
    rec_texts = [r['recommendation'] for r in result['recommendations']]
    # No duplicate recommendation texts
    assert len(rec_texts) == len(set(rec_texts))

def test_13_rule_explanations_match_activated_rules(engine, baseline_facts):
    """Case 13: Rule explanations match the actual activated rules."""
    facts = {**baseline_facts, 'weather': 'Foggy', 'road_condition': 'Damaged'}
    result = engine.evaluate(facts)
    explanation_rule_ids = [e['rule_id'] for e in result['explanations']]
    assert sorted(explanation_rule_ids) == sorted(result['activated_rules'])
    
    # Check explanation trace details
    fog_trace = next(e for e in result['explanations'] if e['rule_id'] == 'R004')
    assert fog_trace['rule_name'] == 'Dense Fog Low-Visibility Warning'
    assert any('weather' in c['field'] for c in fog_trace['condition_evaluations'])

def test_16_emergency_guidance_shown_when_appropriate(engine, baseline_facts):
    """Case 16: Emergency guidance is shown and references 112."""
    facts = {**baseline_facts, 'emergency_reported': 'Yes'}
    result = engine.evaluate(facts)
    assert result['has_emergency'] is True
    assert 'R012' in result['activated_rules']
    rec = next(r for r in result['recommendations'] if r['rule_id'] == 'R012')
    assert '112' in rec['recommendation']
    assert rec['priority'] == 'High'

def test_17_closed_road_never_recommended_as_available(engine, baseline_facts):
    """Case 17: A closed road is never recommended as an available route."""
    facts = {**baseline_facts, 'road_status': 'Closed'}
    result = engine.evaluate(facts)
    for rec in result['recommendations']:
        rec_text = rec['recommendation'].lower()
        # Verify no recommendation suggests proceeding normally or using the road
        assert 'proceed normally' not in rec_text
        assert 'open' not in rec_text
    # Explicit closure directive must be present
    assert any('do not enter' in r['recommendation'].lower() for r in result['recommendations'])
