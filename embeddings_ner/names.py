
import os
from dotenv import load_dotenv
import google.generativeai as genai
from pathlib import Path
import json
from scipy.spatial.distance import cosine

def find_most_similar(embedding, embeddings_dict,incName):
    # Encuentra el vector más cercano usando similitud coseno
    most_similar_name = None
    similarities=[]
    highest_similarity = -1  # Menor posible para similitud coseno (coseno más grande implica más cercano)
    
    for name, candidate_embedding in embeddings_dict.items():
        similarity = 1 - cosine(embedding, candidate_embedding)  # Similitud coseno
        similarities.append((incName,name, similarity))
        if similarity > highest_similarity:
            highest_similarity = similarity
            most_similar_name = name

    return most_similar_name, highest_similarity,similarities


ROOT_DIR = Path(__file__).resolve().parents[1]  / "fine_tunning"
DATA_FOLDER = ROOT_DIR / "data" / "sedici" / "jsons"

filename = DATA_FOLDER / "final_metadata_Chekced2.json"

def flatten_comprehension(matrix):  
    new_matrix = [] 
    for elem in matrix:
        if(isinstance(elem,list)):
            matrix.extend(elem)
        else:
            new_matrix.append(elem)
    return new_matrix

with open(filename) as f:
    data = json.load(f)
    nombres_con_errores = ([value["sedici.creator.person"] for key,value in list(data.items())[30:40]])
    nombres_con_errores = flatten_comprehension(nombres_con_errores)

nombres_reales = ['Santucho, Veronica','Sanchez Veronica' ,'Panigo, Nahuel','Villanueva, Magali Jimena', 'González, Ernesto', 'Rodríguez, Fernando', 'Hoffmann, Karen', 'García Lambas, Dolores', 'Gaztañaga, Emanuel' , 'Garcia, Damian', 'Balghzal, Ahmed','Barberá, José Andres Miguel', 'Vela Gonzáles, Marta', 'Gisbert Caudeli, Vicenta', 'Elisondo, Romina Cecilia', 'Herreras Carrera, Alex', 'Farina, María Andrea', 'De la Ossa Martínez, Marco Antonio', 'Partida-Valdivia, José Marcos', 'Weik, Christian','Pelizza, Fabricio Nahuel', 'Pastor, Sebastián Oscar', 'Sario, Gisela', 'Medina, Matías Eduardo']

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
model_name = "gemini-1.5-pro"

genai.configure(api_key=GOOGLE_API_KEY)


from google.api_core import retry
from tqdm.rich import tqdm


tqdm.pandas()

@retry.Retry(timeout=300.0)
def embed_fn(text: str) -> list[float]:
    # You will be performing classification, so set task_type accordingly.
    response = genai.embed_content(
        model="models/text-multilingual-embedding-002", content=text, task_type="SEMANTIC_SIMILARITY"
    )

    return response["embedding"]


def create_embeddings(nombres_reales , nombres_con_errores):
    dict_nombres_con_errores = {elem : embed_fn(elem) for elem in nombres_con_errores}  
    dict_nombres_reales = {elem : embed_fn(elem) for elem in nombres_reales}  
    return dict_nombres_con_errores , dict_nombres_reales

dict_nombres_con_errores , dict_nombres_reales = create_embeddings(nombres_reales , nombres_con_errores)


for key in dict_nombres_con_errores:
    