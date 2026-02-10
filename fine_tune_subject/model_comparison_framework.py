"""
Model Comparison Framework
Uses saved models to compare performance on same test data
Reuses training strategies for load/predict (no duplication)
"""
import numpy as np
import matplotlib.pyplot as plt
import time
from pathlib import Path

# Optional seaborn import for better confusion matrices
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from constants import SUBJECT_MODEL_RESULTS_FOLDER
from utils.colors.colors_terminal import Bcolors
from fine_tune_subject.utils.dataset.data_loader import load_csv_subjects, create_dataset
from fine_tune_subject.strategies.svm_strategy import SVMTrainingStrategy
from fine_tune_subject.strategies.xgboost_strategy import XGBoostTrainingStrategy
from fine_tune_subject.strategies.random_forest_strategy import RandomForestTrainingStrategy
from fine_tune_subject.strategies.embeddings_strategy import EmbeddingsTrainingStrategy
from fine_tune_subject.strategies.embeddings_knn_strategy import EmbeddingsKNNTrainingStrategy
from fine_tune_subject.strategies.neural_torch_strategy import NeuralTorchTrainingStrategy
from fine_tune_subject.strategies.minilm_strategy import MiniLMTrainingStrategy


class ModelResults:
    """Container for model results"""

    def __init__(self, model_name, accuracy, precision, recall, f1, predictions, confusion_matrix,
                 total_test_time, avg_prediction_time, load_time):
        self.model_name = model_name
        self.accuracy = accuracy
        self.precision = precision
        self.recall = recall
        self.f1 = f1
        self.predictions = predictions
        self.confusion_matrix = confusion_matrix
        self.total_test_time = total_test_time  # Total time to test all samples
        self.avg_prediction_time = avg_prediction_time  # Average time per sample (production metric)
        self.load_time = load_time  # Time to load the model

