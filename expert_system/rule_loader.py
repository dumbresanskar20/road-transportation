"""
Rule Loader for Road Transportation Expert System.
Handles safe loading, JSON parsing, validation, and querying of rules from knowledge base.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

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
        categories = sorted({r['category'] for r in self._rules if 'category' in r})
        return categories

    def count(self, include_disabled: bool = True) -> int:
        """Returns count of rules."""
        return len(self.get_all_rules(include_disabled))

    def get_next_rule_id(self) -> str:
        """Generates the next available rule identifier (e.g., R026)."""
        max_num = 0
        for r in self._rules:
            rid = str(r.get('id', ''))
            if rid.startswith('R') and rid[1:].isdigit():
                max_num = max(max_num, int(rid[1:]))
        return f"R{max_num + 1:03d}"

    def save_rules_to_file(self) -> bool:
        """Saves current in-memory rules back to the JSON knowledge base file."""
        try:
            # Ensure parent directory exists
            self.rules_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.rules_file_path, 'w', encoding='utf-8') as f:
                json.dump(self._rules, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to write rules to {self.rules_file_path}: {e}")
            return False

    def add_rule(self, rule_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Dynamically adds a new rule to the knowledge base, validates schema, and persists to file.
        
        Returns:
            (success: bool, message: str, rule: dict or None)
        """
        if not isinstance(rule_data, dict):
            return False, "Rule payload must be a dictionary.", None

        # Auto-assign rule ID if empty
        if not rule_data.get('id'):
            rule_data['id'] = self.get_next_rule_id()
        else:
            rule_data['id'] = str(rule_data['id']).strip().upper()

        rule_id = rule_data['id']

        # Prevent duplicate ID
        if rule_id in self._rules_by_id:
            return False, f"Rule ID '{rule_id}' already exists in the Knowledge Base.", None

        # Standardize operator & priority
        rule_data['operator'] = str(rule_data.get('operator', 'AND')).upper()
        rule_data['priority'] = str(rule_data.get('priority', 'Medium')).capitalize()
        if 'enabled' not in rule_data:
            rule_data['enabled'] = True

        # Validate against schema
        is_valid, validation_err = validate_rule_schema(rule_data)
        if not is_valid:
            return False, f"Rule validation error: {validation_err}", None

        # Append to in-memory store
        self._rules.append(rule_data)
        self._rules_by_id[rule_id] = rule_data

        # Persist to JSON file
        saved = self.save_rules_to_file()
        if not saved:
            # Rollback if file save failed
            self._rules.remove(rule_data)
            del self._rules_by_id[rule_id]
            return False, "Failed to persist new rule to knowledge base file.", None

        logger.info(f"Dynamically added new rule '{rule_id}' to knowledge base.")
        return True, f"Rule '{rule_id}' created and activated successfully.", rule_data

    def delete_rule(self, rule_id: str) -> Tuple[bool, str]:
        """Removes a rule by ID and updates the knowledge base file."""
        if rule_id not in self._rules_by_id:
            return False, f"Rule '{rule_id}' not found."

        rule = self._rules_by_id.pop(rule_id)
        self._rules = [r for r in self._rules if r.get('id') != rule_id]

        saved = self.save_rules_to_file()
        if not saved:
            # Rollback
            self._rules.append(rule)
            self._rules_by_id[rule_id] = rule
            return False, "Failed to update knowledge base file after deletion."

        return True, f"Rule '{rule_id}' was successfully removed."

    def toggle_rule(self, rule_id: str) -> Tuple[bool, str, bool]:
        """Toggles the enabled status of a rule and persists change."""
        rule = self._rules_by_id.get(rule_id)
        if not rule:
            return False, f"Rule '{rule_id}' not found.", False

        new_status = not rule.get('enabled', True)
        rule['enabled'] = new_status
        saved = self.save_rules_to_file()
        if not saved:
            rule['enabled'] = not new_status
            return False, "Failed to persist rule state change.", not new_status

        status_str = "enabled" if new_status else "disabled"
        return True, f"Rule '{rule_id}' has been {status_str}.", new_status
