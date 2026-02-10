"""
Example script to run metric comparisons between predicted and real JSON outputs.

This script demonstrates how to use the MetricChecker class to compare
different JSON files with various metrics.
"""

import os
import json
from pathlib import Path
from metric_checker import MetricChecker
from fastapi import File, UploadFile


# Fields common to all document types
COMMON_FIELDS = {
    'language', 'title', 'creator', 'rights', 'rightsurl',
    'date', 'originPlaceInfo', 'isRelatedWith', 'type', 'subject',
}

# Type-specific fields: only relevant for their corresponding type
TYPE_SPECIFIC_FIELDS = {
    'tesis': {'codirector', 'director', 'degree.grantor', 'degree.name'},
    'articulo': {'journalTitle', 'journalVolumeAndIssue', 'issn', 'event'},
    'libro': {'publisher', 'isbn', 'compiler'},
    'objeto de conferencia': {'event', 'issn'},
}


def _get_types_for_field(field_name):
    """Return the set of doc types (lowercase) for which a field is relevant, or None if common."""
    if field_name in COMMON_FIELDS:
        return None
    types = set()
    for doc_type, fields in TYPE_SPECIFIC_FIELDS.items():
        if field_name in fields:
            types.add(doc_type)
    return types if types else None


def _filter_data_by_types(data, common_ids, allowed_types, original_data):
    """Filter data to only include documents whose type (from original) is in allowed_types."""
    filtered = {}
    for item_id in common_ids:
        if item_id in original_data and isinstance(original_data[item_id], dict):
            doc_type = original_data[item_id].get('type', '')
            if doc_type and doc_type.lower() in allowed_types:
                filtered[item_id] = data[item_id]
    return filtered


def _get_checker_for_field(field_name, predicted_data, original_data, common_ids, default_checker):
    """Return the appropriate checker for a field: filtered by type if type-specific, or the default."""
    allowed_types = _get_types_for_field(field_name)
    if allowed_types is None:
        return default_checker
    filtered_predicted = _filter_data_by_types(predicted_data, common_ids, allowed_types, original_data)
    filtered_original = _filter_data_by_types(original_data, common_ids, allowed_types, original_data)
    if not filtered_predicted and not filtered_original:
        return None
    return MetricChecker(filtered_predicted, filtered_original)


def run_metric_comparison(original_content: bytes, predicted_content: bytes):
    """
    Run comprehensive metric comparison between predicted and real JSON content.

    Args:
        original_content: Original/ground truth JSON file content as bytes
        predicted_content: Predicted output JSON file content as bytes
    """

    # Parse JSON content
    try:
        original_data = json.loads(original_content.decode('utf-8'))
        predicted_data = json.loads(predicted_content.decode('utf-8'))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON content: {e}")

    common_ids = set(predicted_data.keys()) & set(original_data.keys())

    # Initialize MetricChecker with parsed data
    checker = MetricChecker(predicted_data, original_data)

    # List to store all results
    all_results = []

    # 1. Overall exact equality comparison
    overall_equality = checker.exact_equality_metric()
    all_results.append(overall_equality)

    # 2. Overall F1 Score
    overall_f1 = checker.f1_score_metric()
    all_results.append(overall_f1)

    # 3. Discover all metadata fields present in the data
    all_fields = checker.discover_all_fields()

    # 4. Field-specific exact equality and F1 comparisons for all discovered fields
    #    For type-specific fields, only evaluate documents of the relevant type
    for field in all_fields:
        try:
            field_checker = _get_checker_for_field(field, predicted_data, original_data, common_ids, checker)
            if field_checker is None:
                continue
            field_equality = field_checker.exact_equality_metric(field_name=field)
            all_results.append(field_equality)
            field_f1 = field_checker.f1_score_metric(field_name=field)
            all_results.append(field_f1)
        except Exception as e:
            continue

    # 5. List percentage matching for fields that might be lists
    commonly_list_fields = ['subject', 'keywords', 'creator', 'author', 'contributors', 'editors']

    for field in commonly_list_fields:
        if field in all_fields:
            try:
                field_checker = _get_checker_for_field(field, predicted_data, original_data, common_ids, checker)
                if field_checker is None:
                    continue
                list_percentage = field_checker.list_percentage_match_metric(field_name=field)
                all_results.append(list_percentage)
            except Exception as e:
                continue

    # 5. Create summary statistics
    summary = create_summary_statistics(all_results)
    
    # 6. Generate type-specific results
    type_specific_results = generate_type_specific_results(predicted_data, original_data)
    
    # Add General key with overall results
    general_results = {
        "type": "General",
        "total_documents": len(set(predicted_data.keys()) & set(original_data.keys())),
        "detailed_results": all_results,
        "summary": summary
    }
    
    # Combine general and type-specific results
    final_results = {"General": general_results}
    final_results.update(type_specific_results)
    
    return {
        "detailed_results": all_results,
        "summary": summary,
        "type_specific_results": final_results
    }


