"""
Shared Model Comparison Framework.
Uses saved models to compare performance on same test data.
Parameterized to work across different classification tasks.
"""
import numpy as np
import matplotlib.pyplot as plt
import time
from pathlib import Path

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from utils.colors.colors_terminal import Bcolors


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
        self.total_test_time = total_test_time
        self.avg_prediction_time = avg_prediction_time
        self.load_time = load_time


class ModelComparator:
    """Main class for comparing models - parameterized for any classification task"""

    def __init__(self, strategies, results_folder, load_data_fn):
        """
        Args:
            strategies: dict of {key: strategy_instance}
            results_folder: Path for saving charts
            load_data_fn: callable that returns (documents, labels, doc_ids)
        """
        self.strategies = strategies
        self.results_folder = Path(results_folder)
        self.load_data_fn = load_data_fn
        self.test_data = None
        self.results = {}

        self.results_folder.mkdir(parents=True, exist_ok=True)
        for model_key in self.strategies.keys():
            model_result_folder = self.results_folder / model_key
            model_result_folder.mkdir(parents=True, exist_ok=True)

    def load_test_data(self):
        """Load test data using the provided load_data_fn"""
        print(f"{Bcolors.HEADER}=== Loading Test Data (Same Split as Training) ==={Bcolors.ENDC}")

        documents, labels, document_ids = self.load_data_fn()

        if len(documents) == 0:
            print(f"{Bcolors.FAIL}No documents found!{Bcolors.ENDC}")
            return False

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

        missing_files = []
        for file_path in strategy.get_model_files():
            p = Path(file_path)
            if not p.exists():
                missing_files.append(str(p))

        if missing_files:
            print(f"{Bcolors.WARNING}Missing files for {strategy.get_model_name()}: {missing_files}{Bcolors.ENDC}")
            return None

        load_start = time.time()
        if not strategy.load_model():
            print(f"{Bcolors.FAIL}Failed to load {strategy.get_model_name()}{Bcolors.ENDC}")
            return None
        load_time = time.time() - load_start

        try:
            prediction_start = time.time()
            predictions = strategy.predict(self.test_data['X_test'])
            total_test_time = time.time() - prediction_start

            avg_prediction_time = total_test_time / len(self.test_data['X_test'])

            acc = accuracy_score(self.test_data['y_test'], predictions)

            report = classification_report(
                self.test_data['y_test'],
                predictions,
                output_dict=True,
                zero_division=0
            )

            macro_precision = report['macro avg']['precision']
            macro_recall = report['macro avg']['recall']
            macro_f1 = report['macro avg']['f1-score']

            cm = confusion_matrix(self.test_data['y_test'], predictions)

            result = ModelResults(
                model_name=strategy.get_model_name(),
                accuracy=acc,
                precision=macro_precision,
                recall=macro_recall,
                f1=macro_f1,
                predictions=predictions,
                confusion_matrix=cm,
                total_test_time=total_test_time,
                avg_prediction_time=avg_prediction_time,
                load_time=load_time
            )

            print(f"{Bcolors.OKGREEN}{strategy.get_model_name()} - Accuracy: {acc:.4f}, F1: {macro_f1:.4f}{Bcolors.ENDC}")
            print(f"  Load time: {load_time:.3f}s, Total test time: {total_test_time:.3f}s, Avg per sample: {avg_prediction_time*1000:.2f}ms")

            return result

        except Exception as e:
            print(f"{Bcolors.FAIL}Error testing {strategy.get_model_name()}: {e}{Bcolors.ENDC}")
            return None

    def run_comparison(self, models_to_test):
        """Run comparison for specified models"""
        print(f"{Bcolors.HEADER}=== Model Comparison Framework ==={Bcolors.ENDC}")

        if not self.load_test_data():
            return

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

        self.generate_comparison_charts()
        self.generate_confusion_matrices()
        self.generate_label_model_heatmap()
        self.print_comparison_table()

    def generate_comparison_charts(self):
        """Generate comparison charts including timing metrics"""
        print(f"\n{Bcolors.HEADER}=== Generating Comparison Charts ==={Bcolors.ENDC}")

        if len(self.results) < 2:
            print(f"{Bcolors.WARNING}Need at least 2 models for comparison{Bcolors.ENDC}")
            return

        models = list(self.results.keys())
        model_names = [self.results[key].model_name for key in models]
        accuracies = [self.results[key].accuracy for key in models]
        precisions = [self.results[key].precision for key in models]
        recalls = [self.results[key].recall for key in models]
        f1_scores = [self.results[key].f1 for key in models]
        load_times = [self.results[key].load_time for key in models]
        avg_pred_times_ms = [self.results[key].avg_prediction_time * 1000 for key in models]

        fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3, figsize=(18, 12))

        bars1 = ax1.bar(model_names, accuracies, color='skyblue')
        ax1.set_title('Accuracy Comparison')
        ax1.set_ylabel('Accuracy')
        ax1.set_ylim(0, 1)
        for i, v in enumerate(accuracies):
            ax1.text(i, v + 0.01, f'{v:.3f}', ha='center')

        bars2 = ax2.bar(model_names, precisions, color='lightgreen')
        ax2.set_title('Precision Comparison')
        ax2.set_ylabel('Precision')
        ax2.set_ylim(0, 1)
        for i, v in enumerate(precisions):
            ax2.text(i, v + 0.01, f'{v:.3f}', ha='center')

        bars3 = ax3.bar(model_names, recalls, color='lightcoral')
        ax3.set_title('Recall Comparison')
        ax3.set_ylabel('Recall')
        ax3.set_ylim(0, 1)
        for i, v in enumerate(recalls):
            ax3.text(i, v + 0.01, f'{v:.3f}', ha='center')

        bars4 = ax4.bar(model_names, f1_scores, color='gold')
        ax4.set_title('F1-Score Comparison')
        ax4.set_ylabel('F1-Score')
        ax4.set_ylim(0, 1)
        for i, v in enumerate(f1_scores):
            ax4.text(i, v + 0.01, f'{v:.3f}', ha='center')

        bars5 = ax5.bar(model_names, load_times, color='orange')
        ax5.set_title('Model Load Time')
        ax5.set_ylabel('Load Time (seconds)')
        for i, v in enumerate(load_times):
            ax5.text(i, v + max(load_times)*0.01, f'{v:.2f}s', ha='center')

        bars6 = ax6.bar(model_names, avg_pred_times_ms, color='purple')
        ax6.set_title('Avg Prediction Time (Production)')
        ax6.set_ylabel('Time per sample (ms)')
        for i, v in enumerate(avg_pred_times_ms):
            ax6.text(i, v + max(avg_pred_times_ms)*0.01, f'{v:.1f}ms', ha='center')

        for ax in [ax1, ax2, ax3, ax4, ax5, ax6]:
            ax.tick_params(axis='x', rotation=45)

        plt.tight_layout()

        comparison_filepath = self.results_folder / "models_comparison_detailed.png"
        plt.savefig(comparison_filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"{Bcolors.OKGREEN}Detailed comparison chart saved as '{comparison_filepath}'{Bcolors.ENDC}")

        self._generate_summary_performance_chart()

    def generate_confusion_matrices(self):
        """Generate individual confusion matrices for each model"""
        print(f"\n{Bcolors.HEADER}=== Generating Confusion Matrices ==={Bcolors.ENDC}")

        for model_key, result in self.results.items():
            print(f"Generating confusion matrix for {result.model_name}...")

            model_result_folder = self.results_folder / model_key
            model_result_folder.mkdir(parents=True, exist_ok=True)

            plt.figure(figsize=(16, 14))

            cm_normalized = result.confusion_matrix.astype('float') / result.confusion_matrix.sum(axis=1)[:, np.newaxis]
            cm_percentage = np.round(cm_normalized * 100).astype(int)
            cm_percentage = np.clip(cm_percentage, 0, 99)

            if HAS_SEABORN:
                ax = sns.heatmap(cm_percentage,
                               annot=True, fmt='d', cmap='Blues',
                               xticklabels=self.test_data['unique_labels'],
                               yticklabels=self.test_data['unique_labels'],
                               cbar_kws={'label': 'Percentage (%)'},
                               square=True, linewidths=0.5)
                ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=10)
                ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=10)
            else:
                plt.imshow(cm_percentage, interpolation='nearest', cmap='Blues')
                plt.colorbar(label='Percentage (%)')
                tick_marks = np.arange(len(self.test_data['unique_labels']))
                plt.xticks(tick_marks, self.test_data['unique_labels'], rotation=45, ha='right', fontsize=10)
                plt.yticks(tick_marks, self.test_data['unique_labels'], fontsize=10)
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

            confusion_filepath = model_result_folder / "confusion_matrix.png"
            plt.tight_layout()
            plt.savefig(confusion_filepath, dpi=300, bbox_inches='tight')
            plt.close()

            self._save_model_performance_summary(model_key, result, model_result_folder)

            print(f"{Bcolors.OKGREEN}Confusion matrix saved in '{model_result_folder}'{Bcolors.ENDC}")

    def _save_model_performance_summary(self, model_key, result, model_folder):
        """Save individual model performance summary in its subfolder"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        metrics = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
        values = [result.accuracy, result.precision, result.recall, result.f1]
        colors = ['skyblue', 'lightgreen', 'lightcoral', 'gold']

        bars = ax1.bar(metrics, values, color=colors)
        ax1.set_title(f'Performance Metrics - {result.model_name}', fontsize=14)
        ax1.set_ylabel('Score')
        ax1.set_ylim(0, 1)
        ax1.grid(True, alpha=0.3)

        for bar, value in zip(bars, values):
            ax1.text(bar.get_x() + bar.get_width()/2, value + 0.01,
                    f'{value:.3f}', ha='center', va='bottom', fontweight='bold')

        timing_labels = ['Load Time\n(seconds)', 'Avg Prediction\n(milliseconds)']
        timing_values = [result.load_time, result.avg_prediction_time * 1000]
        timing_colors = ['orange', 'purple']

        bars2 = ax2.bar(timing_labels, timing_values, color=timing_colors)
        ax2.set_title(f'Timing Performance - {result.model_name}', fontsize=14)
        ax2.set_ylabel('Time')
        ax2.grid(True, alpha=0.3)

        for bar, value in zip(bars2, timing_values):
            unit = 's' if bar.get_x() < 0.5 else 'ms'
            ax2.text(bar.get_x() + bar.get_width()/2, value + max(timing_values)*0.01,
                    f'{value:.2f}{unit}', ha='center', va='bottom', fontweight='bold')

        plt.tight_layout()

        summary_chart_path = model_folder / "performance_summary.png"
        plt.savefig(summary_chart_path, dpi=300, bbox_inches='tight')
        plt.close()

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

    def _generate_summary_performance_chart(self):
        """Generate a single summary chart with all metrics"""
        print(f"\n{Bcolors.HEADER}=== Generating Summary Performance Chart ==={Bcolors.ENDC}")

        models = list(self.results.keys())
        model_names = [self.results[key].model_name for key in models]

        metrics = {
            'Accuracy': [self.results[key].accuracy for key in models],
            'Precision': [self.results[key].precision for key in models],
            'Recall': [self.results[key].recall for key in models],
            'F1-Score': [self.results[key].f1 for key in models]
        }

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))

        x = np.arange(len(model_names))
        width = 0.2
        colors = ['skyblue', 'lightgreen', 'lightcoral', 'gold']

        for i, (metric, values) in enumerate(metrics.items()):
            ax1.bar(x + i * width, values, width, label=metric, color=colors[i])
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

        load_times = [self.results[key].load_time for key in models]
        pred_times_ms = [self.results[key].avg_prediction_time * 1000 for key in models]

        x2 = np.arange(len(model_names))
        ax2_twin = ax2.twinx()

        ax2.bar(x2 - 0.2, load_times, 0.4, label='Load Time (s)', color='orange', alpha=0.7)
        ax2_twin.bar(x2 + 0.2, pred_times_ms, 0.4, label='Prediction Time (ms)', color='purple', alpha=0.7)

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
        ax2.legend(loc='upper left')
        ax2_twin.legend(loc='upper right')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        summary_filepath = self.results_folder / "models_summary_comparison.png"
        plt.savefig(summary_filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"{Bcolors.OKGREEN}Summary performance chart saved as '{summary_filepath}'{Bcolors.ENDC}")

    def generate_label_model_heatmap(self):
        """Generate heatmap showing per-label accuracy for each model"""
        print(f"\n{Bcolors.HEADER}=== Generating Label-Model Performance Heatmap ==={Bcolors.ENDC}")

        if len(self.results) < 1:
            print(f"{Bcolors.WARNING}No models to compare{Bcolors.ENDC}")
            return

        unique_labels = self.test_data['unique_labels']
        model_keys = list(self.results.keys())
        model_names = [self.results[key].model_name for key in model_keys]

        label_accuracies = np.zeros((len(unique_labels), len(model_keys)))

        for model_idx, model_key in enumerate(model_keys):
            result = self.results[model_key]
            y_true = self.test_data['y_test']
            y_pred = result.predictions

            for label_idx, label in enumerate(unique_labels):
                label_mask = np.array(y_true) == label
                if np.sum(label_mask) > 0:
                    label_true = np.array(y_true)[label_mask]
                    label_pred = np.array(y_pred)[label_mask]
                    acc = np.mean(label_true == label_pred)
                    label_accuracies[label_idx, model_idx] = acc * 100

        label_accuracies_int = np.round(label_accuracies).astype(int)
        label_accuracies_int = np.clip(label_accuracies_int, 0, 99)

        plt.figure(figsize=(max(12, len(model_keys) * 2), max(8, len(unique_labels) * 0.5)))

        if HAS_SEABORN:
            ax = sns.heatmap(label_accuracies_int,
                           annot=True, fmt='d', cmap='RdYlGn',
                           xticklabels=model_names,
                           yticklabels=unique_labels,
                           cbar_kws={'label': 'Accuracy (%)'},
                           square=False, linewidths=0.5)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=10)
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=9)
        else:
            plt.imshow(label_accuracies_int, cmap='RdYlGn', aspect='auto')
            plt.colorbar(label='Accuracy (%)')
            plt.xticks(range(len(model_names)), model_names, rotation=45, ha='right', fontsize=10)
            plt.yticks(range(len(unique_labels)), unique_labels, fontsize=9)
            for i in range(len(unique_labels)):
                for j in range(len(model_keys)):
                    value = label_accuracies_int[i, j]
                    color = 'white' if value < 50 else 'black'
                    plt.text(j, i, f'{value:02d}', ha='center', va='center', color=color, fontweight='bold')

        plt.title('Per-Label Accuracy by Model\n(Rows: Labels, Columns: Models)', fontsize=14, pad=20)
        plt.xlabel('Models', fontsize=12)
        plt.ylabel('Labels', fontsize=12)
        plt.tight_layout()

        heatmap_filepath = self.results_folder / "label_model_accuracy_heatmap.png"
        plt.savefig(heatmap_filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"{Bcolors.OKGREEN}Label-Model accuracy heatmap saved as '{heatmap_filepath}'{Bcolors.ENDC}")

    def print_comparison_table(self):
        """Print comprehensive comparison table with timing"""
        print(f"\n{Bcolors.HEADER}=== Model Comparison Table ==={Bcolors.ENDC}")

        print(f"{'Model':<20} {'Accuracy':<10} {'Precision':<10} {'Recall':<10} {'F1-Score':<10} {'Load(s)':<8} {'Pred(ms)':<10}")
        print("-" * 88)

        sorted_results = sorted(self.results.items(),
                              key=lambda x: x[1].f1, reverse=True)

        for model_key, result in sorted_results:
            pred_time_ms = result.avg_prediction_time * 1000
            print(f"{result.model_name:<20} {result.accuracy:<10.4f} {result.precision:<10.4f} {result.recall:<10.4f} {result.f1:<10.4f} {result.load_time:<8.2f} {pred_time_ms:<10.1f}")

        print(f"\n{Bcolors.HEADER}=== Production Performance Analysis ==={Bcolors.ENDC}")

        fastest_load = min(self.results.values(), key=lambda x: x.load_time)
        fastest_pred = min(self.results.values(), key=lambda x: x.avg_prediction_time)
        best_accuracy = max(self.results.values(), key=lambda x: x.f1)

        print(f"{Bcolors.OKGREEN}Fastest to load: {fastest_load.model_name} ({fastest_load.load_time:.2f}s){Bcolors.ENDC}")
        print(f"{Bcolors.OKGREEN}Fastest prediction: {fastest_pred.model_name} ({fastest_pred.avg_prediction_time*1000:.1f}ms per sample){Bcolors.ENDC}")
        print(f"{Bcolors.OKGREEN}Best accuracy: {best_accuracy.model_name} (F1: {best_accuracy.f1:.4f}){Bcolors.ENDC}")
