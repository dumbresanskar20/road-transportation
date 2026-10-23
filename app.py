"""
Rule Based Expert System For Road Transportation - Flask Application
A rule-based expert system implementing forward-chaining inference,
interactive knowledge base querying, dynamic rule authoring, AI integration,
SQLite assessment history, and visual analytics.
"""

import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, abort, jsonify, session
from config import config_by_name
from expert_system.rule_engine import RuleEngine
from expert_system.rule_loader import RuleLoader
from expert_system.validators import VALID_FACT_OPTIONS, FIELD_LABELS, VALID_PRIORITIES, VALID_OPERATORS, validate_input_facts
from expert_system.ai_service import (
    analyze_report_with_ai,
    analyze_knowledge_base_with_ai,
    chat_with_transport_ai,
    get_effective_api_key
)
from database.db import (
    init_db,
    save_assessment,
    get_assessment,
    get_all_assessments,
    get_dashboard_stats,
    get_analytics_data
)

def create_app(config_name=None):
    """Application factory for Rule Based Expert System For Road Transportation."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Initialize Database & Engine
    with app.app_context():
        init_db(app.config['DATABASE_PATH'])

    rule_loader = RuleLoader(app.config['RULES_PATH'])
    rule_engine = RuleEngine(rule_loader)

    # Context processor to inject common variables into Jinja templates
    @app.context_processor
    def inject_common():
        return {
            'app_title': 'Rule Based Expert System For Road Transportation',
            'categories': rule_loader.get_categories(),
            'valid_options': VALID_FACT_OPTIONS,
            'field_labels': FIELD_LABELS,
            'valid_priorities': VALID_PRIORITIES,
            'valid_operators': VALID_OPERATORS,
            'next_rule_id': rule_loader.get_next_rule_id()
        }

    # ----------------------------------------------------
    # Core Assessment & Dashboard Routes
    # ----------------------------------------------------

    @app.route('/')
    def dashboard():
        """Home Dashboard displaying real statistics and recent assessments."""
        stats = get_dashboard_stats(app.config['DATABASE_PATH'])
        return render_template('dashboard.html', stats=stats)

    @app.route('/assessment', methods=['GET'])
    def assessment():
        """Interactive assessment form for road and vehicle conditions with dropdown selections."""
        return render_template('assessment.html', errors={}, form_data={})

    @app.route('/analyze', methods=['POST'])
    def analyze():
        """
        Receives user facts from the form, validates input, executes forward chaining,
        stores the result in SQLite, and displays recommendations according to active rules.
        """
        raw_facts = {
            'traffic': request.form.get('traffic', '').strip(),
            'weather': request.form.get('weather', '').strip(),
            'road_condition': request.form.get('road_condition', '').strip(),
            'road_status': request.form.get('road_status', '').strip(),
            'vehicle_condition': request.form.get('vehicle_condition', '').strip(),
            'fuel': request.form.get('fuel', '').strip(),
            'accident_reported': request.form.get('accident_reported', '').strip(),
            'emergency_reported': request.form.get('emergency_reported', '').strip()
        }

        # Validate facts
        is_valid, sanitized_facts, val_errors = validate_input_facts(raw_facts)
        if not is_valid:
            flash("Please correct the highlighted inputs before proceeding.", "danger")
            return render_template('assessment.html', errors=val_errors, form_data=raw_facts), 400

        # Execute rule-based inference engine
        result = rule_engine.evaluate(sanitized_facts)

        # Persist assessment in SQLite
        assessment_id = save_assessment(sanitized_facts, result, app.config['DATABASE_PATH'])

        # Redirect to results view for clean URL & bookmarking
        return redirect(url_for('results', assessment_id=assessment_id))

    @app.route('/results/<assessment_id>', methods=['GET'])
    def results(assessment_id):
        """Displays recommendations, explanation facility, and AI analysis for an assessment."""
        assessment_data = get_assessment(assessment_id, app.config['DATABASE_PATH'])
        if not assessment_data:
            abort(404, description=f"Assessment '{assessment_id}' not found.")

        return render_template('results.html', assessment=assessment_data)

    @app.route('/history', methods=['GET'])
    def history():
        """Assessment history log with filtering, searching, and pagination."""
        search = request.args.get('search', '').strip()
        filter_traffic = request.args.get('traffic', '').strip()
        filter_weather = request.args.get('weather', '').strip()
        filter_priority = request.args.get('priority', '').strip()
        
        try:
            page = max(1, int(request.args.get('page', 1)))
        except ValueError:
            page = 1
            
        per_page = 15
        offset = (page - 1) * per_page

        assessments_list, total_count = get_all_assessments(
            app.config['DATABASE_PATH'],
            search=search if search else None,
            filter_traffic=filter_traffic if filter_traffic else None,
            filter_weather=filter_weather if filter_weather else None,
            filter_priority=filter_priority if filter_priority else None,
            limit=per_page,
            offset=offset
        )

        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

        return render_template(
            'history.html',
            assessments=assessments_list,
            total_count=total_count,
            page=page,
            total_pages=total_pages,
            search=search,
            filter_traffic=filter_traffic,
            filter_weather=filter_weather,
            filter_priority=filter_priority
        )

    @app.route('/history/<assessment_id>', methods=['GET'])
    def assessment_details(assessment_id):
        """Detailed inspection view for a historical assessment."""
        assessment_data = get_assessment(assessment_id, app.config['DATABASE_PATH'])
        if not assessment_data:
            abort(404, description=f"Assessment '{assessment_id}' not found.")

        return render_template('assessment_details.html', assessment=assessment_data)

    # ----------------------------------------------------
    # Knowledge Base & Dynamic Rules Authoring
    # ----------------------------------------------------

    @app.route('/knowledge-base', methods=['GET'])
    def knowledge_base():
        """Knowledge Base viewer displaying active rules and dynamic management."""
        category_filter = request.args.get('category', '').strip()
        search_query = request.args.get('search', '').strip().lower()
        priority_filter = request.args.get('priority', '').strip()

        all_rules = rule_loader.get_all_rules(include_disabled=True)
        filtered_rules = []

        for r in all_rules:
            if category_filter and category_filter != "All" and r.get('category') != category_filter:
                continue
            if priority_filter and priority_filter != "All" and r.get('priority') != priority_filter:
                continue
            if search_query:
                text_corpus = f"{r.get('id', '')} {r.get('name', '')} {r.get('description', '')} {r.get('recommendation', '')} {r.get('category', '')}".lower()
                if search_query not in text_corpus:
                    continue
            filtered_rules.append(r)

        return render_template(
            'knowledge_base.html',
            rules=filtered_rules,
            total_rules=len(all_rules),
            category_filter=category_filter,
            priority_filter=priority_filter,
            search_query=search_query
        )

    @app.route('/knowledge-base/<rule_id>', methods=['GET'])
    def rule_details(rule_id):
        """Inspects full specification, condition logic, and rationale of a single rule."""
        rule = rule_loader.get_rule_by_id(rule_id)
        if not rule:
            abort(404, description=f"Rule '{rule_id}' was not found in the Knowledge Base.")

        return render_template('rule_details.html', rule=rule)

    @app.route('/rules/add', methods=['GET', 'POST'])
    def add_rule():
        """Allows users to dynamically formulate and save new IF-THEN rules."""
        if request.method == 'GET':
            next_id = rule_loader.get_next_rule_id()
            return render_template('add_rule.html', next_id=next_id, form_data={})

        # Process form submission
        rule_id = request.form.get('id', '').strip() or rule_loader.get_next_rule_id()
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        if category == '__new__':
            category = request.form.get('new_category', '').strip()
        description = request.form.get('description', '').strip()
        operator = request.form.get('operator', 'AND').strip().upper()
        priority = request.form.get('priority', 'Medium').strip().capitalize()
        recommendation = request.form.get('recommendation', '').strip()
        explanation = request.form.get('explanation', '').strip()

        # Build conditions dictionary from selected form factors
        conditions = {}
        for factor_key in VALID_FACT_OPTIONS.keys():
            selected_val = request.form.get(f'cond_{factor_key}', '').strip()
            if selected_val:
                conditions[factor_key] = selected_val

        rule_data = {
            'id': rule_id,
            'name': name,
            'category': category,
            'description': description,
            'conditions': conditions,
            'operator': operator,
            'priority': priority,
            'recommendation': recommendation,
            'explanation': explanation,
            'enabled': True
        }

        success, message, created_rule = rule_loader.add_rule(rule_data)
        if not success:
            flash(message, "danger")
            return render_template('add_rule.html', next_id=rule_id, form_data=request.form), 400

        flash(f"Rule {rule_id} ('{name}') was dynamically created and added to the Knowledge Base!", "success")
        return redirect(url_for('knowledge_base'))

    @app.route('/api/rules/add', methods=['POST'])
    def api_add_rule():
        """JSON API endpoint to dynamically add a new rule."""
        data = request.get_json(silent=True) or {}
        success, message, rule = rule_loader.add_rule(data)
        status_code = 201 if success else 400
        return jsonify({'success': success, 'message': message, 'rule': rule}), status_code

    @app.route('/api/rules/<rule_id>/toggle', methods=['POST'])
    def api_toggle_rule(rule_id):
        """API endpoint to enable or disable a rule in the knowledge base."""
        success, message, new_state = rule_loader.toggle_rule(rule_id)
        return jsonify({'success': success, 'message': message, 'enabled': new_state}), (200 if success else 404)

    @app.route('/api/rules/<rule_id>/delete', methods=['POST', 'DELETE'])
    def api_delete_rule(rule_id):
        """API endpoint to delete a rule from the knowledge base."""
        success, message = rule_loader.delete_rule(rule_id)
        return jsonify({'success': success, 'message': message}), (200 if success else 404)

    # ----------------------------------------------------
    # AI Integration Endpoints
    # ----------------------------------------------------

    @app.route('/api/ai/set-key', methods=['POST'])
    def api_set_ai_key():
        """Saves user-supplied AI API key into current browser session."""
        data = request.get_json(silent=True) or request.form
        api_key = data.get('api_key', '').strip()
        if not api_key:
            session.pop('ai_api_key', None)
            session.pop('gemini_api_key', None)
            return jsonify({'success': True, 'message': 'API Key removed.'})

        session['ai_api_key'] = api_key
        session['gemini_api_key'] = api_key
        return jsonify({'success': True, 'message': 'API Key saved successfully for this session!'})

    @app.route('/api/ai/analyze-report', methods=['POST'])
    def api_analyze_report():
        """Analyzes an assessment report using AI."""
        data = request.get_json(silent=True) or request.form
        assessment_id = data.get('assessment_id')
        user_key = data.get('api_key') or session.get('ai_api_key') or session.get('gemini_api_key')

        if not assessment_id:
            return jsonify({'success': False, 'error': 'Assessment ID is required.'}), 400

        assessment_data = get_assessment(assessment_id, app.config['DATABASE_PATH'])
        if not assessment_data:
            return jsonify({'success': False, 'error': f"Assessment '{assessment_id}' not found."}), 404

        analysis_result = analyze_report_with_ai(assessment_data, user_key)
        return jsonify(analysis_result)

    @app.route('/api/ai/analyze-kb', methods=['POST'])
    def api_analyze_kb():
        """Performs a comprehensive AI health audit of the entire rule base."""
        data = request.get_json(silent=True) or request.form or {}
        user_key = data.get('api_key') or session.get('ai_api_key') or session.get('gemini_api_key')
        rules = rule_loader.get_all_rules(include_disabled=True)
        audit_result = analyze_knowledge_base_with_ai(rules, user_key)
        return jsonify(audit_result)

    @app.route('/ai-assistant', methods=['GET'])
    def ai_assistant():
        """Interactive AI Transportation Consultant page."""
        return render_template('ai_assistant.html')

    @app.route('/api/ai/chat', methods=['POST'])
    def api_ai_chat():
        """Interactive Q&A route with AI for transportation queries."""
        data = request.get_json(silent=True) or request.form or {}
        message = data.get('message', '').strip()
        user_key = data.get('api_key') or session.get('ai_api_key') or session.get('gemini_api_key')
        context = data.get('context')

        if not message:
            return jsonify({'success': False, 'error': 'Message cannot be empty.'}), 400

        response = chat_with_transport_ai(message, context_data=context, api_key=user_key)
        return jsonify(response)

    # ----------------------------------------------------
    # Analytics & About Pages
    # ----------------------------------------------------

    @app.route('/analytics', methods=['GET'])
    def analytics():
        """Visual analytics for system assessments using Chart.js."""
        analytics_data = get_analytics_data(app.config['DATABASE_PATH'])
        return render_template('analytics.html', data=analytics_data)

    @app.route('/api/analytics', methods=['GET'])
    def api_analytics():
        """JSON endpoint supplying real SQLite data for dynamic charts."""
        analytics_data = get_analytics_data(app.config['DATABASE_PATH'])
        return jsonify(analytics_data)

    @app.route('/about', methods=['GET'])
    def about():
        """System architecture, declarative IF-THEN AI concepts, and knowledge design."""
        rule_count = rule_loader.count(include_disabled=True)
        return render_template('about.html', rule_count=rule_count)

    # ----------------------------------------------------
    # Error Handlers
    # ----------------------------------------------------

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html', error=e), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('404.html', error="An unexpected server error occurred. Please try again later."), 500

    return app

# Top-level instance for WSGI servers (Gunicorn, Render, etc.)
app = create_app(os.environ.get('FLASK_ENV', 'production'))

if __name__ == '__main__':
    application = create_app('development')
    application.run(host='127.0.0.1', port=5000, debug=True)
