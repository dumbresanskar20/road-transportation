"""
AI Integration Service for Rule Based Expert System For Road Transportation.
Provides deep AI analysis of expert system rules, assessment reports, and intelligent interactive consultation.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load .env file automatically
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

logger = logging.getLogger(__name__)

AI_MODELS = [
    "gemini-3.8-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash"
]

def get_effective_api_key(user_key: Optional[str] = None) -> Optional[str]:
    """
    Resolves the AI API key prioritizing explicit user key, environment variables, or app config.
    """
    if user_key and str(user_key).strip():
        return str(user_key).strip()
    env_key = os.environ.get("AI_API_KEY", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key
    try:
        from flask import current_app
        if current_app:
            return (
                str(current_app.config.get("AI_API_KEY", "")).strip()
                or str(current_app.config.get("GEMINI_API_KEY", "")).strip()
                or None
            )
    except Exception:
        pass
    return None


def call_ai_api(prompt: str, api_key: str, system_instruction: str = "") -> Tuple[bool, str]:
    """
    Executes a direct REST call to the AI endpoint.
    
    Returns:
        (success: bool, response_text_or_error: str)
    """
    if not api_key:
        return False, "AI API Key is not configured."

    payload: Dict[str, Any] = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.35,
            "topP": 0.95,
            "maxOutputTokens": 2048
        }
    }

    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    headers = {"Content-Type": "application/json"}

    last_error = ""
    for model_name in AI_MODELS:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=25)
            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        text = parts[0].get("text", "").strip()
                        return True, text
                return False, "AI returned an empty response. Please retry."
            elif response.status_code in (400, 403):
                err_data = response.json().get("error", {})
                err_msg = err_data.get("message", response.text)
                return False, f"AI API Error ({response.status_code}): {err_msg}"
            else:
                last_error = f"Model {model_name} returned status {response.status_code}: {response.text}"
                continue
        except requests.exceptions.Timeout:
            last_error = "Connection to AI API timed out (25s). Please check your internet connection."
        except Exception as e:
            last_error = f"AI API connection error: {str(e)}"

    return False, last_error or "Unable to contact AI services."


# Alias for backward compatibility
call_gemini_api = call_ai_api


def analyze_report_with_ai(assessment: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs comprehensive AI analysis on an expert system assessment report.
    Analyzes facts, activated rules, priority, and recommends tactical actions.
    """
    effective_key = get_effective_api_key(api_key)
    facts = assessment.get("input_facts", {})
    recommendations = assessment.get("recommendations", [])
    summary = assessment.get("summary", "")
    priority = assessment.get("highest_priority", "Neutral")
    activated_rules = assessment.get("activated_rule_ids", [])

    if not effective_key:
        return {
            "success": True,
            "is_ai_live": False,
            "analysis": generate_fallback_report_analysis(facts, recommendations, priority, summary)
        }

    system_prompt = (
        "You are an Advanced Intelligent Road Transportation & Safety Expert Advisor integrated into "
        "the 'Rule Based Expert System For Road Transportation'. "
        "Analyze the provided road condition facts and expert rule engine outputs. "
        "Provide a clear, authoritative, highly structured advisory in clean Markdown with: "
        "1. Executive Road Safety Overview\n"
        "2. Tactical Commute & Routing Strategy\n"
        "3. Driver Human Factors & Preventive Measures\n"
        "4. Contingency & Safety Action Checklist\n"
        "Keep the tone professional, objective, safety-oriented, and actionable."
    )

    prompt = f"""
Assessment Context:
- Assessment ID: {assessment.get('id', 'N/A')}
- Prevailing Facts:
  * Traffic Density: {facts.get('traffic', 'Unknown')}
  * Weather: {facts.get('weather', 'Unknown')}
  * Road Surface Condition: {facts.get('road_condition', 'Unknown')}
  * Highway Status: {facts.get('road_status', 'Unknown')}
  * Vehicle Condition: {facts.get('vehicle_condition', 'Unknown')}
  * Fuel Level: {facts.get('fuel', 'Unknown')}
  * Accident Reported: {facts.get('accident_reported', 'No')}
  * Emergency Reported: {facts.get('emergency_reported', 'No')}

Rule Engine Deductions:
- Overall Priority: {priority}
- Inference Engine Summary: {summary}
- Total Rules Activated: {len(activated_rules)} ({', '.join(activated_rules) if activated_rules else 'None'})

Activated Recommendations from Knowledge Base:
{json.dumps(recommendations, indent=2)}

Please deliver a comprehensive, structured AI deep-dive analysis addressing this exact transportation scenario.
"""

    success, result_text = call_ai_api(prompt, effective_key, system_prompt)
    if success:
        return {
            "success": True,
            "is_ai_live": True,
            "analysis": result_text
        }
    else:
        return {
            "success": False,
            "is_ai_live": False,
            "error": result_text,
            "analysis": generate_fallback_report_analysis(facts, recommendations, priority, summary)
        }


