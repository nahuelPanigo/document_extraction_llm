from google import genai
import os
import re
import time
from dotenv import load_dotenv
from constants import PROMPT_CLEANER_METADATA, GENAI_REQUEST_LIMIT, GENAI_MODEL
from utils.colors.colors_terminal import Bcolors
from download_prepare_clean_normalize_sedici_dataset.cloud_llm_cleaner_consumer.base_consumer import BaseCloudLLMConsumer

load_dotenv()


class GenaiConsumer(BaseCloudLLMConsumer):

    def __init__(self):
        super().__init__(GENAI_REQUEST_LIMIT)
        api_key = os.getenv("GOOGLE_API_KEY")
        self._client = genai.Client(api_key=api_key)

    def consume_llm(self, metadata, text, max_retries=3):
        input = f"""{PROMPT_CLEANER_METADATA}
            - Metadata: {metadata}
            - Text: {text}"""

        for attempt in range(max_retries):
            try:
                response = self._client.models.generate_content(
                    model=GENAI_MODEL,
                    contents=input,
                )
                return response.text

            except Exception as e:
                error_str = str(e)

                if "429" in error_str and "RESOURCE_EXHAUSTED" in error_str:
                    retry_delay = self._extract_retry_delay(error_str)

                    if retry_delay:
                        print(f"{Bcolors.WARNING}Rate limit hit. Waiting {retry_delay}s + 1s buffer before retry (attempt {attempt + 1}/{max_retries}){Bcolors.ENDC}")
                        time.sleep(retry_delay + 1)
                        continue
                    else:
                        backoff_time = (2 ** attempt) * 30
                        print(f"{Bcolors.WARNING}Rate limit hit, no retry delay found. Using exponential backoff: {backoff_time}s (attempt {attempt + 1}/{max_retries}){Bcolors.ENDC}")
                        time.sleep(backoff_time)
                        continue

                if attempt == max_retries - 1:
                    raise e
                else:
                    print(f"{Bcolors.WARNING}Error: {e}. Retrying in 5s (attempt {attempt + 1}/{max_retries}){Bcolors.ENDC}")
                    time.sleep(5)

    def _extract_retry_delay(self, error_str):
        try:
            retry_match = re.search(r'Please retry in ([\d.]+)s\.', error_str)
            if retry_match:
                return float(retry_match.group(1))
            retry_match = re.search(r"'retryDelay': '(\d+)s'", error_str)
            if retry_match:
                return float(retry_match.group(1))
            return None
        except (ValueError, AttributeError):
            return None
