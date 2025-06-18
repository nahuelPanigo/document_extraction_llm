MODEL_ERRORS = {
    "ERROR_PARSING_OUTPUT" : {'error' : 'cannot parse json output'},
    "ERROR_OPENING_MODEL" : {'error' : 'server internal error'},
    "INTERNAL_ERROR_PARSING_OUTPUT" : {'error' : 'internal error during parsing output'},
    "CODE_ERROR_PARSING_OUTPUT" : 500,
    "CODE_ERROR_OPENING_MODEL" : 500,
    "CODE_INTERNAL_ERROR_PARSING_OUTPUT" : 500
}


ROUTE_ERRORS = {
    "ERROR_NO_INPUT_DATA" : {'error' : 'No text input'},
    "CODE_ERROR_NO_INPUT_DATA" : 400
}