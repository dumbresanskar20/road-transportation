"""
Database Access Layer for Road Transportation Expert System.
Uses standard library sqlite3 with parameterized queries and safe JSON serialization.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

DB_SCHEMA_FILE = Path(__file__).resolve().parent / 'schema.sql'

def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Creates a sqlite3 connection with dict-like row access."""
    if db_path != ':memory:':
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str) -> None:
    """Initializes SQLite database using schema.sql."""
    conn = get_db_connection(db_path)
    try:
        with open(DB_SCHEMA_FILE, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

def save_assessment(facts: Dict[str, Any], result: Dict[str, Any], db_path: str) -> str:
    """
    Saves a completed assessment to SQLite.
    
    Returns:
        The generated unique assessment ID string.
    """
    assessment_id = f"ASM-{uuid.uuid4().hex[:8].upper()}"
    timestamp = result.get('timestamp') or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO assessments (
                id, timestamp, traffic, weather, road_condition, road_status,
                vehicle_condition, fuel, accident_reported, emergency_reported,
                input_facts_json, activated_rule_ids_json, recommendations_json,
                explanations_json, summary, highest_priority, rule_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assessment_id,
                timestamp,
                facts.get('traffic', 'Unknown'),
                facts.get('weather', 'Unknown'),
                facts.get('road_condition', 'Unknown'),
                facts.get('road_status', 'Unknown'),
                facts.get('vehicle_condition', 'Unknown'),
                facts.get('fuel', 'Unknown'),
                facts.get('accident_reported', 'No'),
                facts.get('emergency_reported', 'No'),
                json.dumps(facts),
                json.dumps(result.get('activated_rules', [])),
                json.dumps(result.get('recommendations', [])),
                json.dumps(result.get('explanations', [])),
                result.get('assessment_summary', ''),
                result.get('highest_priority', 'Neutral'),
                len(result.get('activated_rules', []))
            )
        )
        conn.commit()
        return assessment_id
    finally:
        conn.close()

