"""
Metric Checker for JSON Comparison

This module provides functionality to compare predicted outputs with real outputs
from JSON files, specifically designed for metadata comparison with different metrics.
"""

import json
from typing import Dict, List, Any, Tuple, Union
from pathlib import Path
import ast


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
                
                if predict_value == real_value:
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
                if predict_item == real_item:
                    exact_matches += 1
                else:
                    # Find mismatched fields
                    mismatched_fields = []
                    all_fields = set(predict_item.keys()) | set(real_item.keys())
                    
                    for field in all_fields:
                        pred_val = predict_item.get(field)
                        real_val = real_item.get(field)
                        if pred_val != real_val:
                            mismatched_fields.append({
                                "field": field,
                                "predicted": pred_val,
                                "real": real_val
                            })
                    
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
        """Calculate the percentage of matching elements between two lists."""
        if not real_list and not predict_list:
            return 1.0  # Both empty lists are considered a perfect match
        if not real_list or not predict_list:
            return 0.0  # One empty, one not empty
        
        # Convert to sets for intersection calculation
        predict_set = set(predict_list)
        real_set = set(real_list)
        
        # Calculate intersection
        intersection = predict_set & real_set
        union = predict_set | real_set
        
        # Return Jaccard similarity (intersection over union)
        return len(intersection) / len(union) if union else 1.0
    
    def _get_matching_elements(self, predict_list: List[str], real_list: List[str]) -> List[str]:
        """Get elements that are present in both lists."""
        return list(set(predict_list) & set(real_list))
    
    def _get_missing_elements(self, predict_list: List[str], real_list: List[str]) -> List[str]:
        """Get elements that are in real_list but missing from predict_list."""
        return list(set(real_list) - set(predict_list))
    
    def _get_extra_elements(self, predict_list: List[str], real_list: List[str]) -> List[str]:
        """Get elements that are in predict_list but not in real_list."""
        return list(set(predict_list) - set(real_list))
    
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