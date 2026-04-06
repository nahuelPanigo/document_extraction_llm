import os
import json
import time
from pathlib import Path
import sys
from typing import Optional, Dict, Any
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))

from constants import (
    RESULT_FOLDER_VALIDATION, 
    PDF_FOLDER, 
    PROMPT_CLOUD_LLM_VALIDATOR
)
from utils.text_extraction.read_and_write_files import read_data_json, write_to_json
from utils.text_extraction.pdf_reader import PdfReader

class CloudLLMValidator:
    """
    Cloud LLM integration for document metadata validation
    Supports multiple LLM providers through LangSmith
    """
    
    def __init__(self, provider: str = "gemini", model: str = None):
        """
        Initialize the Cloud LLM Validator
        
        Args:
            provider: LLM provider ("gemini", "openai", "anthropic")
            model: Specific model name (optional, uses defaults)
        """
        self.provider = provider.lower()
        self.model = model or self._get_default_model()
        self.pdf_reader = PdfReader()
        self.results_folder = RESULT_FOLDER_VALIDATION / "CLOUDLLM"
        self.results_folder.mkdir(parents=True, exist_ok=True)
        
        # Initialize LangSmith client
        self._init_langsmith_client()
    
    def _get_default_model(self) -> str:
        """Get default model for each provider"""
        defaults = {
            "gemini": "gemini-2.0-flash-exp",
            "openai": "gpt-5.4-mini",
            "anthropic": "claude-3-5-sonnet-20241022"
        }
        return defaults.get(self.provider, "gemini-2.0-flash-exp")
    
    def _init_langsmith_client(self):
        """Initialize LangSmith client based on provider"""
        try:
            from langsmith import Client
            
            # Initialize LangSmith client
            self.langsmith_client = Client()
            
            # Initialize provider-specific client
            if self.provider == "gemini":
                self._init_gemini_client()
            elif self.provider == "openai":
                self._init_openai_client()
            elif self.provider == "anthropic":
                self._init_anthropic_client()
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except ImportError as e:
            print(f"❌ Error importing LangSmith: {e}")
            print("Install with: pip install langsmith")
            raise
        except Exception as e:
            print(f"❌ Error initializing LangSmith: {e}")
            raise
    
    def _init_gemini_client(self):
        """Initialize Google Gemini client"""
        try:
            import google.generativeai as genai
            
            # Configure Gemini API
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is required")
            
            genai.configure(api_key=api_key)
            self.llm_client = genai.GenerativeModel(self.model)
            print(f"✅ Initialized Gemini client with model: {self.model}")
            
        except ImportError:
            print("❌ Google Generative AI not found. Install with: pip install google-generativeai")
            raise
    
    def _init_openai_client(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            
            self.llm_client = OpenAI(api_key=api_key)
            print(f"✅ Initialized OpenAI client with model: {self.model}")
            
        except ImportError:
            print("❌ OpenAI package not found. Install with: pip install openai")
            raise
    
    def _init_anthropic_client(self):
        """Initialize Anthropic client"""
        try:
            import anthropic
            
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable is required")
            
            self.llm_client = anthropic.Anthropic(api_key=api_key)
            print(f"✅ Initialized Anthropic client with model: {self.model}")
            
        except ImportError:
            print("❌ Anthropic package not found. Install with: pip install anthropic")
            raise
    
    def extract_text_from_pdf(self, pdf_path: Path) -> Optional[str]:
        """
        Extract text from PDF using the pdf_reader utility
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text with XML tags or None if error
        """
        try:
            print(f"📄 Extracting text from: {pdf_path.name}")
            extracted_text = self.pdf_reader.extract_text_with_xml_tags(pdf_path, ocr=True)
            
            if not extracted_text.strip():
                print(f"⚠️ No text extracted from {pdf_path.name}")
                return None
                
            print(f"✅ Extracted {len(extracted_text)} characters from {pdf_path.name}")
            return extracted_text
            
        except Exception as e:
            print(f"❌ Error extracting text from {pdf_path.name}: {str(e)}")
            return None
    
    def query_llm(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Query the configured LLM with the extracted text
        
        Args:
            text: Extracted text from PDF
            
        Returns:
            Parsed JSON response or None if error
        """
        try:
            prompt = f"{PROMPT_CLOUD_LLM_VALIDATOR}\n\n{text}"
            
            if self.provider == "gemini":
                response = self._query_gemini(prompt)
            elif self.provider == "openai":
                response = self._query_openai(prompt)
            elif self.provider == "anthropic":
                response = self._query_anthropic(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            # Parse JSON response
            try:
                # Clean response (remove markdown formatting if present)
                clean_response = response.strip()
                if clean_response.startswith("```json"):
                    clean_response = clean_response[7:-3].strip()
                elif clean_response.startswith("```"):
                    clean_response = clean_response[3:-3].strip()
                
                parsed_response = json.loads(clean_response)
                return parsed_response
                
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing JSON response: {e}")
                print(f"Raw response: {response[:200]}...")
                return None
                
        except Exception as e:
            print(f"❌ Error querying LLM: {str(e)}")
            return None
    
    def _query_gemini(self, prompt: str) -> str:
        """Query Gemini model"""
        try:
            response = self.llm_client.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"❌ Gemini API error: {str(e)}")
            raise
    
    def _query_openai(self, prompt: str) -> str:
        """Query OpenAI model"""
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ OpenAI API error: {str(e)}")
            raise
    
    def _query_anthropic(self, prompt: str) -> str:
        """Query Anthropic model"""
        try:
            response = self.llm_client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Anthropic API error: {str(e)}")
            raise
    
    def process_document(self, doc_id: str, pdf_path: Path) -> Optional[Dict[str, Any]]:
        """
        Process a single document: extract text and get metadata from LLM
        
        Args:
            doc_id: Document identifier
            pdf_path: Path to PDF file
            
        Returns:
            Extracted metadata or None if error
        """
        print(f"\n🔍 Processing document: {doc_id}")
        
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return None
        
        # Query LLM for metadata extraction
        metadata = self.query_llm(text)
        if not metadata:
            return None
        
        # Return metadata directly without wrapper keys
        print(f"✅ Successfully processed {doc_id}")
        return metadata
    
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
    # Configuration - can be changed here or via environment variables
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "openai")  # gemini, openai, anthropic
    model = os.getenv("LLM_MODEL", None)  # Optional specific model
    
    print(f"🚀 Starting Cloud LLM Validation with {provider}")
    print("=" * 60)
    
    try:
        # Initialize validator
        validator = CloudLLMValidator(provider=provider, model=model)
        
        # Read JSON file
        json_file_path = RESULT_FOLDER_VALIDATION / "final_to_compare_original.json"

        print(json_file_path)
        
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

            if not pdf_path.exists():
                print(f"⚠️ PDF file not found: {pdf_path}")
                continue

            # Process document
            t0 = time.time()
            result = validator.process_document(doc_id, pdf_path)
            elapsed = time.time() - t0
            doc_times.append(elapsed)
            norm = _norm_type(metadata.get("type", ""))
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
            filename = f"langsmith_validation_{provider}_{timestamp}.json"
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
    print(RESULT_FOLDER_VALIDATION)
    print("hola")
    main()