MODEL_ERRORS = {
    "ERROR_PARSING_OUTPUT" : {'error' : 'cannot parse json output'},
    "ERROR_OPENING_MODEL" : {'error' : 'server internal error'},
    "CODE_ERROR_PARSING_OUTPUT" : 500,
    "CODE_ERROR_OPENING_MODEL" : 500
}

INPUT_ERRORS = {
    "ERROR_FORMAT_EXTENSION" : {'error' : 'fromat extension not permitted'},
    "ERROR_EXTARCTING_TEXT" : {'error' : 'server internal error'},
    "CODE_ERROR_FORMAT_EXTENSION": 400,
    "CODE_ERROR_EXTARCTING_TEXT": 500
}

ROUTE_ERRORS = {
    "ERROR_NO_INPUT_DATA" : {'error' : 'No file part'},
    "CODE_ERROR_NO_INPUT_DATA" : 400
}