import ollama
import time

HEADER_PROMPT = """
<role> you are an expert in metadata extraction and validation. Your task is to process a given text and a JSON object containing metadata.</role>

<task>
Extract the semantic metadata from the text and provide it in JSON format:
You have to extract the metadata:
title, subtitle, subject, date, abstract.
Subject must be a ford Subject:
- Mathematics
- Computer and information sciences
- Physical sciences
- Chemical sciences
- Earth and related environmental sciences
- Biological sciences
- Other natural sciences
- Civil engineering
- Electrical engineering, electronic engineering, information engineering
- Mechanical engineering
- Chemical engineering
- Materials engineering
- Medical engineering
- Environmental engineering
- Environmental biotechnology
- Industrial biotechnology
- Nano-technology
- Other engineering and technologies
- Basic medicine
- Clinical medicine
- Health sciences
- Medical biotechnology
- Other medical sciences
- Agriculture, forestry, and fisheries
- Animal and dairy science
- Veterinary science
- Agricultural biotechnology
- Other agricultural sciences
- Psychology
- Economics and business
- Education
- Sociology
- Law
- Political science
- Social and economic geography
- Media and communications
- Other social sciences
- History and archaeology
- Languages and literature
- Philosophy, ethics and religion
- Arts (arts, history of arts, performing arts, music)
- Other humanities
"""

MIDDLE_PROMPT = """Here is a JSON Example format:"""

END_PROMPT = """Now, extract the metadata from the following text and provide it in the specified JSON format:"""

SCHEMA_TESIS = """ {
        "title": "",
        "subtitle": "",
        "subject": "",
        "date": "",
        abstract: ""
}"""

PROMPT_TESIS = f"""{HEADER_PROMPT}
{MIDDLE_PROMPT}{SCHEMA_TESIS}</task><context>{END_PROMPT}"""




