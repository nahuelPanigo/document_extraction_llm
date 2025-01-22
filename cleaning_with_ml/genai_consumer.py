# from transformers import LEDForConditionalGeneration, LEDTokenizer
import google.generativeai as genai
import os
from dotenv import load_dotenv



load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model=genai.GenerativeModel("models/gemini-1.5-flash-latest")






PROMPT = """
You are an expert in metadata validation and text analysis. Your task is to process a given text and a JSON object containing metadata. Follow these steps precisely:

1. Analyze the provided text and metadata object.

2. For each key-value pair in the metadata:
    - Search the text for the metadata value (or a variation of it, such as differences in case, abbreviations, punctuation, or word order).
    - If the value exists in the text but is written differently, update the metadata value to match the exact appearance in the text.
    - If the value does not appear in the text, remove that key from the metadata.

3. Ensure all metadata values in the JSON object match their exact appearance in the text.

4. Return **only** the corrected JSON schema. Do not include explanations, comments, the original text, or the original metadata. The output first char must be '{' and the last one'}'

Input example:
- Text: "This paper was written by Juan M. Pérez in 2024."
- Metadata: {"author": "Perez, Juan Manuel", "year": "2024", "journal": "Journal of AI Research"}

Output example:
{"author": "Juan M. Pérez", "year": "2024"}

Input example:
- Text: "Dr. María García collaborated with John O'Connor to publish this work in 2023."
- Metadata: {"author1": "Garcia, Maria", "author2": "OConnor, John", "year": "2023", "publisher": "AI Press"}

Output example:
{"author1": "Dr. María García", "author2": "John O'Connor", "year": "2023"}

you must pay attention in the json provided after this:
"""

LIMIT_CHARS = 9500

def consume_llm(metadata,text):
    input = f"""{PROMPT}  
        - Metadata: {metadata}
        - Text: {text}"""
    input = input[:LIMIT_CHARS]
    response = model.generate_content(input)
    return response.text
