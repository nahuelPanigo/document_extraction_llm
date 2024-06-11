# FINE TUNNING LED LONG DOCUMENT TRANSFORMER 


the folder fine_tunning consists in all content to fine_tune the model except the json:
    **arxiv-metadata-oai-snapshot.json**
this has to be download and added into fine_tunning/data 

## STEPS TO MAKE FINE_TUNNING

**the first and second step could be avoid if you want to fine tune with data inside output.json inside data folder**

- install prerequisites (inside fine_tunning do `pip install -r requirements.txt` It is suggested to do it with an enviroment)
- run: `python getting_train_data` (this stage gona take some time, has to make 500 request to download pdf for datasets)


- run: `python fine_tunning.py` (This stage also takes a long time and can vary depending on the hardware you have.)


## RUN API FOR MODEL USAGE

- install prerequisites  (inside api folder do `pip install -r requirementes.txt` It is suggested to do it with an enviroment)
- run `export FLASK_APP=run.py ;flask run`

## USAGE API

make post http://localhost:5000/upload    with Multipart form:   key=file and the (doc or pdf)
