"""
Metric Checker for JSON Comparison

This module provides functionality to compare predicted outputs with real outputs
from JSON files, specifically designed for metadata comparison with different metrics.
"""

import json
from typing import Dict, List, Any, Tuple, Union
from pathlib import Path
import ast
import unicodedata
import re


class MetricChecker:
    """Class for comparing JSON files with different metric strategies."""
    
    def __init__(self, predict_data: Dict[str, Any], real_data: Dict[str, Any]):
        """
        Initialize the MetricChecker with predicted and real JSON data.
        
        Args:
            predict_data: Predicted output JSON data
            real_data: Real/ground truth JSON data
        """
        self.predict_data = predict_data
        self.real_data = real_data
        
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text by converting to lowercase and removing accents.
        Also removes Spanish-specific punctuation like ¿ and ¡.
        Only works with strings and None.
        
        Args:
            text: Text to normalize (string or None)
            
        Returns:
            Normalized text (empty string for None)
        """
        if text is None:
            return ""
        
        if not isinstance(text, str):
            raise TypeError(f"_normalize_text only accepts strings or None, got {type(text)}")
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove Spanish-specific punctuation marks
        text = text.replace('¿', '').replace('¡', '')
        
        # Remove accents using Unicode normalization
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _normalize_value(self, value: Any) -> Any:
        """
        Orchestrator function that normalizes values based on their type.
        - Strings and None: normalized using _normalize_text
        - Lists: each string element normalized, other elements preserved
        - Other types: preserved as-is
        
        Args:
            value: Value to normalize
            
        Returns:
            Normalized value maintaining original type structure
        """
        if value is None or isinstance(value, str):
            return self._normalize_text(value)
        
        if isinstance(value, list):
            normalized_list = []
            for item in value:
                if isinstance(item, str) or item is None:
                    normalized_list.append(self._normalize_text(item))
                else:
                    normalized_list.append(item)  # Preserve non-string items as-is
            return normalized_list
        
        # For other types (int, float, bool, dict, etc.), return as-is
        return value
    
    def _normalize_name_parts(self, name: str) -> List[str]:
        """
        Normalize a person's name by splitting into parts and sorting them.
        This handles cases where names are in different orders (firstname lastname vs lastname firstname).
        
        Args:
            name: Name to normalize
            
        Returns:
            List of normalized name parts sorted alphabetically
        """
        if not isinstance(name, str):
            if name is None:
                return []
            name = str(name)
        
        # Split name by common separators (comma, space, etc.)
        parts = re.split(r'[,\s]+', name.strip())
        
        # Normalize each part and filter out empty strings
        normalized_parts = []
        for part in parts:
            if part.strip():
                normalized_parts.append(self._normalize_text(part.strip()))
        
        # Sort to handle different name orders (John Smith vs Smith John)
        return sorted(normalized_parts)
    
    def _compare_names(self, name1: Any, name2: Any) -> bool:
        """
        Compare two names considering different orders and normalizations.
        
        Args:
            name1: First name to compare
            name2: Second name to compare
            
        Returns:
            True if names match, False otherwise
        """
        if name1 is None and name2 is None:
            return True
        if name1 is None or name2 is None:
            return False
            
        # Normalize both names into sorted parts
        parts1 = self._normalize_name_parts(name1)
        parts2 = self._normalize_name_parts(name2)
        
        # Compare normalized parts
        return parts1 == parts2
    
    def _compare_creator_values(self, creators1: Any, creators2: Any) -> bool:
        """
        Compare creator fields that can be strings or lists with name normalization.
        Handles cases where one is string and other is list, or both are lists.
        
        Args:
            creators1: First creator value (string, list, or None)
            creators2: Second creator value (string, list, or None)
            
        Returns:
            True if creator values match, False otherwise
        """
        # Convert both to lists of strings
        list1 = self._safe_parse_list(creators1)
        list2 = self._safe_parse_list(creators2)
        
        # If different number of creators, they don't match
        if len(list1) != len(list2):
            return False
        
        # If both empty, they match
        if len(list1) == 0:
            return True
        
        # Normalize all names in both lists using name parts comparison
        normalized_names1 = []
        for name in list1:
            normalized_names1.append(self._normalize_name_parts(name))
        
        normalized_names2 = []
        for name in list2:
            normalized_names2.append(self._normalize_name_parts(name))
        
        # Sort both lists to handle different orders of creators
        normalized_names1.sort()
        normalized_names2.sort()
        
        return normalized_names1 == normalized_names2
    
    def _compare_values_with_normalization(self, val1: Any, val2: Any, field_name: str = None) -> bool:
        """
        Compare two values with appropriate normalization based on field type.
        
        Args:
            val1: First value to compare
            val2: Second value to compare
            field_name: Name of the field being compared (for context-specific handling)
            
        Returns:
            True if values match, False otherwise
        """
        # Handle None values
        if val1 is None and val2 is None:
            return True
        if val1 is None or val2 is None:
            return False
        
        # Special handling for creator, director, author fields (names that can have order issues)
        if field_name and field_name.lower() in ['creator', 'director', 'author', 'contributors', 'editors']:
            return self._compare_creator_values(val1, val2)
        
        # For other fields, normalize both values and compare
        norm_val1 = self._normalize_value(val1)
        norm_val2 = self._normalize_value(val2)
        
        return norm_val1 == norm_val2
    
    def discover_all_fields(self) -> set:
        """
        Discover all unique metadata field names present in both datasets.
        This ensures we don't miss any fields that might be specific to certain document types.
        
        Returns:
            Set of all unique field names found across all documents
        """
        all_fields = set()
        
        # Collect fields from predicted data
        for item_id, item_data in self.predict_data.items():
            if isinstance(item_data, dict):
                all_fields.update(item_data.keys())
        
        # Collect fields from real data
        for item_id, item_data in self.real_data.items():
            if isinstance(item_data, dict):
                all_fields.update(item_data.keys())
        
        return all_fields
        
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON data from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {file_path}: {e}")
    
    def _safe_parse_list(self, value: Any) -> List[str]:
        """
        Safely parse a value that might be a string representation of a list.
        
        Args:
            value: The value to parse (could be string, list, or other)
            
        Returns:
            List of strings or empty list if parsing fails
        """
        if isinstance(value, list):
            return [str(item) for item in value]
        elif isinstance(value, str):
            try:
                # Try to parse as literal list
                parsed = ast.literal_eval(value)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
                else:
                    return [value]
            except (ValueError, SyntaxError):
                # If parsing fails, treat as single string
                return [value]
        else:
            return [str(value)] if value is not None else []
    
    def exact_equality_metric(self, field_name: str = None) -> Dict[str, Any]:
        """
        Compare metadata using exact equality.
        
        Args:
            field_name: Specific field to compare. If None, compares all fields.
            
        Returns:
            Dictionary with comparison results
        """
        results = {
            "metric_type": "exact_equality",
            "field_name": field_name,
            "total_items": 0,
            "exact_matches": 0,
            "accuracy": 0.0,
            "mismatches": []
        }
        
        # Get common IDs between both datasets
        common_ids = set(self.predict_data.keys()) & set(self.real_data.keys())
        results["total_items"] = len(common_ids)
        
        if results["total_items"] == 0:
            return results
        
        exact_matches = 0
        
        for item_id in common_ids:
            predict_item = self.predict_data[item_id]
            real_item = self.real_data[item_id]
            
            if field_name:
                # Compare specific field
                predict_value = predict_item.get(field_name)
                real_value = real_item.get(field_name)
                
                if self._compare_values_with_normalization(predict_value, real_value, field_name):
                    exact_matches += 1
                else:
                    results["mismatches"].append({
                        "id": item_id,
                        "field": field_name,
                        "predicted": predict_value,
                        "real": real_value
                    })
            else:
                # Compare all fields
                all_fields = set(predict_item.keys()) | set(real_item.keys())
                mismatched_fields = []
                all_match = True
                
                for field in all_fields:
                    pred_val = predict_item.get(field)
                    real_val = real_item.get(field)
                    if not self._compare_values_with_normalization(pred_val, real_val, field):
                        all_match = False
                        mismatched_fields.append({
                            "field": field,
                            "predicted": pred_val,
                            "real": real_val
                        })
                
                if all_match:
                    exact_matches += 1
                else:
                    
                    results["mismatches"].append({
                        "id": item_id,
                        "mismatched_fields": mismatched_fields
                    })
        
        results["exact_matches"] = exact_matches
        results["accuracy"] = exact_matches / results["total_items"]
        
        return results
    
    def list_percentage_match_metric(self, field_name: str) -> Dict[str, Any]:
        """
        Compare list-type metadata using percentage of matching elements.
        
        Args:
            field_name: The field containing list data to compare
            
        Returns:
            Dictionary with comparison results including percentage matches
        """
        results = {
            "metric_type": "list_percentage_match",
            "field_name": field_name,
            "total_items": 0,
            "perfect_matches": 0,
            "average_percentage": 0.0,
            "details": []
        }
        
        # Get common IDs between both datasets
        common_ids = set(self.predict_data.keys()) & set(self.real_data.keys())
        results["total_items"] = len(common_ids)
        
        if results["total_items"] == 0:
            return results
        
        total_percentage = 0.0
        perfect_matches = 0
        
        for item_id in common_ids:
            predict_item = self.predict_data[item_id]
            real_item = self.real_data[item_id]
            
            # Get the field values and parse as lists
            predict_list = self._safe_parse_list(predict_item.get(field_name))
            real_list = self._safe_parse_list(real_item.get(field_name))
            
            # Calculate percentage match
            percentage = self._calculate_list_match_percentage(predict_list, real_list)
            total_percentage += percentage
            
            if percentage == 1.0:
                perfect_matches += 1
            
            results["details"].append({
                "id": item_id,
                "predicted_list": predict_list,
                "real_list": real_list,
                "match_percentage": percentage,
                "matching_elements": self._get_matching_elements(predict_list, real_list),
                "missing_elements": self._get_missing_elements(predict_list, real_list),
                "extra_elements": self._get_extra_elements(predict_list, real_list)
            })
        
        results["perfect_matches"] = perfect_matches
        results["average_percentage"] = total_percentage / results["total_items"]
        
        return results
    
    def _calculate_list_match_percentage(self, predict_list: List[str], real_list: List[str]) -> float:
        """Calculate the percentage of matching elements between two lists with normalization."""
        if not real_list and not predict_list:
            return 1.0  # Both empty lists are considered a perfect match
        if not real_list or not predict_list:
            return 0.0  # One empty, one not empty
        
        # Normalize all elements before comparison
        normalized_predict = set()
        for item in predict_list:
            normalized_predict.add(self._normalize_text(str(item)))
        
        normalized_real = set()
        for item in real_list:
            normalized_real.add(self._normalize_text(str(item)))
        
        # Calculate intersection
        intersection = normalized_predict & normalized_real
        union = normalized_predict | normalized_real
        
        # Return Jaccard similarity (intersection over union)
        return len(intersection) / len(union) if union else 1.0
    
    def _get_matching_elements(self, predict_list: List[str], real_list: List[str]) -> List[str]:
        """Get elements that are present in both lists (normalized comparison)."""
        # Create mapping from normalized to original values
        pred_norm_to_orig = {}
        for item in predict_list:
            norm = self._normalize_text(str(item))
            pred_norm_to_orig[norm] = item
        
        real_norm_to_orig = {}
        for item in real_list:
            norm = self._normalize_text(str(item))
            real_norm_to_orig[norm] = item
        
        # Find intersection and return original values
        matching_normalized = set(pred_norm_to_orig.keys()) & set(real_norm_to_orig.keys())
        return [real_norm_to_orig[norm] for norm in matching_normalized]
    
    def _get_missing_elements(self, predict_list: List[str], real_list: List[str]) -> List[str]:
        """Get elements that are in real_list but missing from predict_list (normalized comparison)."""
        pred_normalized = set(self._normalize_text(str(item)) for item in predict_list)
        
        missing = []
        for item in real_list:
            if self._normalize_text(str(item)) not in pred_normalized:
                missing.append(item)
        return missing
    
    def _get_extra_elements(self, predict_list: List[str], real_list: List[str]) -> List[str]:
        """Get elements that are in predict_list but not in real_list (normalized comparison)."""
        real_normalized = set(self._normalize_text(str(item)) for item in real_list)
        
        extra = []
        for item in predict_list:
            if self._normalize_text(str(item)) not in real_normalized:
                extra.append(item)
        return extra
    
    def generate_report(self, results: List[Dict[str, Any]], output_path: str = None) -> str:
        """
        Generate a comprehensive report from multiple metric results.
        
        Args:
            results: List of metric result dictionaries
            output_path: Optional path to save the report
            
        Returns:
            String containing the formatted report
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("METRIC COMPARISON REPORT")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        for result in results:
            metric_type = result.get("metric_type", "Unknown")
            field_name = result.get("field_name", "All fields")
            
            report_lines.append(f"Metric: {metric_type}")
            report_lines.append(f"Field: {field_name}")
            report_lines.append("-" * 40)
            
            if metric_type == "exact_equality":
                report_lines.append(f"Total items: {result['total_items']}")
                report_lines.append(f"Exact matches: {result['exact_matches']}")
                report_lines.append(f"Accuracy: {result['accuracy']:.2%}")
                report_lines.append(f"Mismatches: {len(result['mismatches'])}")
                
            elif metric_type == "list_percentage_match":
                report_lines.append(f"Total items: {result['total_items']}")
                report_lines.append(f"Perfect matches: {result['perfect_matches']}")
                report_lines.append(f"Average match percentage: {result['average_percentage']:.2%}")
                
                # Add some detailed examples
                if result['details']:
                    report_lines.append("\nSample comparisons:")
                    for i, detail in enumerate(result['details'][:3]):  # Show first 3 examples
                        report_lines.append(f"  Example {i+1} (ID: {detail['id']}):")
                        report_lines.append(f"    Match: {detail['match_percentage']:.2%}")
                        report_lines.append(f"    Matching: {detail['matching_elements']}")
                        if detail['missing_elements']:
                            report_lines.append(f"    Missing: {detail['missing_elements']}")
                        if detail['extra_elements']:
                            report_lines.append(f"    Extra: {detail['extra_elements']}")
            
            report_lines.append("")
        
        report = "\n".join(report_lines)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report


def main():
    """Example usage of the MetricChecker."""
    # This would be used when running the script directly
    pass


if __name__ == "__main__":
    main()