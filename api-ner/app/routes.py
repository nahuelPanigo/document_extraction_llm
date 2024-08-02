from flask import Blueprint, request, jsonify
from app.utils.connect_services import get_ner_xml
from app.errors import ROUTE_ERRORS as RO_E

main = Blueprint('main', __name__)

@main.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify(RO_E["ERROR_NO_INPUT_DATA"]), RO_E["CODE_ERROR_NO_INPUT_DATA"]
    file = request.files['file']
    response_extraction,error = get_ner_xml(file)
    if error:
        return jsonify({"error": error}), 500
    else:
        return jsonify(response_extraction), 200