def generate_type_specific_results(predicted_data: dict, original_data: dict) -> dict:
    """
    Generate metrics grouped by metadata type.
    
    Args:
        predicted_data: Predicted output JSON data
        original_data: Original/ground truth JSON data
    
    Returns:
        Dictionary with metrics grouped by type
    """
    # Get all unique types from both datasets
    all_types = set()
    common_ids = set(predicted_data.keys()) & set(original_data.keys())
    
    # Normalize type to title case (e.g. "tesis" -> "Tesis", "objeto de conferencia" -> "Objeto De Conferencia")
    def normalize_type(t):
        if not t:
            return t
        return t[0].upper() + t[1:]

    # Extract all unique types (normalized)
    for item_id in common_ids:
        if 'type' in predicted_data[item_id]:
            all_types.add(normalize_type(predicted_data[item_id]['type']))
        if 'type' in original_data[item_id]:
            all_types.add(normalize_type(original_data[item_id]['type']))
    
    type_specific_results = {}
    
    for doc_type in all_types:
        # Filter data by type
        filtered_predicted = {}
        filtered_original = {}
        
        for item_id in common_ids:
            pred_item = predicted_data[item_id]
            orig_item = original_data[item_id]
            
            # Include item if either predicted or original has this type (case-insensitive)
            if (normalize_type(pred_item.get('type', '')) == doc_type or normalize_type(orig_item.get('type', '')) == doc_type):
                filtered_predicted[item_id] = pred_item
                filtered_original[item_id] = orig_item
        
        if filtered_predicted and filtered_original:
            # Create checker for this type
            type_checker = MetricChecker(filtered_predicted, filtered_original)
            
            # Run metrics for this type
            type_results = []
            
            # Overall exact equality
            overall_equality = type_checker.exact_equality_metric()
            type_results.append(overall_equality)

            # Overall F1 Score
            overall_f1 = type_checker.f1_score_metric()
            type_results.append(overall_f1)

            # Discover all fields present in this type's data
            type_fields = type_checker.discover_all_fields()

            # Field-specific metrics for all discovered fields
            for field in type_fields:
                try:
                    field_equality = type_checker.exact_equality_metric(field_name=field)
                    type_results.append(field_equality)
                    field_f1 = type_checker.f1_score_metric(field_name=field)
                    type_results.append(field_f1)
                except Exception:
                    continue
            
            # List percentage matching for commonly list-type fields
            commonly_list_fields = ['subject', 'keywords', 'creator', 'author', 'contributors', 'editors']
            
            for field in commonly_list_fields:
                if field in type_fields:  # Only check if field exists in this type's data
                    try:
                        list_percentage = type_checker.list_percentage_match_metric(field_name=field)
                        type_results.append(list_percentage)
                    except Exception:
                        continue
            
            # Create summary for this type
            type_summary = create_summary_statistics(type_results)
            
            type_specific_results[doc_type] = {
                "type": doc_type,
                "total_documents": len(filtered_predicted),
                "detailed_results": type_results,
                "summary": type_summary
            }
    
    return type_specific_results


