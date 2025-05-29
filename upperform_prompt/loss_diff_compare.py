from difflib import SequenceMatcher
from sentence_transformers import SentenceTransformer, util
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

def similarity_score(a, b):
    """ Devuelve un score de similitud entre dos strings. """
    if not a or not b:
        return 0.0
    # Intenta semántica primero
    emb_a = model.encode(a, convert_to_tensor=True)
    emb_b = model.encode(b, convert_to_tensor=True)
    cosine_sim = float(util.pytorch_cos_sim(emb_a, emb_b)[0][0])
    return cosine_sim

def get_diff(metadata_expected: dict, metadata_response: dict) -> float:
    """
    Calcula una métrica de similitud ponderada entre el metadata real y el generado.
    Devuelve un score entre 0.0 y 1.0
    """
    if not isinstance(metadata_response, dict):
        return 0.0  # Respuesta malformada

    total_score = 0
    fields_checked = 0

    for key, expected_value in metadata_expected.items():
        fields_checked += 1
        response_value = metadata_response.get(key, None)

        # Penaliza campos faltantes
        if response_value is None:
            continue  # Suma 0 al total

        score = similarity_score(str(expected_value), str(response_value))
        total_score += score

    if fields_checked == 0:
        return 0.0
    
    return round(total_score / fields_checked, 4)