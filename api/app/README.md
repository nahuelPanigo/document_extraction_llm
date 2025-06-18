3 differents services:

- extractor_service: receives a document as a request that can be 'pdf, word, doc or ppt' and extracts the metadata necessary for uploading to the sedici repository.
- llm_service_led: receives a document as a request that can be 'pdf, word, doc or ppt' and extracts the metadata necessary for uploading to the sedici repository.
- orchestrator: receives a document as a request that can be 'pdf, word, doc or ppt' and extracts the metadata necessary for uploading to the sedici repository.

## How to run

### Requirements


- Docker Compose: just run `docker-compose up` or you can run specific services with `docker-compose up extractor_service` or the name of the service you want to run (e.g. `docker-compose up orchestrator`, `docker-compose up llm_service_led`) for each service you have to configure the environment variables in the `.env` file see example in `.env.example` and also in the `docker-compose.yml` file for llm_sercive  the model and configurations.

- Docker run with nvidia-container-toolkit: just run `docker run --gpus all -it -v /path/to/your/data:/data -p 8000:8000 orchestrator` or you can run specific services with `docker run --gpus all -it -v /path/to/your/data:/data -p 8000:8000 extractor_service` or the name of the service you want to run (e.g. `docker run --gpus all -it -v /path/to/your/data:/data -p 8000:8000 orchestrator`, `docker run --gpus all -it -v /path/to/your/data:/data -p 8000:8000 llm_service_led`) for each service you have to configure the environment variables in the `.env` file see example in `.env.example` and also in the `docker-compose.yml` file for llm_sercive  the model and configurations.

- Python 3.10 (with out containers): run `uvicorn app.main:app --reload` this you have to configure the enviroments that are in the `.env` file see example in `.env.example` and also in the `docker-compose.yml` file for llm_sercive  the model and configurations. also you need to install the requirements in the `requirements.txt` file with `pip install -r requirements.txt`

1.