"""
Integration Tests for Flask Web Application Routes and Database Layer.
"""

import pytest
from app import create_app
from database.db import init_db, get_dashboard_stats, get_assessment, save_assessment

@pytest.fixture
def test_app(tmp_path):
    """Creates a test Flask application with an isolated temporary SQLite database."""
    test_db = str(tmp_path / "test_transportation.db")
    app = create_app('testing')
    app.config['DATABASE_PATH'] = test_db
    with app.app_context():
        init_db(test_db)
    return app

@pytest.fixture
def client(test_app):
    """Provides test client."""
    return test_app.test_client()

def test_dashboard_route_empty_db(client):
    """Case 15: Dashboard handles empty database statistics gracefully without errors."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Rule Based Expert System For Road Transportation" in response.data

def test_assessment_form_route(client):
    """Assessment form renders all required field controls."""
    response = client.get('/assessment')
    assert response.status_code == 200
    assert b"Traffic Condition" in response.data
    assert b"Weather Condition" in response.data
    assert b"Analyze" in response.data

def test_analyze_valid_submission_and_persistence(client, test_app):
    """Case 14: Valid assessment runs inference, saves to SQLite, and displays results."""
    post_data = {
        'traffic': 'Heavy',
        'weather': 'Rainy',
        'road_condition': 'Slippery',
        'road_status': 'Open',
        'vehicle_condition': 'Normal',
        'fuel': 'Sufficient',
        'accident_reported': 'No',
        'emergency_reported': 'No'
    }
    response = client.post('/analyze', data=post_data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Advisory Assessment Report" in response.data
    assert b"R001" in response.data # Heavy traffic rule
    assert b"R003" in response.data # Rainy weather rule
    assert b"R005" in response.data # Slippery road rule

def test_analyze_invalid_submission_rejection(client):
    """Case 11: Incomplete submissions are rejected with 400 Bad Request and validation errors."""
    invalid_data = {
        'traffic': 'Heavy',
        # weather omitted
        'road_condition': 'Good',
        'road_status': 'Open',
        'vehicle_condition': 'Normal',
        'fuel': 'Sufficient',
        'accident_reported': 'No',
        'emergency_reported': 'No'
    }
    response = client.post('/analyze', data=invalid_data)
    assert response.status_code == 400
    assert b"Weather Condition is required" in response.data

def test_history_and_search_routes(client, test_app):
    """Assessment history route lists saved records and supports search/filter."""
    # First create an assessment
    db_path = test_app.config['DATABASE_PATH']
    facts = {
        'traffic': 'Heavy',
        'weather': 'Foggy',
        'road_condition': 'Damaged',
        'road_status': 'Open',
        'vehicle_condition': 'Normal',
        'fuel': 'Low',
        'accident_reported': 'No',
        'emergency_reported': 'No'
    }
    res = {
        'timestamp': '2026-10-13 12:00:00',
        'assessment_summary': 'Fog and damaged road hazard alert',
        'activated_rules': ['R001', 'R004'],
        'recommendations': [{'rule_id': 'R001', 'priority': 'Medium', 'recommendation': 'Delay travel', 'explanation': 'Heavy traffic', 'matched_conditions': {}}],
        'explanations': [],
        'highest_priority': 'Medium'
    }
    asm_id = save_assessment(facts, res, db_path)

    # Fetch history page
    history_resp = client.get('/history')
    assert history_resp.status_code == 200
    assert asm_id.encode() in history_resp.data

    # Fetch assessment details view
    detail_resp = client.get(f'/history/{asm_id}')
    assert detail_resp.status_code == 200
    assert asm_id.encode() in detail_resp.data

def test_knowledge_base_routes(client):
    """Knowledge base viewer displays loaded rules and specific rule details."""
    kb_resp = client.get('/knowledge-base')
    assert kb_resp.status_code == 200
    assert b"R001" in kb_resp.data
    assert b"R007" in kb_resp.data

    rule_resp = client.get('/knowledge-base/R001')
    assert rule_resp.status_code == 200
    assert b"Heavy Traffic Advisory" in rule_resp.data
    assert b"IF PRECONDITIONS" in rule_resp.data

def test_analytics_and_api_routes(client):
    """Analytics page and JSON API endpoint work properly."""
    page_resp = client.get('/analytics')
    assert page_resp.status_code == 200
    assert b"Transportation Analytics" in page_resp.data

    api_resp = client.get('/api/analytics')
    assert api_resp.status_code == 200
    assert api_resp.is_json
    data = api_resp.get_json()
    assert 'category_distribution' in data
    assert 'priority_distribution' in data

def test_about_page_route(client):
    """About project page displays problem statement, objectives, and architecture."""
    resp = client.get('/about')
    assert resp.status_code == 200
    assert b"Rule Based Expert System For Road Transportation" in resp.data
    assert b"Forward Chaining" in resp.data
    assert b"Explanation Facility" in resp.data

def test_add_dynamic_rule_route_and_evaluation(client):
    """Dynamic rule creation expands knowledge base and immediately influences evaluation."""
    # 1. Fetch add rule form
    form_resp = client.get('/rules/add')
    assert form_resp.status_code == 200
    assert b"Add Dynamic Production Rule" in form_resp.data

    # 2. Add a dynamic rule via POST API
    new_rule_payload = {
        "id": "R999",
        "name": "Dynamic Fog & Low Fuel Alert",
        "category": "Weather Advisory",
        "description": "Dynamic rule testing combined fog and fuel depletion.",
        "conditions": {
            "weather": "Foggy",
            "fuel": "Low"
        },
        "operator": "AND",
        "recommendation": "Emergency refueling protocol active: Pull into nearest station immediately under fog guidance.",
        "explanation": "Low fuel during dense fog risks complete vehicular immobilization in hazardous low-visibility corridor.",
        "priority": "High",
        "enabled": True
    }
    api_resp = client.post('/api/rules/add', json=new_rule_payload)
    assert api_resp.status_code == 201
    assert api_resp.json['success'] is True

    # 3. Test that evaluation immediately activates this dynamic rule!
    eval_data = {
        'traffic': 'Low',
        'weather': 'Foggy',
        'road_condition': 'Good',
        'road_status': 'Open',
        'vehicle_condition': 'Normal',
        'fuel': 'Low',
        'accident_reported': 'No',
        'emergency_reported': 'No'
    }
    eval_resp = client.post('/analyze', data=eval_data, follow_redirects=True)
    assert eval_resp.status_code == 200
    assert b"R999" in eval_resp.data
    assert b"Emergency refueling protocol active" in eval_resp.data

    # Clean up test rule
    client.post('/api/rules/R999/delete')

def test_ai_endpoints(client):
    """AI endpoints for key configuration, report analysis, KB audit, and chat."""
    # Test setting key in session
    set_key_resp = client.post('/api/ai/set-key', json={'api_key': 'test-fake-key-12345'})
    assert set_key_resp.status_code == 200
    assert set_key_resp.json['success'] is True

    # Test clearing key
    clear_resp = client.post('/api/ai/set-key', json={'api_key': ''})
    assert clear_resp.status_code == 200

    # Test assistant page route
    asst_resp = client.get('/ai-assistant')
    assert asst_resp.status_code == 200
    assert b"AI Transportation Expert Consultant" in asst_resp.data

    # Test AI chat endpoint in offline heuristic mode
    chat_resp = client.post('/api/ai/chat', json={'message': 'How does the expert system handle heavy rain?'})
    assert chat_resp.status_code == 200
    assert 'reply' in chat_resp.json

def test_404_error_page(client):
    """Non-existent URLs trigger clean 404 response."""
    resp = client.get('/non-existent-page-url')
    assert resp.status_code == 404
    assert b"Resource Not Found" in resp.data
