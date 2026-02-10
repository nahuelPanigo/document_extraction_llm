from abc import ABC, abstractmethod
import json
import threading
import time
from constants import APROX_TOK_PER_SOL
from utils.text_extraction.read_and_write_files import read_data_json, write_to_json
from utils.colors.colors_terminal import Bcolors


class BaseCloudLLMConsumer(ABC):

    def __init__(self, request_limits):
        self._running = True
        self._lock = threading.Lock()
        self._request_limits = request_limits.copy()
        self._initial_limits = request_limits.copy()

    @abstractmethod
    def consume_llm(self, metadata, text, max_retries=3):
        """Send metadata + text to the cloud LLM and return the cleaned response string."""
        pass

    def _can_make_request(self):
        return (
            self._request_limits["req_per_min"] > 0
            and self._request_limits["req_per_day"] > 0
            and self._request_limits["tok_per_min"] >= APROX_TOK_PER_SOL
        )

    def _decrement_limits(self):
        self._request_limits["req_per_min"] -= 1
        self._request_limits["req_per_day"] -= 1
        self._request_limits["tok_per_min"] -= APROX_TOK_PER_SOL
        print(
            f"{Bcolors.OKGREEN}Solicitud realizada: "
            f"req_per_min={self._request_limits['req_per_min']}, "
            f"req_per_day={self._request_limits['req_per_day']}, "
            f"tok_per_min={self._request_limits['tok_per_min']}{Bcolors.ENDC}"
        )

    def _reset_limits_loop(self):
        while self._running:
            time.sleep(60)
            with self._lock:
                self._request_limits["req_per_min"] = self._initial_limits["req_per_min"]
                self._request_limits["tok_per_min"] = self._initial_limits["tok_per_min"]
                print(
                    f"{Bcolors.OKBLUE}Request Limits: "
                    f"req_per_min={self._initial_limits['req_per_min']}, "
                    f"tok_per_min={self._initial_limits['tok_per_min']}{Bcolors.ENDC}"
                )

    def make_request(self, metadata, extracted_text):
        while True:
            while not self._can_make_request():
                print(
                    f"{Bcolors.WARNING}No se puede realizar la solicitud, esperando...{Bcolors.ENDC}",
                    self._request_limits,
                )
                time.sleep(5)
            response = self.consume_llm(metadata, extracted_text)
            with self._lock:
                self._decrement_limits()
            return response

    def save_json(self, id, data, output_filename, extracted_text):
        try:
            metadata = read_data_json(output_filename, "utf-8")
            data = data.strip()
            if data.startswith("```json") and data.endswith("```"):
                data = data[7:-3].strip()
            else:
                print(data[7:-3].strip())
            data = json.loads(data)
            metadata[id] = data
            metadata[id]["original_text"] = extracted_text
            write_to_json(output_filename, metadata, "utf-8")
        except json.JSONDecodeError as e:
            print(f"{Bcolors.FAIL}Decode Error in JSON: {e}{Bcolors.ENDC}")
            print(data)

    def get_metadata_to_process(self, metadatas_filename, final_json_filename):
        new_metadatas = read_data_json(metadatas_filename, "utf-8")
        if not (final_json_filename).exists():
            return new_metadatas
        final_metadatas = read_data_json(final_json_filename, "utf-8")
        return {
            k: v for k, v in new_metadatas.items() if k not in final_metadatas.keys()
        }

    def process_metadatas(self, metadatas_filename, final_json_filename):
        print(f"{Bcolors.OKGREEN}extracting metadatas{Bcolors.ENDC}")
        metadatas = self.get_metadata_to_process(metadatas_filename, final_json_filename)
        print(f"{Bcolors.OKGREEN}processing metadatas{Bcolors.ENDC}")
        already_processed = read_data_json(final_json_filename, "utf-8")
        metadatas_to_process = {k: v for k, v in metadatas.items() if k not in already_processed.keys()}
        for index, metadata in metadatas_to_process.items():
            try:
                extracted_text = metadata["original_text"]
                id = index
                dict_metadata = {k: v for k, v in metadata.items() if k not in ["original_text"]}
                response = self.make_request(dict_metadata, extracted_text)
                if response:
                    self.save_json(id, response, final_json_filename, extracted_text)
            except Exception as e:
                print(f"cannot process the row {index} error: {e}")

    def clean_metadata(self, metadata_filename, final_json_filename):
        reset_thread = threading.Thread(target=self._reset_limits_loop)
        reset_thread.daemon = True
        reset_thread.start()
        self.process_metadatas(metadata_filename, final_json_filename)
        self._running = False