class ModelComparator:
    """Main class for comparing models"""

    def __init__(self):
        self.strategies = {
            'svm': SVMTrainingStrategy(kernel='linear'),
            'random_forest': RandomForestTrainingStrategy(),
            'xgboost': XGBoostTrainingStrategy(),
            'embeddings': EmbeddingsTrainingStrategy(),
            'embeddings_knn': EmbeddingsKNNTrainingStrategy(),
            'neural': NeuralTorchTrainingStrategy(),
            'minilm': MiniLMTrainingStrategy()
        }
        self.test_data = None
        self.results = {}

        # Create results folder structure
        SUBJECT_MODEL_RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)

        # Create individual model result folders
        for model_key in self.strategies.keys():
            model_result_folder = SUBJECT_MODEL_RESULTS_FOLDER / model_key
            model_result_folder.mkdir(parents=True, exist_ok=True)

    def load_test_data(self):
        """Load test data using EXACT same logic as training scripts"""
        print(f"{Bcolors.HEADER}=== Loading Test Data (Same Split as Training) ==={Bcolors.ENDC}")

        # Load subject mapping using shared utility
        subject_mapping = load_csv_subjects()

        # Create dataset using shared utility with EXACT same parameters
        documents, labels, document_ids = create_dataset(
            subject_mapping,
            min_frequency=5,
            max_per_subject=200,
            random_state=42
        )

        if len(documents) == 0:
            print(f"{Bcolors.FAIL}No documents found!{Bcolors.ENDC}")
            return False

        # EXACT same train_test_split as in training scripts
        X_train, X_test, y_train, y_test = train_test_split(
            documents, labels, test_size=0.2, random_state=42, stratify=labels
        )

        self.test_data = {
            'X_test': X_test,
            'y_test': y_test,
            'unique_labels': sorted(list(set(labels)))
        }

        print(f"{Bcolors.OKGREEN}Using EXACT same test split as training:{Bcolors.ENDC}")
        print(f"  Total dataset: {len(documents)} documents")
        print(f"  Training set: {len(X_train)} documents")
        print(f"  Test set: {len(X_test)} documents")
        print(f"  Classes: {len(set(labels))}")
        return True

    def test_model(self, model_key):
        """Test a specific model with timing"""
        strategy = self.strategies[model_key]

        print(f"\n{Bcolors.OKBLUE}Testing {strategy.get_model_name()}...{Bcolors.ENDC}")

        # Check if model files exist
        missing_files = []
        for file_path in strategy.get_model_files():
            p = Path(file_path)
            if not p.exists():
                missing_files.append(str(p))

        if missing_files:
            print(f"{Bcolors.WARNING}Missing files for {strategy.get_model_name()}: {missing_files}{Bcolors.ENDC}")
            return None

        # Time model loading
        load_start = time.time()
        if not strategy.load_model():
            print(f"{Bcolors.FAIL}Failed to load {strategy.get_model_name()}{Bcolors.ENDC}")
            return None
        load_time = time.time() - load_start

        # Make predictions with timing
        try:
            # Time total prediction
            prediction_start = time.time()
            predictions = strategy.predict(self.test_data['X_test'])
            total_test_time = time.time() - prediction_start

            # Calculate average time per sample (production metric)
            avg_prediction_time = total_test_time / len(self.test_data['X_test'])

            # Calculate metrics
            accuracy = accuracy_score(self.test_data['y_test'], predictions)

            # Get classification report
            report = classification_report(
                self.test_data['y_test'],
                predictions,
                output_dict=True,
                zero_division=0
            )

            # Extract macro averages
            macro_precision = report['macro avg']['precision']
            macro_recall = report['macro avg']['recall']
            macro_f1 = report['macro avg']['f1-score']

            # Create confusion matrix
            cm = confusion_matrix(self.test_data['y_test'], predictions)

            result = ModelResults(
                model_name=strategy.get_model_name(),
                accuracy=accuracy,
                precision=macro_precision,
                recall=macro_recall,
                f1=macro_f1,
                predictions=predictions,
                confusion_matrix=cm,
                total_test_time=total_test_time,
                avg_prediction_time=avg_prediction_time,
                load_time=load_time
            )

            print(f"{Bcolors.OKGREEN}{strategy.get_model_name()} - Accuracy: {accuracy:.4f}, F1: {macro_f1:.4f}{Bcolors.ENDC}")
            print(f"  Load time: {load_time:.3f}s, Total test time: {total_test_time:.3f}s, Avg per sample: {avg_prediction_time*1000:.2f}ms")

            return result

        except Exception as e:
            print(f"{Bcolors.FAIL}Error testing {strategy.get_model_name()}: {e}{Bcolors.ENDC}")
            return None

    def run_comparison(self, models_to_test):
        """Run comparison for specified models"""
        print(f"{Bcolors.HEADER}=== Model Comparison Framework ==={Bcolors.ENDC}")

        # Load test data
        if not self.load_test_data():
            return

        # Test each model
        self.results = {}
        for model_key in models_to_test:
            if model_key in self.strategies:
                result = self.test_model(model_key)
                if result:
                    self.results[model_key] = result
            else:
                print(f"{Bcolors.WARNING}Unknown model: {model_key}{Bcolors.ENDC}")

        if not self.results:
            print(f"{Bcolors.FAIL}No models could be tested!{Bcolors.ENDC}")
            return

        # Generate comparison
        self.generate_comparison_charts()
        self.generate_confusion_matrices()
        self.generate_subject_model_heatmap()
        self.print_comparison_table()

    def generate_comparison_charts(self):
        """Generate comparison charts including timing metrics"""
        print(f"\n{Bcolors.HEADER}=== Generating Comparison Charts ==={Bcolors.ENDC}")

        if len(self.results) < 2:
            print(f"{Bcolors.WARNING}Need at least 2 models for comparison{Bcolors.ENDC}")
            return

        # Prepare data for plotting
        models = list(self.results.keys())
        model_names = [self.results[key].model_name for key in models]
        accuracies = [self.results[key].accuracy for key in models]
        precisions = [self.results[key].precision for key in models]
        recalls = [self.results[key].recall for key in models]
        f1_scores = [self.results[key].f1 for key in models]
        load_times = [self.results[key].load_time for key in models]
        avg_pred_times_ms = [self.results[key].avg_prediction_time * 1000 for key in models]  # Convert to ms

        # Create comparison chart with 6 subplots (2x3)
        fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3, figsize=(18, 12))

        # Accuracy comparison
        bars1 = ax1.bar(model_names, accuracies, color='skyblue')
        ax1.set_title('Accuracy Comparison')
        ax1.set_ylabel('Accuracy')
        ax1.set_ylim(0, 1)
        for i, v in enumerate(accuracies):
            ax1.text(i, v + 0.01, f'{v:.3f}', ha='center')

        # Precision comparison
        bars2 = ax2.bar(model_names, precisions, color='lightgreen')
        ax2.set_title('Precision Comparison')
        ax2.set_ylabel('Precision')
        ax2.set_ylim(0, 1)
        for i, v in enumerate(precisions):
            ax2.text(i, v + 0.01, f'{v:.3f}', ha='center')

        # Recall comparison
        bars3 = ax3.bar(model_names, recalls, color='lightcoral')
        ax3.set_title('Recall Comparison')
        ax3.set_ylabel('Recall')
        ax3.set_ylim(0, 1)
        for i, v in enumerate(recalls):
            ax3.text(i, v + 0.01, f'{v:.3f}', ha='center')

        # F1-Score comparison
        bars4 = ax4.bar(model_names, f1_scores, color='gold')
        ax4.set_title('F1-Score Comparison')
        ax4.set_ylabel('F1-Score')
        ax4.set_ylim(0, 1)
        for i, v in enumerate(f1_scores):
            ax4.text(i, v + 0.01, f'{v:.3f}', ha='center')

        # Load time comparison
        bars5 = ax5.bar(model_names, load_times, color='orange')
        ax5.set_title('Model Load Time')
        ax5.set_ylabel('Load Time (seconds)')
        for i, v in enumerate(load_times):
            ax5.text(i, v + max(load_times)*0.01, f'{v:.2f}s', ha='center')

        # Average prediction time comparison (production metric)
        bars6 = ax6.bar(model_names, avg_pred_times_ms, color='purple')
        ax6.set_title('Avg Prediction Time (Production)')
        ax6.set_ylabel('Time per sample (ms)')
        for i, v in enumerate(avg_pred_times_ms):
            ax6.text(i, v + max(avg_pred_times_ms)*0.01, f'{v:.1f}ms', ha='center')

        # Rotate x-axis labels for better readability
        for ax in [ax1, ax2, ax3, ax4, ax5, ax6]:
            ax.tick_params(axis='x', rotation=45)

        plt.tight_layout()

        # Save in main model_results folder (not in subfolders)
        comparison_filename = f"models_comparison_detailed.png"
        comparison_filepath = SUBJECT_MODEL_RESULTS_FOLDER / comparison_filename

        plt.savefig(comparison_filepath, dpi=300, bbox_inches='tight')
        plt.close()  # Close instead of show to avoid blocking

        print(f"{Bcolors.OKGREEN}Detailed comparison chart saved as '{comparison_filepath}'{Bcolors.ENDC}")

        # Also create a summary performance chart
        self.generate_summary_performance_chart()

    def generate_confusion_matrices(self):
        """Generate individual confusion matrices for each model"""
        print(f"\n{Bcolors.HEADER}=== Generating Confusion Matrices ==={Bcolors.ENDC}")

        for model_key, result in self.results.items():
            print(f"Generating confusion matrix for {result.model_name}...")

            # Create model-specific subfolder
            model_result_folder = SUBJECT_MODEL_RESULTS_FOLDER / model_key
            model_result_folder.mkdir(parents=True, exist_ok=True)

            # Create larger figure for better readability
            plt.figure(figsize=(16, 14))

            # Normalize confusion matrix for better visualization
            cm_normalized = result.confusion_matrix.astype('float') / result.confusion_matrix.sum(axis=1)[:, np.newaxis]

            # Convert to percentage and cap at 99
            cm_percentage = np.round(cm_normalized * 100).astype(int)
            cm_percentage = np.clip(cm_percentage, 0, 99)

            # Create heatmap
            if HAS_SEABORN:
                # Better seaborn visualization with percentage format
                ax = sns.heatmap(cm_percentage,
                               annot=True,
                               fmt='d',
                               cmap='Blues',
                               xticklabels=self.test_data['unique_labels'],
                               yticklabels=self.test_data['unique_labels'],
                               cbar_kws={'label': 'Percentage (%)'},
                               square=True,
                               linewidths=0.5)

                # Improve text size
                ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=10)
                ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=10)

            else:
                # Fallback to matplotlib imshow if seaborn not available
                plt.imshow(cm_percentage, interpolation='nearest', cmap='Blues')
                plt.colorbar(label='Percentage (%)')
                tick_marks = np.arange(len(self.test_data['unique_labels']))
                plt.xticks(tick_marks, self.test_data['unique_labels'], rotation=45, ha='right', fontsize=10)
                plt.yticks(tick_marks, self.test_data['unique_labels'], fontsize=10)

                # Add text annotations with percentage format
                thresh = cm_percentage.max() / 2.
                for i in range(cm_percentage.shape[0]):
                    for j in range(cm_percentage.shape[1]):
                        plt.text(j, i, f'{cm_percentage[i, j]:02d}',
                                ha="center", va="center",
                                color="white" if cm_percentage[i, j] > thresh else "black")

            plt.title(f'Confusion Matrix - {result.model_name}\n'
                     f'Accuracy: {result.accuracy:.4f} | Precision: {result.precision:.4f} | '
                     f'Recall: {result.recall:.4f} | F1: {result.f1:.4f}',
                     fontsize=14, pad=20)
            plt.ylabel('True Label', fontsize=12)
            plt.xlabel('Predicted Label', fontsize=12)

            # Save in model-specific subfolder
            confusion_filename = f"confusion_matrix.png"
            confusion_filepath = model_result_folder / confusion_filename

            plt.tight_layout()
            plt.savefig(confusion_filepath, dpi=300, bbox_inches='tight')
            plt.close()  # Close instead of show to avoid blocking

            # Also save model-specific performance summary
            self.save_model_performance_summary(model_key, result, model_result_folder)

            print(f"{Bcolors.OKGREEN}Confusion matrix saved in '{model_result_folder}'{Bcolors.ENDC}")

    def save_model_performance_summary(self, model_key, result, model_folder):
        """Save individual model performance summary in its subfolder"""

        # Create individual model performance chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Performance metrics bar chart
        metrics = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
        values = [result.accuracy, result.precision, result.recall, result.f1]
        colors = ['skyblue', 'lightgreen', 'lightcoral', 'gold']

        bars = ax1.bar(metrics, values, color=colors)
        ax1.set_title(f'Performance Metrics - {result.model_name}', fontsize=14)
        ax1.set_ylabel('Score')
        ax1.set_ylim(0, 1)
        ax1.grid(True, alpha=0.3)

        # Add value labels on bars
        for bar, value in zip(bars, values):
            ax1.text(bar.get_x() + bar.get_width()/2, value + 0.01,
                    f'{value:.3f}', ha='center', va='bottom', fontweight='bold')

        # Timing information
        timing_labels = ['Load Time\n(seconds)', 'Avg Prediction\n(milliseconds)']
        timing_values = [result.load_time, result.avg_prediction_time * 1000]
        timing_colors = ['orange', 'purple']

        bars2 = ax2.bar(timing_labels, timing_values, color=timing_colors)
        ax2.set_title(f'Timing Performance - {result.model_name}', fontsize=14)
        ax2.set_ylabel('Time')
        ax2.grid(True, alpha=0.3)

        # Add value labels on timing bars
        for bar, value in zip(bars2, timing_values):
            unit = 's' if bar.get_x() < 0.5 else 'ms'
            ax2.text(bar.get_x() + bar.get_width()/2, value + max(timing_values)*0.01,
                    f'{value:.2f}{unit}', ha='center', va='bottom', fontweight='bold')

        plt.tight_layout()

        # Save in model subfolder
        summary_chart_path = model_folder / "performance_summary.png"
        plt.savefig(summary_chart_path, dpi=300, bbox_inches='tight')
        plt.close()  # Don't show individual charts, only the main comparison

        # Save performance data as text file
        performance_text_path = model_folder / "performance_metrics.txt"
        with open(performance_text_path, 'w') as f:
            f.write(f"Model Performance Summary: {result.model_name}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Accuracy:          {result.accuracy:.4f}\n")
            f.write(f"Precision (macro): {result.precision:.4f}\n")
            f.write(f"Recall (macro):    {result.recall:.4f}\n")
            f.write(f"F1-Score (macro):  {result.f1:.4f}\n\n")
            f.write("Timing Performance:\n")
            f.write(f"Load Time:         {result.load_time:.3f} seconds\n")
            f.write(f"Total Test Time:   {result.total_test_time:.3f} seconds\n")
            f.write(f"Avg Pred Time:     {result.avg_prediction_time*1000:.2f} milliseconds/sample\n\n")
            f.write(f"Test Samples:      {len(result.predictions)}\n")

        print(f"  - Performance summary saved in '{model_folder}'")

    def generate_summary_performance_chart(self):
        """Generate a single summary chart with all metrics"""
        print(f"\n{Bcolors.HEADER}=== Generating Summary Performance Chart ==={Bcolors.ENDC}")

        # Prepare data
        models = list(self.results.keys())
        model_names = [self.results[key].model_name for key in models]

        # Metrics data
        metrics = {
            'Accuracy': [self.results[key].accuracy for key in models],
            'Precision': [self.results[key].precision for key in models],
            'Recall': [self.results[key].recall for key in models],
            'F1-Score': [self.results[key].f1 for key in models]
        }

        # Create grouped bar chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))

        # Performance metrics grouped bar chart
        x = np.arange(len(model_names))
        width = 0.2

        colors = ['skyblue', 'lightgreen', 'lightcoral', 'gold']

        for i, (metric, values) in enumerate(metrics.items()):
            ax1.bar(x + i * width, values, width, label=metric, color=colors[i])

            # Add value labels on bars
            for j, v in enumerate(values):
                ax1.text(x[j] + i * width, v + 0.01, f'{v:.3f}',
                        ha='center', va='bottom', fontsize=8)

        ax1.set_xlabel('Models')
        ax1.set_ylabel('Score')
        ax1.set_title('Model Performance Comparison (All Metrics)')
        ax1.set_xticks(x + width * 1.5)
        ax1.set_xticklabels(model_names, rotation=45, ha='right')
        ax1.legend()
        ax1.set_ylim(0, 1.1)
        ax1.grid(True, alpha=0.3)

        # Timing comparison
        load_times = [self.results[key].load_time for key in models]
        pred_times_ms = [self.results[key].avg_prediction_time * 1000 for key in models]

        x2 = np.arange(len(model_names))

        # Use secondary y-axis for different scales
        ax2_twin = ax2.twinx()

        bars1 = ax2.bar(x2 - 0.2, load_times, 0.4, label='Load Time (s)', color='orange', alpha=0.7)
        bars2 = ax2_twin.bar(x2 + 0.2, pred_times_ms, 0.4, label='Prediction Time (ms)', color='purple', alpha=0.7)

        # Add value labels
        for i, v in enumerate(load_times):
            ax2.text(i - 0.2, v + max(load_times)*0.01, f'{v:.2f}s', ha='center', va='bottom', fontsize=8)

        for i, v in enumerate(pred_times_ms):
            ax2_twin.text(i + 0.2, v + max(pred_times_ms)*0.01, f'{v:.1f}ms', ha='center', va='bottom', fontsize=8)

        ax2.set_xlabel('Models')
        ax2.set_ylabel('Load Time (seconds)', color='orange')
        ax2_twin.set_ylabel('Prediction Time (ms)', color='purple')
        ax2.set_title('Model Timing Comparison')
        ax2.set_xticks(x2)
        ax2.set_xticklabels(model_names, rotation=45, ha='right')

        # Add legends
        ax2.legend(loc='upper left')
        ax2_twin.legend(loc='upper right')

        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save summary chart in main model_results folder
        summary_filename = f"models_summary_comparison.png"
        summary_filepath = SUBJECT_MODEL_RESULTS_FOLDER / summary_filename

        plt.savefig(summary_filepath, dpi=300, bbox_inches='tight')
        plt.close()  # Close instead of show to avoid blocking

        print(f"{Bcolors.OKGREEN}Summary performance chart saved as '{summary_filepath}'{Bcolors.ENDC}")

    def generate_subject_model_heatmap(self):
        """Generate heatmap showing per-subject accuracy for each model"""
        print(f"\n{Bcolors.HEADER}=== Generating Subject-Model Performance Heatmap ==={Bcolors.ENDC}")

        if len(self.results) < 1:
            print(f"{Bcolors.WARNING}No models to compare{Bcolors.ENDC}")
            return

        # Get unique subjects from test data
        unique_subjects = self.test_data['unique_labels']
        model_keys = list(self.results.keys())
        model_names = [self.results[key].model_name for key in model_keys]

        # Calculate per-subject accuracy for each model
        subject_accuracies = np.zeros((len(unique_subjects), len(model_keys)))

        for model_idx, model_key in enumerate(model_keys):
            result = self.results[model_key]
            y_true = self.test_data['y_test']
            y_pred = result.predictions

            # Calculate accuracy for each subject
            for subject_idx, subject in enumerate(unique_subjects):
                # Get indices where true label is this subject
                subject_mask = np.array(y_true) == subject
                if np.sum(subject_mask) > 0:  # Ensure there are samples for this subject
                    subject_true = np.array(y_true)[subject_mask]
                    subject_pred = np.array(y_pred)[subject_mask]
                    # Calculate accuracy for this subject
                    accuracy = np.mean(subject_true == subject_pred)
                    subject_accuracies[subject_idx, model_idx] = accuracy * 100  # Convert to percentage

        # Convert to integer percentages and cap at 99
        subject_accuracies_int = np.round(subject_accuracies).astype(int)
        subject_accuracies_int = np.clip(subject_accuracies_int, 0, 99)

        # Create the heatmap
        plt.figure(figsize=(max(12, len(model_keys) * 2), max(8, len(unique_subjects) * 0.5)))

        if HAS_SEABORN:
            # Use seaborn for better visualization
            ax = sns.heatmap(subject_accuracies_int,
                           annot=True,
                           fmt='d',
                           cmap='RdYlGn',  # Red-Yellow-Green colormap for better performance visualization
                           xticklabels=model_names,
                           yticklabels=unique_subjects,
                           cbar_kws={'label': 'Accuracy (%)'},
                           square=False,
                           linewidths=0.5)

            # Improve label formatting
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=10)
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=9)
        else:
            # Fallback to matplotlib
            plt.imshow(subject_accuracies_int, cmap='RdYlGn', aspect='auto')
            plt.colorbar(label='Accuracy (%)')

            # Set ticks and labels
            plt.xticks(range(len(model_names)), model_names, rotation=45, ha='right', fontsize=10)
            plt.yticks(range(len(unique_subjects)), unique_subjects, fontsize=9)

            # Add text annotations
            for i in range(len(unique_subjects)):
                for j in range(len(model_keys)):
                    value = subject_accuracies_int[i, j]
                    color = 'white' if value < 50 else 'black'  # Choose text color based on background
                    plt.text(j, i, f'{value:02d}', ha='center', va='center', color=color, fontweight='bold')

        plt.title('Per-Subject Accuracy by Model\n(Rows: Subjects, Columns: Models)', fontsize=14, pad=20)
        plt.xlabel('Models', fontsize=12)
        plt.ylabel('Subjects', fontsize=12)
        plt.tight_layout()

        # Save the heatmap
        heatmap_filename = "subject_model_accuracy_heatmap.png"
        heatmap_filepath = SUBJECT_MODEL_RESULTS_FOLDER / heatmap_filename
        plt.savefig(heatmap_filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"{Bcolors.OKGREEN}Subject-Model accuracy heatmap saved as '{heatmap_filepath}'{Bcolors.ENDC}")

        # Also save a summary text file with the data
        summary_text_path = SUBJECT_MODEL_RESULTS_FOLDER / "subject_model_accuracy_summary.txt"
        with open(summary_text_path, 'w') as f:
            f.write("Subject-Model Accuracy Matrix\n")
            f.write("=" * 50 + "\n\n")
            f.write("Format: Accuracy percentage for each subject (rows) by model (columns)\n\n")

            # Write header
            f.write(f"{'Subject':<30}")
            for model_name in model_names:
                f.write(f"{model_name:<15}")
            f.write("\n")
            f.write("-" * (30 + len(model_names) * 15) + "\n")

            # Write data
            for i, subject in enumerate(unique_subjects):
                f.write(f"{subject:<30}")
                for j in range(len(model_keys)):
                    f.write(f"{subject_accuracies_int[i, j]:>13}% ")
                f.write("\n")

            # Write summary statistics
            f.write("\n" + "=" * 50 + "\n")
            f.write("Summary Statistics:\n")
            f.write("-" * 20 + "\n")

            for j, model_name in enumerate(model_names):
                avg_accuracy = np.mean(subject_accuracies_int[:, j])
                f.write(f"{model_name:<20}: {avg_accuracy:.1f}% average\n")

        print(f"{Bcolors.OKGREEN}Subject-Model accuracy summary saved as '{summary_text_path}'{Bcolors.ENDC}")

    def print_comparison_table(self):
        """Print comprehensive comparison table with timing"""
        print(f"\n{Bcolors.HEADER}=== Model Comparison Table ==={Bcolors.ENDC}")

        print(f"{'Model':<20} {'Accuracy':<10} {'Precision':<10} {'Recall':<10} {'F1-Score':<10} {'Load(s)':<8} {'Pred(ms)':<10}")
        print("-" * 88)

        # Sort by F1-score
        sorted_results = sorted(self.results.items(),
                              key=lambda x: x[1].f1, reverse=True)

        for model_key, result in sorted_results:
            pred_time_ms = result.avg_prediction_time * 1000
            print(f"{result.model_name:<20} {result.accuracy:<10.4f} {result.precision:<10.4f} {result.recall:<10.4f} {result.f1:<10.4f} {result.load_time:<8.2f} {pred_time_ms:<10.1f}")

        # Print timing analysis
        print(f"\n{Bcolors.HEADER}=== Production Performance Analysis ==={Bcolors.ENDC}")

        fastest_load = min(self.results.values(), key=lambda x: x.load_time)
        fastest_pred = min(self.results.values(), key=lambda x: x.avg_prediction_time)
        best_accuracy = max(self.results.values(), key=lambda x: x.f1)

        print(f"{Bcolors.OKGREEN}Fastest to load: {fastest_load.model_name} ({fastest_load.load_time:.2f}s){Bcolors.ENDC}")
        print(f"{Bcolors.OKGREEN}Fastest prediction: {fastest_pred.model_name} ({fastest_pred.avg_prediction_time*1000:.1f}ms per sample){Bcolors.ENDC}")
        print(f"{Bcolors.OKGREEN}Best accuracy: {best_accuracy.model_name} (F1: {best_accuracy.f1:.4f}){Bcolors.ENDC}")

        # Performance recommendations
        print(f"\n{Bcolors.HEADER}=== Production Recommendations ==={Bcolors.ENDC}")

        # Find best balance of speed vs accuracy
        for model_key, result in sorted_results:
            pred_time_ms = result.avg_prediction_time * 1000

            if pred_time_ms < 10:  # Very fast
                speed_category = "Very Fast"
            elif pred_time_ms < 50:  # Fast
                speed_category = "Fast"
            elif pred_time_ms < 200:  # Medium
                speed_category = "Medium"
            else:  # Slow
                speed_category = "Slow"

            if result.f1 > 0.85:
                accuracy_category = "Excellent"
            elif result.f1 > 0.80:
                accuracy_category = "Good"
            elif result.f1 > 0.75:
                accuracy_category = "Fair"
            else:
                accuracy_category = "Poor"

            print(f"  {result.model_name:<20} {accuracy_category:<12} {speed_category}")

        # Overall recommendation
        print(f"\n{Bcolors.OKBLUE}Recommendation:{Bcolors.ENDC}")
        if fastest_pred.model_name == best_accuracy.model_name:
            print(f"   {best_accuracy.model_name} is both fastest and most accurate!")
        else:
            fast_pred_ms = fastest_pred.avg_prediction_time * 1000
            best_pred_ms = best_accuracy.avg_prediction_time * 1000

            if abs(best_accuracy.f1 - fastest_pred.f1) < 0.02:  # Very close accuracy
                print(f"   Use {fastest_pred.model_name} - similar accuracy but {fast_pred_ms:.1f}ms vs {best_pred_ms:.1f}ms")
            elif best_pred_ms < 100:  # Best model is still fast enough
                print(f"   Use {best_accuracy.model_name} - best accuracy and acceptable speed ({best_pred_ms:.1f}ms)")
            else:
                print(f"   Trade-off: {fastest_pred.model_name} for speed ({fast_pred_ms:.1f}ms) vs {best_accuracy.model_name} for accuracy (F1: {best_accuracy.f1:.3f})")

def main():
    """Main function with user input"""
    print(f"{Bcolors.HEADER}=== Model Comparison Tool ==={Bcolors.ENDC}")

    comparator = ModelComparator()

    # Available models
    available_models = {
        'svm': 'SVM (Linear)',
        'random_forest': 'Random Forest',
        'xgboost': 'XGBoost',
        'embeddings': 'Embeddings + Centroid',
        'embeddings_knn': 'Embeddings + KNN',
        'neural': 'Neural Network (PyTorch)',
        'minilm': 'all-MiniLM-L6-v2 (SVM)'
    }

    print(f"\nAvailable models:")
    for key, name in available_models.items():
        print(f"  {key}: {name}")

    print(f"\nEnter models to compare (comma-separated), or 'all' for all models:")
    print(f"Example: svm,xgboost")

    user_input = input("Models to test: ").strip().lower()

    if user_input == 'all':
        models_to_test = list(available_models.keys())
    else:
        models_to_test = [model.strip() for model in user_input.split(',')]

    print(f"\nTesting models: {models_to_test}")

    # Run comparison
    comparator.run_comparison(models_to_test)

if __name__ == "__main__":
    main()
