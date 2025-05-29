# from transformers import LEDForConditionalGeneration, LEDTokenizer
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GOOGLE_API_KEY)


def consume_llm(input):    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=input,
    )
    return response.text

