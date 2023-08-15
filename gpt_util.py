import os
import json

import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_TOKEN")

# Если используете прокси для доступа к openai -
# раскоментируйте следующую строку и отредактируйте в соответствии своими данными
# openai.api_base = f"http://127.0.0.1:5000"

import data_base.utils as db_utils

prompts = {}

with open("prompts.json", "r", encoding="utf-8") as file:
    prompts = json.load(file)


def ask_gpt(context):
    """
    Выполняет запрос по апи к ChatGPT
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=context,
        max_tokens=256,
        temperature=0.6,
        top_p=1,
        stop=None
    )

    for choice in response.choices:
        if "text" in choice:
            return choice.text

    return response.choices[0].message.content


def chat_gpt_query(input_str):
    """ Выполняет запрос заданного текста к CHATGPT """

    dialog_data = [
        {"role": "system", "content": prompts["start_prompt"]},
        {"role": "user", "content": input_str}
    ]
    raw_response = ask_gpt(dialog_data)

    return raw_response
