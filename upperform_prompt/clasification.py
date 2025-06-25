from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from constants import JSON_FOLDER,DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED
from utils.text_extraction.read_and_write_files import read_data_json
from sklearn.feature_extraction.text import TfidfVectorizer
from bs4 import BeautifulSoup

def clean_html(text):
    return BeautifulSoup(text, "html.parser").get_text(separator=" ")

import random
# Datos de entrada


filename = JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED


data = read_data_json(filename, "utf-8")

types = {}

for step,elem in data.items():
    for dict in elem:
        if dict["dc.type"] not in types:
            types[dict["dc.type"]] =  [dict["original_text"]]
        else:
            types[dict["dc.type"]].append(dict["original_text"])


texts_tesis = types["Tesis"][:100]
texts_articulos= types["Articulo"][:100]
texts_libros = types["Libro"]

labels_tesis = ["Tesis"] * len(texts_tesis)
labels_articulos = ["Articulo"] * len(texts_articulos)
labels_libros = ["Libro"] * len(texts_libros)

# Prepara textos y etiquetas como ya lo haces
texts = texts_tesis + texts_articulos + texts_libros
labels = labels_tesis + labels_articulos + labels_libros

texts = [clean_html(text) for text in texts]
# Shuffle
import random
combined = list(zip(texts, labels))
random.shuffle(combined)
texts_shuffled, labels_shuffled = zip(*combined)

# TF-IDF
vectorizer = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 3),
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