def get_assessment(assessment_id: str, db_path: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single assessment by ID with deserialized JSON payloads."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return _format_assessment_row(row)
    finally:
        conn.close()

def get_all_assessments(
    db_path: str,
    search: Optional[str] = None,
    filter_traffic: Optional[str] = None,
    filter_weather: Optional[str] = None,
    filter_priority: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Retrieves assessments with optional filtering and search, plus total count.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        
        where_clauses = []
        params: List[Any] = []

        if search and search.strip():
            s = f"%{search.strip()}%"
            where_clauses.append("(id LIKE ? OR summary LIKE ? OR activated_rule_ids_json LIKE ?)")
            params.extend([s, s, s])

        if filter_traffic and filter_traffic.strip() and filter_traffic != "All":
            where_clauses.append("traffic = ?")
            params.append(filter_traffic.strip())

        if filter_weather and filter_weather.strip() and filter_weather != "All":
            where_clauses.append("weather = ?")
            params.append(filter_weather.strip())

        if filter_priority and filter_priority.strip() and filter_priority != "All":
            where_clauses.append("highest_priority = ?")
            params.append(filter_priority.strip())

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # Total count query
        count_query = f"SELECT COUNT(*) FROM assessments {where_sql}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # Fetch records query
        data_query = f"""
            SELECT * FROM assessments
            {where_sql}
            ORDER BY timestamp DESC, id DESC
            LIMIT ? OFFSET ?
        """
        cursor.execute(data_query, params + [limit, offset])
        rows = cursor.fetchall()

        assessments = [_format_assessment_row(r) for r in rows]
        return assessments, total_count
    finally:
        conn.close()

def get_dashboard_stats(db_path: str) -> Dict[str, Any]:
    """
    Computes real summary metrics and recent history for the home dashboard.
    Gracefully handles empty database.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()

        # Total assessments
        cursor.execute("SELECT COUNT(*) FROM assessments")
        total_assessments = cursor.fetchone()[0]

        # Total assessments with advisories (rules > 0)
        cursor.execute("SELECT COUNT(*) FROM assessments WHERE rule_count > 0")
        with_advisories = cursor.fetchone()[0]

        # Highest priority distribution
        cursor.execute("SELECT highest_priority, COUNT(*) FROM assessments GROUP BY highest_priority")
        priority_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # Recent 5 assessments
        cursor.execute("SELECT * FROM assessments ORDER BY timestamp DESC, id DESC LIMIT 5")
        recent_rows = cursor.fetchall()
        recent_assessments = [_format_assessment_row(r) for r in recent_rows]

        # Rule activations tally & recommendation categories
        cursor.execute("SELECT activated_rule_ids_json, recommendations_json FROM assessments")
        all_rows = cursor.fetchall()

        rule_counter: Dict[str, int] = {}
        category_counter: Dict[str, int] = {}

        for row in all_rows:
            try:
                rule_ids = json.loads(row[0]) if row[0] else []
                for rid in rule_ids:
                    rule_counter[rid] = rule_counter.get(rid, 0) + 1
            except Exception:
                pass

            try:
                recs = json.loads(row[1]) if row[1] else []
                for rec in recs:
                    cat = rec.get('category', 'General')
                    category_counter[cat] = category_counter.get(cat, 0) + 1
            except Exception:
                pass

        # Most active rules sorted
        top_rules = sorted(rule_counter.items(), key=lambda x: x[1], reverse=True)[:5]
        top_rules_list = [{"rule_id": r[0], "count": r[1]} for r in top_rules]

        return {
            "total_assessments": total_assessments,
            "advisories_count": with_advisories,
            "priority_counts": priority_counts,
            "recent_assessments": recent_assessments,
            "top_rules": top_rules_list,
            "category_distribution": category_counter,
            "is_empty": (total_assessments == 0)
        }
    finally:
        conn.close()

def get_analytics_data(db_path: str) -> Dict[str, Any]:
    """
    Computes comprehensive analytics datasets for Chart.js.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()

        # Traffic distribution
        cursor.execute("SELECT traffic, COUNT(*) FROM assessments GROUP BY traffic")
        traffic_dist = {row[0]: row[1] for row in cursor.fetchall()}

        # Weather distribution
        cursor.execute("SELECT weather, COUNT(*) FROM assessments GROUP BY weather")
        weather_dist = {row[0]: row[1] for row in cursor.fetchall()}

        # Priority distribution
        cursor.execute("SELECT highest_priority, COUNT(*) FROM assessments GROUP BY highest_priority")
        priority_dist = {row[0]: row[1] for row in cursor.fetchall()}

        # Timeline (grouped by date)
        cursor.execute("""
            SELECT SUBSTR(timestamp, 1, 10) as assess_date, COUNT(*)
            FROM assessments
            GROUP BY assess_date
            ORDER BY assess_date ASC
            LIMIT 14
        """)
        timeline = [{"date": row[0], "count": row[1]} for row in cursor.fetchall()]

        # Rule activations and Category distribution
        cursor.execute("SELECT activated_rule_ids_json, recommendations_json FROM assessments")
        rows = cursor.fetchall()

        rule_counter: Dict[str, int] = {}
        category_counter: Dict[str, int] = {}

        for row in rows:
            try:
                rule_ids = json.loads(row[0]) if row[0] else []
                for rid in rule_ids:
                    rule_counter[rid] = rule_counter.get(rid, 0) + 1
            except Exception:
                pass

            try:
                recs = json.loads(row[1]) if row[1] else []
                for rec in recs:
                    cat = rec.get('category', 'General')
                    category_counter[cat] = category_counter.get(cat, 0) + 1
            except Exception:
                pass

        top_rules = sorted(rule_counter.items(), key=lambda x: x[1], reverse=True)[:8]

        return {
            "traffic_distribution": traffic_dist,
            "weather_distribution": weather_dist,
            "priority_distribution": priority_dist,
            "timeline": timeline,
            "category_distribution": category_counter,
            "top_rules": [{"rule_id": r[0], "count": r[1]} for r in top_rules],
            "total_records": len(rows)
        }
    finally:
        conn.close()

def _format_assessment_row(row: sqlite3.Row) -> Dict[str, Any]:
    """Helper to convert sqlite3.Row to structured Python dict with JSON deserialization."""
    d = dict(row)
    try:
        d['input_facts'] = json.loads(d.get('input_facts_json', '{}'))
    except Exception:
        d['input_facts'] = {}

    try:
        d['activated_rule_ids'] = json.loads(d.get('activated_rule_ids_json', '[]'))
    except Exception:
        d['activated_rule_ids'] = []

    try:
        d['recommendations'] = json.loads(d.get('recommendations_json', '[]'))
    except Exception:
        d['recommendations'] = []

    try:
        d['explanations'] = json.loads(d.get('explanations_json', '[]'))
    except Exception:
        d['explanations'] = []

    return d
