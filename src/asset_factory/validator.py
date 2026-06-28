import json
import logging
from typing import Dict, Any, List, Tuple
from .brief_schema import BriefSchema

logger = logging.getLogger(__name__)

class BriefValidator:
    @staticmethod
    def validate(brief_data: Dict[str, Any]) -> Tuple[bool, List[str], List[str], List[str]]:
        """
        Validates brief data.
        Returns: (is_valid, missing_fields, warnings, suggestions)
        """
        is_valid = True
        missing_fields = []
        warnings = []
        suggestions = []

        required_fields = BriefSchema.get_required_fields()
        allowed_values = BriefSchema.get_allowed_values()

        # Check required fields
        for field in required_fields:
            if field not in brief_data or not brief_data[field]:
                missing_fields.append(field)
                is_valid = False

        # Check allowed values
        for field, allowed in allowed_values.items():
            if field in brief_data and brief_data[field] not in allowed:
                warnings.append(f"Field '{field}' has unexpected value '{brief_data[field]}'. Expected one of: {allowed}.")

        # Business logic validation
        if "description" in brief_data and len(str(brief_data["description"])) < 10:
            warnings.append("Description is too short. It might not generate good prompts.")
            suggestions.append("Provide a more detailed description (at least 2-3 sentences).")

        if "target_outputs" in brief_data and isinstance(brief_data["target_outputs"], list):
            if len(brief_data["target_outputs"]) == 0:
                warnings.append("target_outputs list is empty.")
                suggestions.append("Specify at least one target output format (e.g. 'png', 'mp4').")

        if not missing_fields and not warnings:
            suggestions.append("Brief looks great and is ready for production.")

        return is_valid, missing_fields, warnings, suggestions

    @staticmethod
    def validate_file(filepath: str) -> Dict[str, Any]:
        result = {
            "status": "invalid",
            "missing_fields": [],
            "warnings": [],
            "suggestions": []
        }
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            is_valid, missing, warnings, suggestions = BriefValidator.validate(data)
            result["status"] = "valid" if is_valid else "invalid"
            result["missing_fields"] = missing
            result["warnings"] = warnings
            result["suggestions"] = suggestions
            
        except json.JSONDecodeError:
            result["warnings"].append("File is not valid JSON.")
        except FileNotFoundError:
            result["warnings"].append(f"File not found: {filepath}")
        except Exception as e:
            result["warnings"].append(f"Unknown error parsing brief: {str(e)}")
            
        return result
