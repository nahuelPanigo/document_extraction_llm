from openai import OpenAI
import os
import time
from dotenv import load_dotenv
from constants import PROMPT_CLEANER_METADATA, OPENAI_REQUEST_LIMIT, OPENAI_MODEL
from utils.colors.colors_terminal import Bcolors
from download_prepare_clean_normalize_sedici_dataset.cloud_llm_cleaner_consumer.base_consumer import BaseCloudLLMConsumer

load_dotenv()


class OpenaiConsumer(BaseCloudLLMConsumer):

    def __init__(self):
        super().__init__(OPENAI_REQUEST_LIMIT)
        api_key = os.getenv("OPENAI_API_KEY")
        self._client = OpenAI(api_key=api_key)

    def consume_llm(self, metadata, text, max_retries=3):
        input = f"""{PROMPT_CLEANER_METADATA}
            - Metadata: {metadata}
            - Text: {text}"""

        for attempt in range(max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are an expert in metadata validation and text analysis. Return only valid JSON."},
                        {"role": "user", "content": input},
                    ],
                )
                usage = response.usage
                print(
                    f"{Bcolors.OKBLUE}Tokens usados: prompt={usage.prompt_tokens}, "
                    f"completion={usage.completion_tokens}, total={usage.total_tokens}{Bcolors.ENDC}"
                )
                return response.choices[0].message.content

            except Exception as e:
                error_str = str(e)

                if "429" in error_str or "rate_limit" in error_str.lower():
                    backoff_time = (2 ** attempt) * 30
                    print(f"{Bcolors.WARNING}Rate limit hit. Using exponential backoff: {backoff_time}s (attempt {attempt + 1}/{max_retries}){Bcolors.ENDC}")
                    time.sleep(backoff_time)
                    continue

                if attempt == max_retries - 1:
                    raise e
                else:
                    print(f"{Bcolors.WARNING}Error: {e}. Retrying in 5s (attempt {attempt + 1}/{max_retries}){Bcolors.ENDC}")
                    time.sleep(5)
