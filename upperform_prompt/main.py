
from constants import PROMPT_TESIS, PROMPT_ARTICULO,PROMPT_UPPERFORM,PDF_FOLDER,JSON_FOLDER,DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED
from utils.text_extraction.read_and_write_files import read_data_json,write_to_json
from upperform_prompt.qwen_consumer import consume_qewn
from upperform_prompt.genai_consumer import consume_llm
import os
import logging
from upperform_prompt.loss_diff_compare import get_diff

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)




def get_metadata_and_text(type):
    dict = read_data_json(JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED, "utf-8")
    for col in dict.values():
        for item in col:
            if item["dc.type"] == type:
                metadata = {x: y for x, y in item.items() if x != "original_text" and x != "dc.type" and x != "id" and x is not None}
                text = item["original_text"]
                return metadata, text

def consume_and_compare(prompt,metadata,results,prompts_results):
    for i in range(10):
        response = consume_qewn(input)
        input = f"""<INSTRUCTS>{PROMPT_UPPERFORM} </INSTRUCTS>  
            - <ACTUAL_PROMPT> {prompt} </ACTUAL_PROMPT>
            - <RESULTS_OBTAINED> {response} </RESULTS_OBTAINED>
            - <EXPECTED_RESULTS> {metadata}  </EXPECTED_RESULTS>
            """
        prompt = consume_llm(input)
        dif = get_diff(metadata,response)
        results.append({"response": response, "dif": dif})
        prompts_results.append(prompt)
    return prompt,dif



def main():
    prompts_results = []
    prompts_filenames = "prompts.json"

    results = []
    results_filenames = "results.json"

    logger.info("running upperform prompt for article")
    metadata, text = get_metadata_and_text("Articulo")
    text = text[:4000]
    input = f"""{PROMPT_ARTICULO}{text}"""
    response = consume_qewn(input)
    print(f"response: {response}")

    input = f"""<INSTRUCTS>{PROMPT_UPPERFORM} </INSTRUCTS>  
            - <ACTUAL_PROMPT> {prompt} </ACTUAL_PROMPT>
            - <RESULTS_OBTAINED> {response} </RESULTS_OBTAINED>
            - <EXPECTED_RESULTS> {metadata}  </EXPECTED_RESULTS>
            """
    prompt = consume_llm(input)
    
    print(f"prompt: {prompt}")

    # logger.info(f"final diference between prompt and response in article: {dif}")
    # logger.info(f"final prompt for article: {prompt}")

    # logger.info("running upperform prompt for tesis")
    # metadata, text = get_metadata_and_text("Tesis")
    # text = text[:4000]
    # prompt,dif =consume_and_compare(PROMPT_TESIS,metadata,results,prompts_results)

    # logger.info(f"final diference between prompt and response in tesis: {dif}")
    # logger.info(f"final prompt for tesis: {prompt}")


    # write_to_json(JSON_FOLDER / prompts_filenames,prompts_results,"utf-8")
    # write_to_json(JSON_FOLDER / results_filenames,results,"utf-8")


if __name__ == "__main__":
    main()