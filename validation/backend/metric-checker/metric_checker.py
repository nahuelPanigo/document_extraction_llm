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
    
    def _normalize_name_parts(self, name: str) -> set:
        """
        Normalize a person's name by splitting into individual words.
        This handles cases where names are in different orders and formats.
        
        Args:
            name: Name to normalize
            
        Returns:
            Set of normalized name words (removes duplicates and order)
        """
        if not isinstance(name, str):
            if name is None:
                return set()
            name = str(name)
        
        # Split name by common separators (comma, space, semicolon, etc.)
        # Remove any punctuation and split by whitespace
        name_clean = re.sub(r'[,;.\-_()]+', ' ', name.strip())
        words = name_clean.split()
        
        # Normalize each word and filter out empty strings
        normalized_words = set()
        for word in words:
            word = word.strip()
            if word and len(word) > 1:  # Skip single characters and empty strings
                normalized_word = self._normalize_text(word)
                if normalized_word:  # Only add non-empty normalized words
                    normalized_words.add(normalized_word)
        
        return normalized_words
    
    def _compare_names(self, name1: Any, name2: Any) -> bool:
        """
        Compare two names by matching individual words regardless of order.
        Handles cases like "Andrea Soledad Orsatti" vs "Orsatti, Andrea Soledad".

        Args:
            name1: First name to compare
            name2: Second name to compare

        Returns:
            True if names contain the same words, False otherwise
        """
        if name1 is None and name2 is None:
            return True
        if (name1 is None and name2 == "") or (name2 is None and name1 == ""):
            return True
        if name1 is None or name2 is None:
            return False

        # Normalize both names into sets of words
        words1 = self._normalize_name_parts(name1)
        words2 = self._normalize_name_parts(name2)

        # Names match if they contain the same words (regardless of order)
        return words1 == words2
    
    def _compare_creator_values(self, creators1: Any, creators2: Any) -> bool:
        """
        Compare creator fields that can be strings or lists with word-by-word name matching.
        For collections, each name in one collection is compared against all names in the other.
        
        Args:
            creators1: First creator value (string, list, or None)
            creators2: Second creator value (string, list, or None)
            
        Returns:
            True if creator values match, False otherwise
        """
        # Convert both to lists of strings
        list1 = self._safe_parse_list(creators1)
        list2 = self._safe_parse_list(creators2)
        
        # If both empty, they match
        if len(list1) == 0 and len(list2) == 0:
            return True
        
        # If different number of creators, they don't match
        if len(list1) != len(list2):
            return False
        
        # For each name in list1, find a matching name in list2
        list2_copy = list2[:]  # Make a copy to track matched names
        
        for name1 in list1:
            found_match = False
            for i, name2 in enumerate(list2_copy):
                if self._compare_names(name1, name2):
                    found_match = True
                    # Remove matched name from copy to avoid double matching
                    list2_copy.pop(i)
                    break
            
            # If no match found for this name, collections don't match
            if not found_match:
                return False
        
        # All names in list1 found matches in list2
        return True
    
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
        # Normalize "null" string to None for comparison
        if val1 == "null":
            val1 = None
        if val2 == "null":
            val2 = None
            
        # Handle None values - treat None and empty string as equivalent
        if val1 is None and val2 is None:
            return True
        if (val1 is None and val2 == "") or (val2 is None and val1 == ""):
            return True
        if val1 is None or val2 is None:
            return False
        
        # Special handling for creator, director, codirector, author fields (names that can have order issues)
        if field_name and field_name.lower() in ['creator', 'director', 'codirector', 'author', 'contributors', 'editors']:
            return self._compare_creator_values(val1, val2)
        
        # For other fields, normalize both values and compare
        norm_val1 = self._normalize_value(val1)
        norm_val2 = self._normalize_value(val2)
        
        return norm_val1 == norm_val2
    
    def discover_all_fields(self) -> set:
        """
        Discover all unique metadata field names present in both datasets.
        This ensures we don't miss any fields that might be specific to certain document types.
        Excludes the 'type' field since it's used for grouping, not metadata comparison.
        
        Returns:
            Set of all unique field names found across all documents (excluding 'type')
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
        
        # Remove 'id' field as it's used for matching, not metadata comparison
        all_fields.discard('id')

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
            "null_count": 0,
            "null_both": 0,
            "null_false": 0,
            "mismatches": []
        }

        # Get common IDs between both datasets
        common_ids = set(self.predict_data.keys()) & set(self.real_data.keys())
        results["total_items"] = len(common_ids)

        if results["total_items"] == 0:
            return results

        exact_matches = 0
        null_count = 0
        null_both = 0
        null_false = 0

        for item_id in common_ids:
            predict_item = self.predict_data[item_id]
            real_item = self.real_data[item_id]

            if field_name:
                # Compare specific field
                predict_value = predict_item.get(field_name)
                real_value = real_item.get(field_name)

                pred_null = not self._is_value_present(predict_value)
                real_null = not self._is_value_present(real_value)

                if pred_null or real_null:
                    null_count += 1
                    if pred_null and real_null:
                        null_both += 1
                    else:
                        null_false += 1

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
                # Compare all fields (excluding 'id')
                all_fields = set(predict_item.keys()) | set(real_item.keys())
                all_fields.discard('id')  # Exclude 'id' from comparison (used for matching only)
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
        results["null_count"] = null_count
        results["null_both"] = null_both
        results["null_false"] = null_false

        return results
    
    def _is_value_present(self, value: Any) -> bool:
        """Check if a value is considered present (not null/empty)."""
        if value is None:
            return False
        if value == "null":
            return False
        if isinstance(value, str) and value.strip() == "":
            return False
        if isinstance(value, list) and len(value) == 0:
            return False
        return True

    def f1_score_metric(self, field_name: str = None) -> Dict[str, Any]:
        """
        Calculate F1 Score for metadata comparison.

        For a specific field:
          - TP: Model extracted a value AND it matches the real value
          - FN: Real has a value BUT model extracted nothing (null/empty)
          - FP: Model extracted something incorrect (wrong value OR hallucination when real is null)

        For all fields (field_name=None):
          - Aggregates TP/FP/FN across all fields for each document

        Args:
            field_name: Specific field to compare. If None, compares all fields.

        Returns:
            Dictionary with F1 score results
        """
        results = {
            "metric_type": "f1_score",
            "field_name": field_name,
            "total_items": 0,
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
        }

        common_ids = set(self.predict_data.keys()) & set(self.real_data.keys())
        results["total_items"] = len(common_ids)

        if results["total_items"] == 0:
            return results

        tp = 0
        fp = 0
        fn = 0

        for item_id in common_ids:
            predict_item = self.predict_data[item_id]
            real_item = self.real_data[item_id]

            if field_name:
                predict_value = predict_item.get(field_name)
                real_value = real_item.get(field_name)
                real_present = self._is_value_present(real_value)
                pred_present = self._is_value_present(predict_value)
                match = self._compare_values_with_normalization(predict_value, real_value, field_name)

                if real_present and pred_present and match:
                    # TP: Both have values and they match
                    tp += 1
                elif real_present and not pred_present:
                    # FN: Real has value but model extracted nothing
                    fn += 1
                elif pred_present and not match:
                    # FP: Model extracted something incorrect (wrong value or hallucination)
                    fp += 1
                # If both are null/empty, it's a True Negative (not counted in F1)
            else:
                all_fields = set(predict_item.keys()) | set(real_item.keys())
                all_fields.discard('id')
                for field in all_fields:
                    pred_val = predict_item.get(field)
                    real_val = real_item.get(field)
                    real_present = self._is_value_present(real_val)
                    pred_present = self._is_value_present(pred_val)
                    match = self._compare_values_with_normalization(pred_val, real_val, field)

                    if real_present and pred_present and match:
                        tp += 1
                    elif real_present and not pred_present:
                        fn += 1
                    elif pred_present and not match:
                        fp += 1

        results["true_positives"] = tp
        results["false_positives"] = fp
        results["false_negatives"] = fn

        # When TP+FP+FN=0, all cases are True Negatives (both null) - that's 100% correct
        if tp == 0 and fp == 0 and fn == 0:
            precision = 1.0
            recall = 1.0
            f1 = 1.0
        else:
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        results["precision"] = precision
        results["recall"] = recall
        results["f1_score"] = f1

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
            percentage = self._calculate_list_match_percentage(predict_list, real_list, field_name)
            total_percentage += percentage

            if percentage == 1.0:
                perfect_matches += 1

            results["details"].append({
                "id": item_id,
                "predicted_list": predict_list,
                "real_list": real_list,
                "match_percentage": percentage,
                "matching_elements": self._get_matching_elements(predict_list, real_list, field_name),
                "missing_elements": self._get_missing_elements(predict_list, real_list, field_name),
                "extra_elements": self._get_extra_elements(predict_list, real_list, field_name)
            })
        
        results["perfect_matches"] = perfect_matches
        results["average_percentage"] = total_percentage / results["total_items"]
        
        return results
    
    def _calculate_list_match_percentage(self, predict_list: List[str], real_list: List[str], field_name: str = None) -> float:
        """Calculate the percentage of matching elements between two lists with normalization."""
        if not real_list and not predict_list:
            return 1.0  # Both empty lists are considered a perfect match
        if not real_list or not predict_list:
            return 0.0  # One empty, one not empty

        # For name fields, use name-aware comparison
        is_name_field = field_name and field_name.lower() in ['creator', 'director', 'codirector', 'author', 'contributors', 'editors']

        if is_name_field:
            # Use name-aware matching (order-independent)
            matched_real = set()
            matched_predict = set()
            for i, pred_item in enumerate(predict_list):
                for j, real_item in enumerate(real_list):
                    if j not in matched_real and self._compare_names(pred_item, real_item):
                        matched_predict.add(i)
                        matched_real.add(j)
                        break
            # Jaccard: intersection / union
            intersection_count = len(matched_real)
            union_count = len(predict_list) + len(real_list) - intersection_count
            return intersection_count / union_count if union_count > 0 else 1.0
        else:
            # Standard text normalization for non-name fields
            normalized_predict = set()
            for item in predict_list:
                normalized_predict.add(self._normalize_text(str(item)))

            normalized_real = set()
            for item in real_list:
                normalized_real.add(self._normalize_text(str(item)))

            intersection = normalized_predict & normalized_real
            union = normalized_predict | normalized_real
            return len(intersection) / len(union) if union else 1.0
    
    def _get_matching_elements(self, predict_list: List[str], real_list: List[str], field_name: str = None) -> List[str]:
        """Get elements that are present in both lists (normalized comparison)."""
        is_name_field = field_name and field_name.lower() in ['creator', 'director', 'codirector', 'author', 'contributors', 'editors']

        if is_name_field:
            matching = []
            matched_real_indices = set()
            for pred_item in predict_list:
                for j, real_item in enumerate(real_list):
                    if j not in matched_real_indices and self._compare_names(pred_item, real_item):
                        matching.append(real_item)
                        matched_real_indices.add(j)
                        break
            return matching
        else:
            pred_norm_to_orig = {}
            for item in predict_list:
                norm = self._normalize_text(str(item))
                pred_norm_to_orig[norm] = item

            real_norm_to_orig = {}
            for item in real_list:
                norm = self._normalize_text(str(item))
                real_norm_to_orig[norm] = item

            matching_normalized = set(pred_norm_to_orig.keys()) & set(real_norm_to_orig.keys())
            return [real_norm_to_orig[norm] for norm in matching_normalized]

    def _get_missing_elements(self, predict_list: List[str], real_list: List[str], field_name: str = None) -> List[str]:
        """Get elements that are in real_list but missing from predict_list (normalized comparison)."""
        is_name_field = field_name and field_name.lower() in ['creator', 'director', 'codirector', 'author', 'contributors', 'editors']

        missing = []
        for real_item in real_list:
            found = False
            for pred_item in predict_list:
                if is_name_field:
                    if self._compare_names(pred_item, real_item):
                        found = True
                        break
                else:
                    if self._normalize_text(str(pred_item)) == self._normalize_text(str(real_item)):
                        found = True
                        break
            if not found:
                missing.append(real_item)
        return missing

    def _get_extra_elements(self, predict_list: List[str], real_list: List[str], field_name: str = None) -> List[str]:
        """Get elements that are in predict_list but not in real_list (normalized comparison)."""
        is_name_field = field_name and field_name.lower() in ['creator', 'director', 'codirector', 'author', 'contributors', 'editors']

        extra = []
        for pred_item in predict_list:
            found = False
            for real_item in real_list:
                if is_name_field:
                    if self._compare_names(pred_item, real_item):
                        found = True
                        break
                else:
                    if self._normalize_text(str(pred_item)) == self._normalize_text(str(real_item)):
                        found = True
                        break
            if not found:
                extra.append(pred_item)
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