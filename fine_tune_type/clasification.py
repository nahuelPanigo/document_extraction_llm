from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from constants import JSON_FOLDER,DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED,DATASET_TYPE,PDF_FOLDER,DATA_FOLDER
from utils.text_extraction.read_and_write_files import read_data_json,write_to_json,read_data_txt
from sklearn.feature_extraction.text import TfidfVectorizer
from bs4 import BeautifulSoup
import random
import os
from utils.consume_apis.consume_extractor import make_requests_only_text
from dotenv import load_dotenv

def clean_html(text):
    return BeautifulSoup(text, "html.parser").get_text(separator=" ")


def clear_ids_no_pdf(data):
    final_data = {"Libro": [], "Tesis": [], "Articulo": []}
    pdf_files = [x.replace(".pdf","") for x in os.listdir(PDF_FOLDER)]
    for type in data:
        for elem in data[type]:
            if elem in pdf_files:
                final_data[type].append(elem)
    return final_data



TEXT_FOLDER = DATA_FOLDER /  "texts2"

def filter_existing_ids(ids, folder):
    return [id_ for id_ in ids if (folder / f"{id_}.txt").exists()]

# Datos de entrada

if __name__ == "__main__":
    load_dotenv()
    filename = JSON_FOLDER / DATASET_TYPE
    data = read_data_json(filename, "utf-8")

    id_tesis = data["Tesis"]
    id_libros = data["Libro"]
    id_articulos = data["Articulo"]

    id_tesis = filter_existing_ids(id_tesis, TEXT_FOLDER)[:1450]
    id_libros = filter_existing_ids(id_libros, TEXT_FOLDER)[:1450]
    id_articulos = filter_existing_ids(id_articulos, TEXT_FOLDER)[:1450]

    print(f"Se han encontrado {len(id_tesis)} tesis")
    print(f"Se han encontrado {len(id_articulos)} articulos")   
    print(f"Se han encontrado {len(id_libros)} libros")

    texts_tesis = [read_data_txt(TEXT_FOLDER / f"{id_tesis[i]}.txt","utf-8") for i in range(len(id_tesis))]
    texts_libros = [read_data_txt(TEXT_FOLDER / f"{id_libros[i]}.txt","utf-8") for i in range(len(id_libros))]
    texts_articulos = [read_data_txt(TEXT_FOLDER / f"{id_articulos[i]}.txt","utf-8") for i in range(len(id_articulos))]

    token_extractor = os.getenv("EXTRACTOR_TOKEN")

    filename = JSON_FOLDER / "textos_extraccion.json"
    print("comenzando el entrenamiento")


    labels_tesis = ["tesis"] * len(texts_tesis)
    labels_articulos = ["articulo"] * len(texts_articulos)
    labels_libros = ["libro"] * len(texts_libros)

    # Prepara textos y etiquetas como ya lo haces
    texts = texts_tesis + texts_articulos + texts_libros
    labels = labels_tesis + labels_articulos + labels_libros


    #texts = [clean_html(text) for text in texts]
    # Shuffle
    import random
    combined = list(zip(texts, labels))
    random.shuffle(combined)
    texts_shuffled, labels_shuffled = zip(*combined)

    # TF-IDF
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 4),
        analyzer='word',
        sublinear_tf=True,
    )

    X = vectorizer.fit_transform(texts_shuffled)

    # Clasificación
    X_train, X_test, y_train, y_test = train_test_split(X, labels_shuffled, test_size=0.2, random_state=42)

    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred))

    import joblib
    joblib.dump(clf, 'modelo_tipo_documento.pkl')
    joblib.dump(vectorizer, 'vectorizador_tfidf.pkl')