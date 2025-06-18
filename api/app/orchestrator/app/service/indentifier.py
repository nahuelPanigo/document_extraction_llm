import joblib
from app.logging_config import logging
from pathlib import Path

class TypeIdentifier:
    def __init__(self,path_clf : str,path_vectorizer : str):
        base_dir = Path(__file__).resolve().parent.parent  # llega a `orchestrator/`
        self.clf = joblib.load( base_dir / path_clf)
        self.vectorizer = joblib.load( base_dir / path_vectorizer)
        self.logger = logging.getLogger(__name__)  

    def predecir_tipo_documento(self,texto:str) -> str:
        logging.info(f"loading tyoe identifier model")
        vector = self.vectorizer.transform([texto])
        logging.info(f"predicting type of document")
        prediccion = self.clf.predict(vector)
        logging.info(f"type of document: {prediccion[0]}")
        return prediccion[0]



