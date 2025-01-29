import requests
import os
import pandas as pd
import inflect
import time
import json  
import dotenv
import sys
sys.path.append("..")
dotenv.load_dotenv()

from deep_translator import GoogleTranslator
from supabase import create_client, Client

def translate_es_en(text):
    return GoogleTranslator(source='es', target='en').translate(text)

def translate_en_es(text):
    return GoogleTranslator(source='en', target='es').translate(text)

def get_nutrients(ing_list, serving_size):
    """
    Obtiene datos nutricionales de una lista de ingredientes usando la API de EDAMAM.

    Args:
        ing_list (list): Lista de ingredientes en formato de texto (en inglés).
        serving_size (int): Tamaño de porción para ajustar valores nutricionales.

    Returns:
        tuple: (pd.DataFrame, dict)
            - DataFrame: detalle de nutrientes por ingrediente.
            - dict: resumen de nutrientes totales y etiquetas de salud.
    """
    url = "https://api.edamam.com/api/nutrition-details"
    headers = { "Content-Type": "application/json" }
    data = { "ingr": ing_list }

    response = requests.post(
        url,
        headers=headers,
        params={"app_id": os.getenv('edamam_session_id'), "app_key": os.getenv('edamam_api_key')},
        json=data
    )

    if response.status_code == 200:
        nutrition_data = response.json()
        
        # Extraer nutrientes de cada ingrediente
        nutrient_list = []
        for ingredient in nutrition_data.get("ingredients", []):
            parsed_data = ingredient.get("parsed", [])
            if not parsed_data:
                continue
            
            ingredient_data = parsed_data[0]
            ingredient_name = ingredient_data.get("foodMatch", "Unknown")
            nutrients = ingredient_data.get("nutrients", {})
            weight = ingredient_data.get("weight", 0)
            total_weight = nutrition_data.get("totalWeight", 0)

            # Extraer nutrientes
            calories = nutrients.get("ENERC_KCAL", {}).get("quantity", 0)
            protein = nutrients.get("PROCNT", {}).get("quantity", 0)
            fat = nutrients.get("FAT", {}).get("quantity", 0)
            carbs = nutrients.get("CHOCDF", {}).get("quantity", 0)
            fiber = nutrients.get("FIBTG", {}).get("quantity", 0)
            sugar = nutrients.get("SUGAR", {}).get("quantity", 0)

            nutrient_list.append({
                "Ingredient": ingredient_name,
                "Weight (g)": weight,
                "calories": calories,
                "protein": protein,
                "fat": fat,
                "carbs": carbs,
                "sugar": sugar,
                "fiber": fiber,
            })

        nutrients_df = pd.DataFrame(nutrient_list)

        # Nutrientes relevantes que se deben incluir en el resumen
        relevant_nutrients = {
            "ENERC_KCAL": "calories",
            "PROCNT": "protein",
            "FAT": "fat",
            "CHOCDF": "carbs",
            "SUGAR": "sugar",
            "FIBTG": "fiber"
        }

        # Crear el diccionario con los nutrientes totales
        recipe_summary = {}
        for key, label in relevant_nutrients.items():
            nutrient_data = nutrition_data.get("totalNutrients", {}).get(key, {})
            recipe_summary[label] = nutrient_data.get("quantity", 0)

        # Agregar etiquetas de salud
        recipe_summary["HealthLabels"] = nutrition_data.get("healthLabels", [])
        recipe_summary["weight"] = total_weight
        recipe_summary["Serving Size"] = serving_size

        return nutrients_df, recipe_summary
    else:
        print("Error:", response.status_code, response.json())
        return response.status_code, response.status_code


# Supabase client global (o puedes instanciarlo donde más te convenga)
def get_supabase_client() -> Client:
    """
    Retorna la instancia de Supabase con las credenciales de entorno.
    """
    url = "https://zrhsejedrpoqcyfvfzsr.supabase.co"
    key = os.getenv("db_API_pass")
    return create_client(url, key)

import hashlib

def generate_ingredient_id(name: str) -> int:
    """
    Genera un ID único para un ingrediente basado en su nombre utilizando MD5.
    """
    name = name.strip()
    return int(hashlib.md5(name.encode()).hexdigest()[:8], 16)


