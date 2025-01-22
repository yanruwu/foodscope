import sys
import os
import pandas as pd

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from src.support_etl import *
dap = pd.read_json(r'recetas_scrapper\dap.jsonl', lines=True)

print("Translating ingredients...")
for i in range(len(dap)):
    ingredients = dap["ingredientes"].loc[i]
    resultados = [
        f"{n} {c} {u}".strip() if u else f"{n} {c}".strip()
        for n, c, u in zip(ingredients['nombre'], ingredients['cantidad'], ingredients['unidad'])
        if c is not None
    ]
    en_ingredients = [translate_es_en(e) for e in resultados]
    print(en_ingredients)
    serving = dap["raciones"].loc[i]
    break

print("Getting nutrients...")

print(get_nutrients(en_ingredients, int(serving)))


print("End")