def create_summary_statistics(results: list) -> dict:
    """Create summary statistics from all metric results."""
    summary = {
        "total_metrics_run": len(results),
        "exact_equality_metrics": [],
        "f1_score_metrics": [],
        "list_percentage_metrics": [],
        "overall_performance": {}
    }

    exact_accuracies = []
    f1_scores = []
    list_percentages = []

    for result in results:
        if result["metric_type"] == "exact_equality":
            metric_summary = {
                "field": result["field_name"],
                "accuracy": result["accuracy"],
                "total_items": result["total_items"],
                "exact_matches": result["exact_matches"]
            }
            summary["exact_equality_metrics"].append(metric_summary)
            exact_accuracies.append(result["accuracy"])

        elif result["metric_type"] == "f1_score":
            metric_summary = {
                "field": result["field_name"],
                "f1_score": result["f1_score"],
                "precision": result["precision"],
                "recall": result["recall"],
                "total_items": result["total_items"],
            }
            summary["f1_score_metrics"].append(metric_summary)
            f1_scores.append(result["f1_score"])

        elif result["metric_type"] == "list_percentage_match":
            metric_summary = {
                "field": result["field_name"],
                "average_percentage": result["average_percentage"],
                "perfect_matches": result["perfect_matches"],
                "total_items": result["total_items"]
            }
            summary["list_percentage_metrics"].append(metric_summary)
            list_percentages.append(result["average_percentage"])

    # Calculate overall performance statistics
    if exact_accuracies:
        summary["overall_performance"]["average_exact_accuracy"] = sum(exact_accuracies) / len(exact_accuracies)
        summary["overall_performance"]["min_exact_accuracy"] = min(exact_accuracies)
        summary["overall_performance"]["max_exact_accuracy"] = max(exact_accuracies)

    if f1_scores:
        summary["overall_performance"]["average_f1_score"] = sum(f1_scores) / len(f1_scores)
        summary["overall_performance"]["min_f1_score"] = min(f1_scores)
        summary["overall_performance"]["max_f1_score"] = max(f1_scores)

    if list_percentages:
        summary["overall_performance"]["average_list_percentage"] = sum(list_percentages) / len(list_percentages)
        summary["overall_performance"]["min_list_percentage"] = min(list_percentages)
        summary["overall_performance"]["max_list_percentage"] = max(list_percentages)

    return summary


def main():
    """Main function to demonstrate metric comparison usage."""
    
    # Example paths - adjust these to your actual file paths
    # These should point to your predicted output and real/ground truth files
    
    # For demonstration, using the existing files in the validation folder
    validation_dir = Path(__file__).parent
    results_dir = validation_dir / "result"
    
    # Example usage with existing files
    real_json_path = results_dir / "original_metadata.json"
    
    # You would replace this with your predicted output file
    # For now, we'll use the same file to demonstrate (in real usage, these would be different)
    predict_json_path = results_dir / "extracted_metadata.json"  # This should be your predicted output file
    
    if real_json_path.exists():
        print("Running metric comparison with existing files...")
        print("Note: For demonstration, using the same file for both predicted and real.")
        print("In actual usage, you would provide different files for comparison.")
        print()
        
        try:
            results = run_metric_comparison(
                predict_json_path=str(predict_json_path),
                real_json_path=str(real_json_path),
                output_dir="metric_results"
            )
            
            print("\nMetric comparison completed successfully!")
            print(results)
            
        except Exception as e:
            print(f"Error running metric comparison: {e}")
    else:
        print(f"Ground truth file not found: {real_json_path}")
        print("Please ensure you have the required JSON files to compare.")
        print()
        print("Expected file structure:")
        print("  - predicted_output.json (your model's predictions)")
        print("  - real_output.json (ground truth data)")


if __name__ == "__main__":
    main()