def get_or_create_ingredient(supabase: Client, ingredient_name: str, nutrients: dict, name_en: str, name_es: str) -> int:
    """
    Busca un ingrediente por nombre o lo inserta si no existe, retornando su ID.
    """
    # 1. Verificar si ya existe en la tabla
    existing = supabase.table("ingredients").select("id").eq("name", ingredient_name).execute()
    p = inflect.engine()
    if existing.data and len(existing.data) > 0:
        # Ya existe
        return existing.data[0]["id"]
    else:
        # 2. Insertar el nuevo ingrediente
        ingredient_id = generate_ingredient_id(ingredient_name)
        insert_data = {
            "id": ingredient_id,
            "name": ingredient_name,
            "calories": float(nutrients.get("calories", 0.0)),
            "proteins": float(nutrients.get("protein", 0.0)),
            "carbs": float(nutrients.get("carbs", 0.0)),
            "fats": float(nutrients.get("fat", 0.0)),
            "sugars": float(nutrients.get("sugar", 0.0)),
            "fiber": float(nutrients.get("fiber", 0.0)),
            "name_en": name_en,
            "name_es": name_es,
            "name_norm" : p.singular_noun(ingredient_name) if p.singular_noun(ingredient_name) else ingredient_name
        }
        supabase.table("ingredients").insert(insert_data).execute()
        return ingredient_id


def insert_recipe(
    supabase: Client,
    recipe_name: str,
    name_en: str,
    name_es: str,
    recipe_url: str,
    weight: float,
    nutrients: dict,
    serving_size: int
) -> int:
    """
    Inserta una nueva receta en la tabla 'recipes' y retorna su ID.
    """
    # Insert
    insert_data = {
        "name": recipe_name,
        "name_en": name_en,
        "name_es": name_es,
        "url": recipe_url,
        "weight": weight,
        "calories": float(nutrients.get("calories", 0)) / serving_size,
        "proteins": float(nutrients.get("protein", 0)) / serving_size,
        "carbs": float(nutrients.get("carbs", 0)) / serving_size,
        "fats": float(nutrients.get("fat", 0)) / serving_size,
        "sugars": float(nutrients.get("sugar", 0)) / serving_size,
        "fiber": float(nutrients.get("fiber", 0)) / serving_size,
        "servings": serving_size
    }
    response = supabase.table("recipes").insert(insert_data).execute()

    # Supabase no siempre retorna el registro insertado (dependiendo de la configuración),
    # si tu tabla 'recipes' tiene la columna 'url' única, podemos hacer un select:
    if response.data and len(response.data) > 0:
        # Si configuraste return=representation (o similar) en el Policy, data debería traer el objeto insertado
        return response.data[0]["id"]
    else:
        # Si no vino en data, hacemos un select por url (asumiendo que es única):
        result = supabase.table("recipes").select("id").eq("url", recipe_url).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]["id"]
        return None  # Manejo de error en caso de no encontrar


def insert_ingredient_recipe(supabase: Client, recipe_id: int, ingredient_id: int, amount: float):
    """
    Inserta relación receta-ingrediente en la tabla 'recipe_ingredients'.
    """
    supabase.table("recipe_ingredients").insert({
        "recipe_id": recipe_id,
        "ingredient_id": ingredient_id,
        "amount": amount
    }).execute()


def insert_steps_from_jsonl(supabase: Client, jsonl: pd.DataFrame, index: int):
    """
    Inserta los pasos de elaboración en la tabla 'steps'.
    """
    recipe_url = jsonl.loc[index, "url"]

    # Recuperar ID de la receta por URL (asumiendo que es única)
    recipe_found = supabase.table("recipes").select("id").eq("url", recipe_url).execute()
    if not recipe_found.data:
        return  # Si no existe la receta, no insertamos pasos

    recipe_id = recipe_found.data[0]["id"]
    steps_es = jsonl.loc[index, "instrucciones"]
    steps_en = translate_es_en(steps_es)  # se traduce a inglés

    supabase.table("steps").insert({
        "recipe_id": recipe_id,
        "description": steps_es,       # descripción original
        "description_es": steps_es,    # redundante: texto en español
        "description_en": steps_en     # texto en inglés
    }).execute()


