from flask import Blueprint, request, jsonify
from app.utils.extraction.text_extraction import get_text
from app.utils.model_manipulation.llms_extraction import model_extraction
from app.errors import ROUTE_ERRORS as RO_E

main = Blueprint('main', __name__)

@main.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify(RO_E["ERROR_NO_INPUT_DATA"]), RO_E["CODE_ERROR_NO_INPUT_DATA"]
    file = request.files['file']
    response_extraction,error = get_text(file)
    if(error is not None):
        return jsonify(response_extraction), error
    response_ml,error = model_extraction(response_extraction["text"])
    if (error is not None):
        return jsonify(response_ml), error
    return response_ml