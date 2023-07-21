import json

prompts = {}

with open("prompts.json", "r", encoding="utf-8") as file:
    prompts = json.load(file)
