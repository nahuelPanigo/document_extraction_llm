import os
import json
from pathlib import Path
import sys
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import time

sys.path.append(str(Path(__file__).resolve().parents[1]))

from constants import (
    RESULT_FOLDER_VALIDATION,
    PDF_FOLDER,
    ROOT_DIR
)
from utils.text_extraction.read_and_write_files import read_data_json, write_to_json
from utils.consume_apis.consume_orchestrator import upload_file


class FinetunedValidator:
    """
    Validator using local fine-tuned orchestrator service
    Calls the orchestrator service to extract metadata from PDFs
    """

    def __init__(self, orchestrator_url: str = None, token: str = None, ocr: bool = False):
        """
        Initialize the Finetuned Validator

        Args:
            orchestrator_url: URL of orchestrator service (default: http://localhost:8000)
            token: Bearer token for authentication
            ocr: Enable OCR for image extraction
        """
        load_dotenv()

        self.orchestrator_url = orchestrator_url or os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
        self.token = token or os.getenv("ORCHESTRATOR_TOKEN")
        self.ocr = ocr

        if not self.token:
            raise ValueError("ORCHESTRATOR_TOKEN environment variable is required or pass token parameter")

        self.results_folder = RESULT_FOLDER_VALIDATION / "FINETUNNED"
        self.results_folder.mkdir(parents=True, exist_ok=True)

        print(f"✅ Initialized Finetuned Validator")
        print(f"🔗 Orchestrator URL: {self.orchestrator_url}")
        print(f"🔍 OCR enabled: {self.ocr}")

    def process_document(self, doc_id: str, pdf_path: Path, normalization: bool = True,
                        deepanalyze: bool = False, doc_type: str = "None") -> Optional[Dict[str, Any]]:
        """
        Process a single document through the orchestrator service

        Args:
            doc_id: Document identifier
            pdf_path: Path to PDF file
            normalization: Apply text normalization
            deepanalyze: Enable deep analysis
            doc_type: Document type (Articulo, Libro, Tesis, etc.)

        Returns:
            Extracted metadata or None if error
        """
        print(f"\n🔍 Processing document: {doc_id}")

        try:
            # Call orchestrator service
            print(f"📤 Sending {pdf_path.name} to orchestrator service...")
            response = upload_file(
                file_path=pdf_path,
                token=self.token,
                normalization=normalization,
                type=doc_type,
                deepanalyze=deepanalyze,
                host_url=self.orchestrator_url,
                ocr=self.ocr
            )

            # Debug: print raw response
            print(f"📥 Raw response type: {type(response)}")
            print(f"📥 Raw response: {response}")

            # Check if request was successful
            if not response:
                print(f"❌ Empty response from orchestrator for {doc_id}")
                return None

            # Check for errors in response
            if not response.get("success", False):
                error_msg = response.get("error", {}).get("message", "Unknown error")
                error_code = response.get("error", {}).get("code", "Unknown code")
                print(f"❌ Orchestrator error for {doc_id}: {error_msg} (code: {error_code})")
                return None

            # Extract metadata from response
            metadata = response.get("data", {})

            if not metadata:
                print(f"⚠️ No metadata extracted for {doc_id}")
                return None

            # Return metadata directly without wrapper keys
            print(f"✅ Successfully processed {doc_id}")
            print(f"📊 Extracted fields: {list(metadata.keys())}")

            return metadata

        except Exception as e:
            print(f"❌ Error processing {doc_id}: {str(e)}")
            return None

    def save_results(self, results: Dict[str, Any], filename: str):
        """Save results to JSON file"""
        output_path = self.results_folder / filename
        try:
            write_to_json(output_path, results, 'utf-8')
            print(f"💾 Results saved to: {output_path}")
        except Exception as e:
            print(f"❌ Error saving results: {str(e)}")