def analyze_knowledge_base_with_ai(rules: List[Dict[str, Any]], api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs holistic AI analysis of the entire Knowledge Base rules:
    evaluates coverage, identifies domain gaps, detects conflicts, and suggests new rules.
    """
    effective_key = get_effective_api_key(api_key)

    categories = sorted({r.get('category', 'General') for r in rules})
    total_rules = len(rules)

    if not effective_key:
        return {
            "success": True,
            "is_ai_live": False,
            "analysis": generate_fallback_kb_analysis(total_rules, categories)
        }

    rules_summary = []
    for r in rules:
        rules_summary.append({
            "id": r.get("id"),
            "name": r.get("name"),
            "category": r.get("category"),
            "conditions": r.get("conditions"),
            "operator": r.get("operator"),
            "priority": r.get("priority"),
            "recommendation": r.get("recommendation")
        })

    system_prompt = (
        "You are an AI Knowledge Engineer and Senior Transportation Systems Auditor. "
        "You are auditing the Knowledge Base of 'Rule Based Expert System For Road Transportation'. "
        "Analyze the complete catalog of production rules provided in JSON. "
        "Provide a comprehensive, high-value audit in Markdown covering:\n"
        "1. Knowledge Base Health & Coverage Score (e.g. 92/100) with key strengths\n"
        "2. Domain Coverage Analysis across Traffic, Weather, Infrastructure, Vehicle Mechanics, and Emergencies\n"
        "3. Potential Gaps & Unhandled Edge Cases (e.g., black ice, gale winds, EV battery depletion, night low-light)\n"
        "4. Top 3 Recommended Production Rules to Add (Provide exact ID, Name, Category, Conditions, Operator, Recommendation, Explanation, Priority)\n"
        "Be constructive, highly rigorous, and clear."
    )

    prompt = f"""
Currently Loaded Knowledge Base Rules ({total_rules} rules across {len(categories)} categories):
Categories: {', '.join(categories)}

Rules Catalog:
{json.dumps(rules_summary, indent=2)}

Please perform a complete diagnostic evaluation of this rule base.
"""

    success, result_text = call_ai_api(prompt, effective_key, system_prompt)
    if success:
        return {
            "success": True,
            "is_ai_live": True,
            "analysis": result_text
        }
    else:
        return {
            "success": False,
            "is_ai_live": False,
            "error": result_text,
            "analysis": generate_fallback_kb_analysis(total_rules, categories)
        }


def chat_with_transport_ai(
    user_message: str,
    context_data: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Interactive Q&A assistant with AI specializing in road transit, rules, and transport safety.
    """
    effective_key = get_effective_api_key(api_key)

    if not effective_key:
        return {
            "success": True,
            "is_ai_live": False,
            "reply": (
                f"**Rule-Based Guidance:** For '{user_message}', please use the **New Assessment** form "
                "to evaluate prevailing road factors or inspect active rules in the **Knowledge Base**."
            )
        }

    system_prompt = (
        "You are the embedded AI Transportation Expert Consultant in the 'Rule Based Expert System For Road Transportation'. "
        "Assist the user with transportation safety protocols, traffic management strategies, road hazard mitigation, "
        "rule formulations, or explaining the system's deductions. Be helpful, concise, well-formatted, and accurate."
    )

    context_str = ""
    if context_data:
        context_str = f"\nCurrent Active Context:\n{json.dumps(context_data, indent=2)}\n"

    prompt = f"{context_str}\nUser Question: {user_message}"

    success, result_text = call_ai_api(prompt, effective_key, system_prompt)
    if success:
        return {
            "success": True,
            "is_ai_live": True,
            "reply": result_text
        }
    else:
        return {
            "success": False,
            "is_ai_live": False,
            "error": result_text,
            "reply": f"Sorry, could not contact AI: {result_text}"
        }


def generate_fallback_report_analysis(facts: Dict[str, Any], recommendations: List[Dict[str, Any]], priority: str, summary: str) -> str:
    """Generates a high-quality heuristic analysis when AI is in offline mode."""
    lines = [
        "### 🚦 Executive Road Safety Overview",
        f"**Calculated Threat Level:** `{priority} Priority` &bull; **Engine Deduction:** {summary}",
        "",
        "The current transit profile indicates several concurrent operational variables:",
        f"- **Weather & Traction:** {facts.get('weather', 'Clear')} skies with {facts.get('road_condition', 'Good')} pavement.",
        f"- **Traffic Density & Flow:** {facts.get('traffic', 'Low')} traffic along an {facts.get('road_status', 'Open')} corridor.",
        f"- **Vehicle & Range Readiness:** Vehicle state is {facts.get('vehicle_condition', 'Normal')} with {facts.get('fuel', 'Sufficient')} fuel.",
        "",
        "### 🛡️ Tactical Safety & Routing Strategy",
    ]

    if facts.get("emergency_reported") == "Yes" or facts.get("accident_reported") == "Yes":
        lines.append("- **Urgent Incident Precedence:** Immediate life safety protocols override all standard transit guidance. Dial **112** and establish safe standoff distances.")
    elif facts.get("road_status") == "Closed":
        lines.append("- **Corridor Inaccessibility:** Road closure is absolute. Switch immediately to designated secondary bypass routes.")
    else:
        lines.append("- **Optimal Trajectory:** Proceed along primary routes maintaining calibrated headways.")

    if recommendations:
        lines.append("")
        lines.append("### 📋 Core Actionable Directives from Knowledge Base")
        for idx, r in enumerate(recommendations, 1):
            lines.append(f"{idx}. **[{r.get('priority', 'Medium')}] {r.get('rule_name', 'Rule')}**: {r.get('recommendation')}")

    return "\n".join(lines)


def generate_fallback_kb_analysis(total_rules: int, categories: List[str]) -> str:
    """Generates an audit heuristic overview when AI is in offline mode."""
    return f"""### 📊 Knowledge Base Architecture Audit

**System Overview:**
- **Total Registered Production Rules:** {total_rules}
- **Knowledge Domains:** {', '.join(categories)}
- **Inference Strategy:** Forward-Chaining Deduction with Deterministic Priority Arbitration

### 🔍 Domain Evaluation
1. **Traffic Density & Flow Control:** Comprehensive coverage of Low, Moderate, and Heavy congestion regimes.
2. **Atmospheric & Weather Hazards:** Effective rules addressing Clear, Heavy Rain, Hydroplaning, and Dense Fog.
3. **Pavement & Infrastructure:** Rules covering intact road surfaces, potholes/damaged asphalt, and road closures.
4. **Mechanical & Fuel Reserves:** Vehicle breakdown mitigation, towing requirements, and low-fuel alerts.
5. **Accident & Emergency Incident Response:** Prioritized directives with statutory emergency overriding.

### 🚀 Recommended Rule Expansions
- **R026 - Black Ice / Freezing Rain Advisory:** Triggered when temperature drops near freezing on wet asphalt.
- **R027 - Electric Vehicle Critical Charge Advisory:** Triggered when vehicle battery drops below 10% on high-speed corridors.
- **R028 - High Wind & Gust Hazard for Heavy Vehicles:** High-profile vehicle warnings during severe crosswinds.
"""
