"""
Explanation Facility for Road Transportation Expert System.
Builds transparent, inspectable reasoning traces for activated rules.
"""

from typing import Dict, Any, List

class ExplanationFacility:
    """Generates structured reasoning traces explaining why each rule was activated."""

    @staticmethod
    def create_trace(rule: Dict[str, Any], 
                     user_facts: Dict[str, Any], 
                     condition_eval_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Creates an audit trail explaining how user facts satisfied the rule conditions.
        
        Args:
            rule: Rule dictionary from knowledge base.
            user_facts: The full dictionary of user input facts.
            condition_eval_results: List of evaluations for each condition clause:
                [
                    {
                        "field": "weather",
                        "fact_val": "Rainy",
                        "expected": "Rainy",
                        "matched": True,
                        "expr": "weather == 'Rainy' -> TRUE"
                    }, ...
                ]
        """
        matched_facts = {}
        for eval_res in condition_eval_results:
            field = eval_res["field"]
            if field in user_facts:
                matched_facts[field] = user_facts[field]

        operator = rule.get('operator', 'AND')
        passed_count = sum(1 for c in condition_eval_results if c['matched'])
        total_conditions = len(condition_eval_results)

        if operator == 'AND':
            operator_summary = f"All {total_conditions} condition(s) satisfied ({passed_count}/{total_conditions} passed)."
            conclusion = f"Rule '{rule['id']}' triggered because all conjunctive (AND) preconditions were satisfied."
        else: # OR
            operator_summary = f"At least one condition satisfied ({passed_count}/{total_conditions} passed)."
            conclusion = f"Rule '{rule['id']}' triggered because at least one disjunctive (OR) precondition was satisfied."

        return {
            "rule_id": rule.get("id"),
            "rule_name": rule.get("name"),
            "category": rule.get("category"),
            "priority": rule.get("priority"),
            "description": rule.get("description"),
            "operator": operator,
            "operator_summary": operator_summary,
            "matched_user_facts": matched_facts,
            "condition_evaluations": condition_eval_results,
            "conclusion": conclusion,
            "recommendation": rule.get("recommendation"),
            "explanation": rule.get("explanation")
        }
