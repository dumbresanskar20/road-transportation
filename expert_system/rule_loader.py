"""
Rule Loader for Road Transportation Expert System.
Handles safe loading, JSON parsing, validation, and querying of rules from knowledge base.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from .validators import validate_rule_schema

logger = logging.getLogger(__name__)

class RuleLoader:
    """Loads and caches transportation rules from JSON knowledge base."""

    def __init__(self, rules_file_path: str):
        self.rules_file_path = Path(rules_file_path)
        self._rules: List[Dict[str, Any]] = []
        self._rules_by_id: Dict[str, Dict[str, Any]] = {}
        self.load_errors: List[str] = []
        self.load_rules()

    def load_rules(self) -> List[Dict[str, Any]]:
        """
        Loads rules from the JSON file, validating each against the schema.
        Skips invalid rules while logging clear error messages.
        """
        self._rules = []
        self._rules_by_id = {}
        self.load_errors = []

        if not self.rules_file_path.exists():
            error_msg = f"Knowledge base file not found at: {self.rules_file_path}"
            logger.error(error_msg)
            self.load_errors.append(error_msg)
            return []

        try:
            with open(self.rules_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON knowledge base: {e}"
            logger.error(error_msg)
            self.load_errors.append(error_msg)
            return []
        except Exception as e:
            error_msg = f"Unexpected error reading knowledge base: {e}"
            logger.error(error_msg)
            self.load_errors.append(error_msg)
            return []

        if not isinstance(data, list):
            error_msg = "Knowledge base root element must be a JSON array of rule objects."
            logger.error(error_msg)
            self.load_errors.append(error_msg)
            return []

        for idx, rule_data in enumerate(data):
            is_valid, validation_err = validate_rule_schema(rule_data)
            if not is_valid:
                rule_id = rule_data.get('id', f'Index-{idx}') if isinstance(rule_data, dict) else f'Index-{idx}'
                err_str = f"Rule '{rule_id}' failed validation: {validation_err}"
                logger.warning(err_str)
                self.load_errors.append(err_str)
                continue

            # Standardize operator & priority casing
            rule_data['operator'] = rule_data['operator'].upper()
            rule_data['priority'] = rule_data['priority'].capitalize()

            self._rules.append(rule_data)
            self._rules_by_id[rule_data['id']] = rule_data

        logger.info(f"Loaded {len(self._rules)} valid rules from {self.rules_file_path}")
        return self._rules

    def get_all_rules(self, include_disabled: bool = True) -> List[Dict[str, Any]]:
        """Returns all loaded rules, optionally filtering out disabled rules."""
        if include_disabled:
            return list(self._rules)
        return [r for r in self._rules if r.get('enabled', True)]

    def get_rule_by_id(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a rule by its unique ID."""
        return self._rules_by_id.get(rule_id)

    def get_categories(self) -> List[str]:
        """Returns distinct categories of active rules sorted alphabetically."""
        categories = sorted({r['category'] for r in self._rules})
        return categories

    def count(self, include_disabled: bool = True) -> int:
        """Returns count of rules."""
        return len(self.get_all_rules(include_disabled))