def insert_tags(supabase: Client, recipe_id: int, health_labels: list):
    """
    Inserta etiquetas (tags) en la tabla 'tags' y su relación en 'recipe_tags'.
    """
    for label in health_labels:
        label_lower = label.lower().replace("_", " ")

        # 1. Buscar tag
        existing_tag = supabase.table("tags").select("id").eq("name", label_lower).execute()
        if existing_tag.data and len(existing_tag.data) > 0:
            tag_id = existing_tag.data[0]["id"]
        else:
            # 2. Crear tag
            new_tag = supabase.table("tags").insert({
                "name": label_lower,
                "name_en": label_lower,
                "name_es": translate_en_es(label_lower).lower()
            }).execute()

            if new_tag.data and len(new_tag.data) > 0:
                tag_id = new_tag.data[0]["id"]
            else:
                # Si no viene el ID en la respuesta, recuperamos el ID seleccionando por nombre
                tag_res = supabase.table("tags").select("id").eq("name", label_lower).execute()
                tag_id = tag_res.data[0]["id"] if tag_res.data else None
        
        # 3. Insertar relación recipe-tag
        if tag_id:
            supabase.table("recipe_tags").insert({
                "recipe_id": recipe_id,
                "tag_id": tag_id
            }).execute()


def process_recipes(file_path: str, leftoff_path: str):
    """
    Procesa recetas desde un archivo JSONL y almacena en Supabase.
    - file_path: ruta al archivo JSONL con las recetas.
    - leftoff_path: ruta al archivo JSON con la posición de la última receta procesada.
    """
    # 1. Carga de datos
    dap = pd.read_json(file_path, lines=True)
    with open(leftoff_path, 'r', encoding='utf-8') as file:
        dap_leftoff = json.load(file)

    # 2. Instancia global de Supabase
    supabase = get_supabase_client()

    # 3. Iterar recetas
    for i in range(1 + dap_leftoff["Position"], len(dap)):
        ingredients = dap["ingredientes"].loc[i]
        # Unir nombre, cantidad, unidad
        resultados = [
            " ".join(filter(None, [str(c) if c is not None else None, u, n]))
            for n, c, u in zip(ingredients['nombre'], ingredients['cantidad'], ingredients['unidad'])
        ]
        en_ingredients = [translate_es_en(e) for e in resultados]        
        serving = dap["raciones"].loc[i]

        # Obtener info nutricional de la API de Edamam
        nut_info, recipe_sum = get_nutrients(en_ingredients, int(serving))
        if isinstance(nut_info, int) and nut_info != 555:
            print("Error en la API Edamam:", nut_info)
            break  # Detenemos si hay error distinto a 555
        elif isinstance(nut_info, int) and nut_info == 555:
            # Guardar la posición actual y continuar
            json.dump(dap_leftoff, open(leftoff_path, "w"))
            continue

        # Actualizar posición en el archivo de progreso
        dap_leftoff["Position"] = i

        # Filtrar ingredientes con peso > 0
        filtered_nut_info = nut_info[nut_info["Weight (g)"] > 0].copy()
        columns_to_normalize = filtered_nut_info.columns[2:]  # desde 'calories' en adelante

        # Normalizar a cada 100 g
        filtered_nut_info[columns_to_normalize] = (
            filtered_nut_info[columns_to_normalize]
            .div(filtered_nut_info["Weight (g)"], axis=0)*100
        )

        # Insertar receta
        recipe_id = insert_recipe(
            supabase,
            dap["titulo"].loc[i],
            translate_es_en(dap["titulo"].loc[i]),
            dap["titulo"].loc[i],
            dap["url"].loc[i],
            recipe_sum.get("weight"),
            recipe_sum,
            int(serving)
        )
        
        # Insertar tags
        insert_tags(supabase, recipe_id=recipe_id, health_labels=recipe_sum.get("HealthLabels", []))
        # Insertar pasos de elaboración
        insert_steps_from_jsonl(supabase, dap, i)

        # Insertar ingredientes (relación muchos a muchos)
        for j in filtered_nut_info.index:
            ingredient_id = get_or_create_ingredient(
                supabase,
                filtered_nut_info.loc[j].get("Ingredient").lower(),
                filtered_nut_info.loc[j],
                filtered_nut_info.loc[j].get("Ingredient").lower(),
                translate_en_es(filtered_nut_info.loc[j].get("Ingredient")).lower()
            )
            insert_ingredient_recipe(
                supabase,
                recipe_id,
                ingredient_id,
                float(filtered_nut_info.loc[j].get("Weight (g)"))
            )

        # Guardar la posición actual en el JSON
        json.dump(dap_leftoff, open(leftoff_path, "w"))
        time.sleep(2)
