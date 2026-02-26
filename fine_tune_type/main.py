#!/usr/bin/env python3
"""
Unified Type Classification - Backward compatible entry point.
Runs make_dataset (interactive) then train (interactive).

For direct usage, prefer:
    python -m fine_tune_type.make_dataset [--all|--types|--download|--extract]
    python -m fine_tune_type.train [model_name|all] [--compare]
"""
from fine_tune_type.make_dataset import ask_pipeline_steps, run_pipeline_steps
from fine_tune_type.train import interactive_mode
from fine_tune_type.test import interactive_mode as test_interactive_mode
from utils.colors.colors_terminal import Bcolors
import numpy as np


def main():
    """Main entry point: dataset pipeline then model training then optional PDF test"""
    np.random.seed(42)

    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}UNIFIED TYPE CLASSIFICATION TRAINING{Bcolors.ENDC}")
    print(f"{Bcolors.HEADER}{'='*60}{Bcolors.ENDC}")

    # STEP 1: Data pipeline
    pipeline_steps = ask_pipeline_steps()
    run_pipeline_steps(pipeline_steps)

    # STEP 2: Model training (interactive)
    interactive_mode()

    # STEP 3: Test on a PDF (optional)
    test_interactive_mode()


if __name__ == "__main__":
    main()