def main():
    """Main function to run the validation process"""
    load_dotenv()

    # Configuration
    orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
    token = os.getenv("ORCHESTRATOR_TOKEN")
    ocr = os.getenv("OCR_ENABLED", "false").lower() == "true"
    normalization = os.getenv("NORMALIZATION_ENABLED", "true").lower() == "true"
    deepanalyze = os.getenv("DEEPANALYZE_ENABLED", "false").lower() == "true"

    print(f"🚀 Starting Finetuned Model Validation")
    print("=" * 60)

    try:
        # Initialize validator
        validator = FinetunedValidator(
            orchestrator_url=orchestrator_url,
            token=token,
            ocr=ocr
        )

        # Read JSON file
        #json_file_path = RESULT_FOLDER_VALIDATION / "test_metadata_validada.json"

        json_file_path = RESULT_FOLDER_VALIDATION / "final_to_compare_original.json"

        try:
            data = read_data_json(json_file_path, 'utf-8')
        except Exception as e:
            print(f"❌ Error reading JSON file: {str(e)}")
            return

        if not data:
            print("❌ No data found in JSON file")
            return

        print(f"📋 Found {len(data)} documents to process")

        def _norm_type(t):
            t = str(t).lower()
            if "tesis" in t: return "Tesis"
            if "articulo" in t or "artículo" in t: return "Articulo"
            if "libro" in t: return "Libro"
            if "conferencia" in t: return "Objeto de conferencia"
            return "Other"

        # Process each document
        results = {}
        successful_count = 0
        doc_times = []
        type_times = {}

        for doc_id, metadata in data.items():
            if not doc_id:
                continue

            # Construct PDF filename
            pdf_filename = f"{doc_id}.pdf"
            pdf_path = PDF_FOLDER / pdf_filename

            print(f"🔍 Looking for PDF: {pdf_path}")
            print(f"   PDF_FOLDER: {PDF_FOLDER}")
            print(f"   doc_id: {doc_id}")
            print(f"   pdf_filename: {pdf_filename}")
            print(f"   Path exists: {pdf_path.exists()}")

            if not pdf_path.exists():
                print(f"⚠️ PDF file not found: {pdf_path}")
                continue

            # Extract document type from original metadata
            doc_type = metadata.get("type", metadata.get("dc.type", "None"))

            # Process document
            t0 = time.time()
            result = validator.process_document(
                doc_id=doc_id,
                pdf_path=pdf_path,
                normalization=normalization,
                deepanalyze=deepanalyze,
                doc_type=doc_type
            )
            elapsed = time.time() - t0
            doc_times.append(elapsed)
            norm = _norm_type(doc_type)
            type_times.setdefault(norm, []).append(elapsed)
            print(f"⏱️  {doc_id} took {elapsed:.2f}s")

            if result:
                results[doc_id] = result
                successful_count += 1

        # Print timing stats
        if doc_times:
            print(f"\n⏱️  Timing stats ({len(doc_times)} docs):")
            print(f"   Min : {min(doc_times):.2f}s")
            print(f"   Max : {max(doc_times):.2f}s")
            print(f"   Avg : {sum(doc_times)/len(doc_times):.2f}s")
            print(f"\n⏱️  Timing by type:")
            for t in ["Libro", "Tesis", "Articulo", "Objeto de conferencia"]:
                times = type_times.get(t, [])
                if times:
                    print(f"   {t} (n={len(times)}): min={min(times):.2f}s  max={max(times):.2f}s  avg={sum(times)/len(times):.2f}s")

        # Save results
        if results:
            timestamp = int(time.time())
            ocr_suffix = "_ocr" if ocr else ""
            deepanalyze_suffix = "_deepanalyze" if deepanalyze else ""
            filename = f"finetuned_validation{ocr_suffix}{deepanalyze_suffix}_{timestamp}_with_date_fixed.json"
            validator.save_results(results, filename)

            print(f"\n✅ Validation completed!")
            print(f"📊 Successfully processed: {successful_count}/{len(data)} documents")
            print(f"💾 Results saved to: {validator.results_folder / filename}")
        else:
            print("❌ No documents were successfully processed")

    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
