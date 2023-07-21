import openai
import os
import utils
import data_base.utils as db_utils
openai.api_key = ""
openai.api_base = f"http://127.0.0.1:5000"

def list_files(startpath):
    rez = ''
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        rez += '{}{}/'.format(indent, os.path.basename(root))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            rez += '{}{}'.format(subindent, f)

    return rez


def read_file(file_location):
    with open(file_location, "r", encoding="utf-8") as file:
        data = file.read()

    return data


def gpt_answer(message_log):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=message_log,
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
        {"role": "system", "content": utils.prompts["start_prompt"]},
        {"role": "user", "content": input_str}
    ]
    raw_response = gpt_answer(dialog_data)

    return raw_response


if __name__ == '__main__':
    ask = "где анины кисточки?"
    print(ask)
    files = db_utils.get_tree("12")
    file_location = chat_gpt_query(utils.prompts["ask_file_location"].format(ask, files))
    print(file_location)
    data = db_utils.get_notes_from_location("12", file_location)
    data = chat_gpt_query(utils.prompts["read_file"].format(ask, file_location, data))
    print(data)
    list_files("data")