text = """"<h2>DOSSIER Entre la corrección étnica y las fases del proceso revolucionario: formas de lo nacional-popular en el marxismo de Álvaro García Linera</h2><p>Between the ethnic correction and the phases of the revolutionary process: forms of the national-popular in the Marxism of Álvaro García Linera Marcelo Starcenbaum* IdIHCS/UNLP-CONICET - Argentina mstarcenbaum@gmail.com RESUMEN El objetivo de este trabajo es analizar las formas en las cuales se presenta el problema de lo nacional-popular en la obra de Álvaro García Linera. A través de un análisis de sus lecturas de los grandes movimientos de masas bolivianos y un seguimiento de las torsiones en su trayectoria como teórico marxista, damos cuenta de los modos en los cuales García Linera procesa lo nacional-popular en distintos momentos de su itinerario intelectual y distintas etapas de la historia boliviana. De esta manera recortamos un primer período en el cual la Revolución Nacional es censurada en nombre de una posición leninista y katarista, un segundo en el cual el proceso revolucionario de 1952 es abordado en términos ambivalente según una clave de lectura subalternista, y un tercero en el cual el desarrollo del evismo habilita un pensamiento en torno a las fases que caracterizan a los procesos políticos revolucionarios. Palabras clave: Álvaro García Linera; Marxismo; Nacional-popular; América Latina ABSTRACT The objective of this paper is to analyze the ways in which the national-popular problem is presented in the work of Álvaro García Linera. Through an analysis of his readings of the great Bolivian mass movements and an interest in the changes in his career as a Marxist theorist, we look at the ways in which García Linera processes the national-popular at different moments of his intellectual itinerary and different stages of Bolivian history. In this way we analyze a first period in which the National Revolution is censored in the name of a Leninist and Katarist position, a second in which the revolutionary process of 1952 is approached in ambivalent terms according to a subaltern reading, and a third in which the development of evismo enables a thought around the phases that characterize the revolutionary political processes. Keywords: Álvaro García Linera, Marxism, National-Popular; Latin America *Doctor en Historia, IdIHCS/UNLP-CONICET Recibido: 06/02/2019 Aceptado: 29/05/2019 RELIGACIÓN. REVISTA DE CIENCIAS SOCIALES Y HUMANIDADES Vol 4 • Nº 16 • Quito • Trimestral • Junio 2019 6 pp. 111 - 122 • ISSN 2477-9083 Entre la corrección étnica y las fases del proceso revolucionario: formas de lo nacional-popular en el marxismo  112</p><h1>221-111</h1><p>.pp</p><h2>,9102 oinuJ</h2><p>,61 ºN 4 LOV</p><h1>.NOICAGILER</h1><p>RESUMO O objetivo deste artigo é analisar as formas pelas quais o problema nacional-popular é apresentado na obra de Álvaro García Linera. Através de uma análise de suas leituras dos grandes movimentos de massa bolivianos e um interesse nas mudanças em sua carreira como teórico marxista, nós olhamos para as formas em que García Linera processa o nacional-popular em diferentes momentos de seu itinerário intelectual e diferentes estágios da história boliviana. Assim, analisamos um primeiro período em que a Revolução Nacional é censurada em nome de uma posição leninista e katarista, uma segunda em que o processo revolucionário de 1952 é abordado em termos ambivalentes de acordo com uma leitura subalterna e um terceiro em que o desenvolvimento do evismo possibilita um pensamento em torno das fases que caracterizam os processos políticos revolucionários. Palavras-chave: Álvaro García Linera, marxismo, nacional-popular; América latina I. La obra de Álvaro García Linera constituye una de las pocas inflexiones latinoamericanas en la tradición marxista que asumieron de manera positiva el problema de lo nacional-popular. Entre los múltiples marxismos desplegados en la historia contemporánea del subcontinente, el de García Linera se ubica junto al de otros pensadores en una franja caracterizada por una articulación entre los elementos teóricos fundamentales de la tradición y la singularidad política de la región. Si bien la delimitación de los vínculos entre el marxismo y lo nacional-popular no es una tarea sencilla, podemos avanzar hacia una sistematización del problema reuniendo en un mismo espacio a un conjunto de análisis y reflexiones que se han caracterizado por el otorgamiento de un carácter positivo a lo nacional y lo popular. A diferencia de otras corrientes del marxismo latinoamericano, pero también de las posiciones abiertamente populistas y nacionalistas, este espacio teórico ha evitado esencializar dichos fenómenos, pero a su vez los ha considerado fundamentales para un pensamiento histórico y político sobre la región. Sin dejar de comprenderla en los marcos del desarrollo capitalista, la nación se presenta como un espacio clave para el análisis de las formas de dominación y la constitución de un sujeto político revolucionario. Sin desconocer la estructura de clases que lo atraviesa, lo popular constituye una noción insoslayable a los fines de dar cuenta de la particularidad de los sectores subalternos. Sin olvidar su función en una sociedad de clases, el Estado aparece como un marco relevante para el entendimiento de la politicidad de las clases dominadas. A su vez, resulta productivo pensar el análisis marxista de lo nacional-popular como un espacio en el que convergen tres grandes problemas teóricos y políticos. En primer lugar, la discusión alrededor de la particularidad del capitalismo latinoamericano, la cual tiende a alejarse del evolucionismo y atender los diferentes regímenes productivos de la región. Por otra parte, un procesamiento singular de la obra de Marx y el marxismo, orientado hacia los textos y las discusiones centradas en el problema de la nación y las particularidades de la práctica política en sociedades atrasadas. Por último, la importancia de la problemática gramsciana de lo nacional-popular, lo cual direcciona la reflexión hacia las cuestiones de la constitución del pueblo y la distancia entre intelectuales y sectores populares.1 Al igual que en otros autores pertenecientes a este espacio, el vínculo establecido en la obra de García Linera entre el marxismo y lo nacional-popular está fuertemente condicionado por el desarrollo de experiencias históricas concretas. Así como la apertura del marxismo de José Aricó no puede ser disociada de los efectos del peronismo, la de René Zavaleta Mercado resulta incomprensible sin las consecuencias de la Revolución Nacional, y la de Armando Bartra sólo se vuelve inteligible a partir de las implicaciones del neocardenismo, la de García Linera también está estrechamente vinculada al despliegue de los movimientos de masas que marcaron la vida política de su país. Por un lado, al igual que Zavaleta Mercado, es el proceso impulsado por el Movimiento Nacionalista Revolucionario (MNR) el que orienta los esquemas interpretativos marxistas hacia la problemática nacional- popular. Sin embargo, y aquí se revela la singularidad de su obra, este direccionamiento también está condicionado por el desarrollo del movimiento liderado por Evo Morales a comienzos del siglo XXI. Y, del mismo modo que otros autores que se esforzaron por desplegar una aproximación positiva de lo nacional-popular, este tipo de vínculo con las experiencias políticas de masas no es característico de la totalidad de la obra ni de la trayectoria de García Linera. Al igual que tantos otros, su formación en la tradición marxista-leninista propició en un primer momento una censura de la problemática nacional-popular. El objetivo de este trabajo es analizar las formas en las cuales se presenta lo nacional-popular en el conjunto de la obra teórica y política de García Linera. El recorrido por sus trabajos se realizará teniendo como variables analíticas las dos dimensiones recientemente mencionadas. Es decir, por un lado, nos concentramos en los términos del análisis marxista de las dos experiencias nacionales populares bolivianas: la Revolución Nacional y el evismo. Por el otro, revisamos sus elaboraciones de manera diacrónica a los fines de evidenciar las torsiones que sufre el vínculo entre el marxismo y lo nacional-popular entre los dos polos de su trayectoria: la de la militancia katarista y la de la 1 Puede verse una versión ampliada de esta sistematización en Starcenbaum (2018). Marcelo Starcenbaum</p><h1>221-111</h1><p>.pp</p><h2>,9102 oinuJ</h2><p>,61 ºN 4 LOV</p><h1>.NOICAGILER</h1><p>113</p><h1>REISSOD</h1><p>vicepresidencia de la Nación."""

prompt = f"""{PROMPT_TESIS}{text[:6000]}</context>"""



try:
    start = time.time()
    response = ollama.generate(
        model='qwen3:4b',
        prompt=prompt,
        stream=False, # Set to True for streaming responses
        # You can add other options here as well, e.g.:
        # temperature=0.7,
        # top_p=0.9
    )
    print("content:", response['response'].strip())
    print(f"Time taken: {time.time() - start}")

except Exception as e:
    print(f"Error communicating with Ollama: {e}")
