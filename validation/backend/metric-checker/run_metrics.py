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
    
    # Initialize MetricChecker with parsed data
    checker = MetricChecker(predicted_data, original_data)
    
    # List to store all results
    all_results = []
    
    # 1. Overall exact equality comparison
    overall_equality = checker.exact_equality_metric()
    all_results.append(overall_equality)
    
    # 2. Field-specific exact equality comparisons for important metadata fields
    important_fields = ['title', 'abstract', 'creator', 'keywords', 'subject', 'language', 'date']
    
    for field in important_fields:
        try:
            field_equality = checker.exact_equality_metric(field_name=field)
            all_results.append(field_equality)
        except Exception as e:
            # Skip fields that don't exist or cause errors
            continue
    
    # 3. List percentage matching for fields that might be lists
    list_fields = ['subject', 'keywords']  # These are commonly list-type fields
    
    for field in list_fields:
        try:
            list_percentage = checker.list_percentage_match_metric(field_name=field)
            all_results.append(list_percentage)
        except Exception as e:
            # Skip fields that don't exist or cause errors
            continue
    
    # 4. Create summary statistics
    summary = create_summary_statistics(all_results)
    
    return {
        "detailed_results": all_results,
        "summary": summary
    }


def create_summary_statistics(results: list) -> dict:
    """Create summary statistics from all metric results."""
    summary = {
        "total_metrics_run": len(results),
        "exact_equality_metrics": [],
        "list_percentage_metrics": [],
        "overall_performance": {}
    }
    
    exact_accuracies = []
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