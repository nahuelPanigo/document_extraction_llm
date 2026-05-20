import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.app.orchestrator.app.service.pattern_extractors import extract_abstract


doc = """
Acerca de la Querella de las\nMujeres\nMÓNICA BEATRIZ BORNIA\nFACULTAD DE CIENCIAS JURÍDICAS Y SOCIALES (UNLP)\nResumen\nSe conoce con este nombre («Querella de las Mujeres») al debate académico\nque tuvo lugar en Europa desde mediados del siglo XI, principalmente entre\nhombres: unos a favor, otros en contra de la tesis de la superioridad natural\nque ellos mismos se atribuían. El Humanismo, como movimiento literario y\npolítico, plantea por primera vez en Europa el proyecto de igualdad entre los\nsexos; una igualdad entendida como igualdad ante el conocimiento (no como\nvalor igual de lo femenino y lo masculino).\nPalabras clave\nQuerella; mujeres; género; igualdad.\n2131 | SALUD DE LA MUJER\n\nPara algunas gentes no es suficiente la preeminencia del sexo masculino, sino que\npretenden confinar a las mujeres a una reclusión, inevitable y necesaria, a la rueca;\nsí, a la rueca.\nMARIE LE JARS DE GOURNAY\nVivimos tiempos de grandes reivindicaciones y también, debemos\ndecirlo, de grandes ignorancias. 
"""


result = extract_abstract(doc)

print("\n=== RESULT ===\n")
print(result)