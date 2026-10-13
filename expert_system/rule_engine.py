"""
Forward-Chaining Rule Inference Engine for Road Transportation Expert System.
Evaluates working memory facts against knowledge base rules, resolves priorities,
and generates structured, explainable recommendations.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from .rule_loader import RuleLoader
from .explanation import ExplanationFacility
from .validators import validate_input_facts

logger = logging.getLogger(__name__)

PRIORITY_WEIGHTS = {
    'High': 3,
    'Medium': 2,
    'Low': 1,
    'Neutral': 0
}

class RuleEngine:
    """
    Expert system inference engine employing forward chaining over transportation rules.
    """

    def __init__(self, rules_path_or_loader):
        if isinstance(rules_path_or_loader, RuleLoader):
            self.loader = rules_path_or_loader
        else:
            self.loader = RuleLoader(rules_path_or_loader)

    def evaluate(self, raw_facts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes forward chaining inference over user facts.
        
        Args:
            raw_facts: Dictionary of user inputs.
            
        Returns:
            Structured assessment result dictionary.
        """
        # Step 1: Validate and sanitize facts
        is_valid, facts, val_errors = validate_input_facts(raw_facts)
        if not is_valid:
            return {
                "success": False,
                "errors": val_errors,
                "assessment_summary": "Input validation failed. Please check submitted conditions.",
                "activated_rules": [],
                "recommendations": [],
                "explanations": [],
                "highest_priority": "Neutral",
                "total_activated": 0,
                "has_emergency": False,
                "has_closure": False,
                "evaluated_facts": raw_facts
            }

        # Step 2: Retrieve enabled rules from Knowledge Base
        all_rules = self.loader.get_all_rules(include_disabled=False)
        
        activated_rule_ids: List[str] = []
        raw_recommendations: List[Dict[str, Any]] = []
        explanations: List[Dict[str, Any]] = []

        # Step 3: Forward Chaining Rule Matching
        for rule in all_rules:
            # Rule must be enabled
            if not rule.get('enabled', True):
                continue

            conditions = rule.get('conditions', {})
            operator = rule.get('operator', 'AND').upper()
            
            clause_eval_results = []

            for field, expected_val in conditions.items():
                actual_val = facts.get(field)
                matched = False

                if actual_val is not None:
                    if isinstance(expected_val, list):
                        # Match if actual value is among expected options (OR list)
                        matched = any(str(actual_val).lower() == str(exp).lower() for exp in expected_val)
                        expected_repr = " OR ".join([f"'{exp}'" for exp in expected_val])
                        expr = f"{field} in [{expected_repr}] ({actual_val}) -> {'TRUE' if matched else 'FALSE'}"
                    else:
                        matched = (str(actual_val).lower() == str(expected_val).lower())
                        expr = f"{field} == '{expected_val}' ({actual_val}) -> {'TRUE' if matched else 'FALSE'}"
                else:
                    expr = f"{field} is MISSING -> FALSE"

                clause_eval_results.append({
                    "field": field,
                    "fact_val": actual_val,
                    "expected": expected_val,
                    "matched": matched,
                    "expr": expr
                })

            # Evaluate conjunction (AND) or disjunction (OR)
            if operator == 'AND':
                is_rule_active = all(c['matched'] for c in clause_eval_results) if clause_eval_results else False
            elif operator == 'OR':
                is_rule_active = any(c['matched'] for c in clause_eval_results) if clause_eval_results else False
            else:
                is_rule_active = False

            # If rule triggers, fire recommendation & explanation
            if is_rule_active:
                rule_id = rule['id']
                activated_rule_ids.append(rule_id)

                # Generate detailed explanation trace
                trace = ExplanationFacility.create_trace(rule, facts, clause_eval_results)
                explanations.append(trace)

                # Prepare recommendation item
                matched_conditions_summary = {
                    c['field']: c['fact_val'] for c in clause_eval_results if c['matched']
                }

                rec_item = {
                    "rule_id": rule_id,
                    "rule_name": rule.get("name"),
                    "category": rule.get("category"),
                    "priority": rule.get("priority", "Medium"),
                    "recommendation": rule.get("recommendation"),
                    "explanation": rule.get("explanation"),
                    "matched_conditions": matched_conditions_summary
                }
                raw_recommendations.append(rec_item)

        # Step 4: Conflict Resolution and Deduplication
        # Sort recommendations by priority (High -> Medium -> Low)
        sorted_recommendations = sorted(
            raw_recommendations,
            key=lambda r: (
                -PRIORITY_WEIGHTS.get(r['priority'], 1),
                r['category'],
                r['rule_id']
            )
        )

        # Remove duplicate recommendation texts while preserving multiple rules
        unique_recommendations = []
        seen_texts = set()
        for rec in sorted_recommendations:
            rec_text = rec['recommendation'].strip()
            if rec_text not in seen_texts:
                seen_texts.add(rec_text)
                unique_recommendations.append(rec)

        # Determine highest priority
        highest_priority = "Neutral"
        if unique_recommendations:
            highest_weight = max(PRIORITY_WEIGHTS.get(r['priority'], 1) for r in unique_recommendations)
            for p, w in PRIORITY_WEIGHTS.items():
                if w == highest_weight:
                    highest_priority = p
                    break

        # Check special domain flags
        has_emergency = (facts.get('emergency_reported') == 'Yes' or 
                         any(r['category'] == 'Accident and Emergency' for r in unique_recommendations))
        has_closure = (facts.get('road_status') == 'Closed')

        # Generate overall assessment summary
        if len(unique_recommendations) == 0:
            assessment_summary = (
                "Neutral Advisory: No configured transportation advisories matched the current conditions. "
                "Please note that the system cannot guarantee absolute road safety; "
                "continue to exercise standard driving care and observe local road signs."
            )
        elif has_emergency:
            assessment_summary = (
                "CRITICAL SAFETY ALERT: Active emergency or incident reported. "
                "Emergency instructions take precedence over routine travel recommendations."
            )
        elif has_closure:
            assessment_summary = (
                "STRICT ROAD CLOSURE: The selected road corridor is closed to traffic. "
                "Do not attempt to enter closed segments under any circumstances; utilize designated official detours."
            )
        elif len(unique_recommendations) > 1:
            assessment_summary = (
                f"Multiple transportation advisories ({len(unique_recommendations)}) detected across "
                f"{len(set(r['category'] for r in unique_recommendations))} categories based on prevailing conditions."
            )
        else:
            assessment_summary = "Transportation advisory generated for current travel conditions."

        return {
            "success": True,
            "assessment_summary": assessment_summary,
            "activated_rules": activated_rule_ids,
            "recommendations": unique_recommendations,
            "explanations": explanations,
            "highest_priority": highest_priority,
            "total_activated": len(activated_rule_ids),
            "has_emergency": has_emergency,
            "has_closure": has_closure,
            "evaluated_facts": facts,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
