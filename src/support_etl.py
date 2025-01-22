import requests
import os
import pandas as pd
from tqdm import tqdm

import dotenv
import sys
sys.path.append("..")
dotenv.load_dotenv()

from deep_translator import GoogleTranslator

def translate_es_en(text):
    return GoogleTranslator(source='es', target='en').translate(text)

def translate_en_es(text):
    return GoogleTranslator(source='en', target='es').translate(text)

def get_nutrients(ing_list, serving_size):
    """
    Obtiene datos nutricionales de una lista de ingredientes usando la API de EDAMAM.

    Args:
        ing_list (list): Lista de ingredientes en formato de texto.
        serving_size (int): Tamaño de porción para ajustar los valores nutricionales.

    Returns:
        tuple: Una tupla con dos elementos:
            - pd.DataFrame: DataFrame con los nutrientes de cada ingrediente, incluyendo:
                - 'Ingredient' (str): Nombre del ingrediente.
                - 'Weight (g)' (float): Peso en gramos del ingrediente ajustado al tamaño de porción.
                - 'Calories (kcal)' (float): Calorías por porción.
                - 'Protein (g)' (float): Proteína por porción.
                - 'Fat (g)' (float): Grasas por porción.
                - 'Carbohydrates (g)' (float): Carbohidratos por porción.
                - 'Sugar (g)' (float): Azúcar por porción.
                - 'Fiber (g)' (float): Fibra por porción.
            - dict: Diccionario con los nutrientes totales y etiquetas de salud en formato:
                - {"Energy (kcal)": ..., "Protein (g)": ..., "HealthLabels": [...]}

    Raises:
        HTTPError: Si hay un problema en la solicitud a la API de EDAMAM.
    """
    url = "https://api.edamam.com/api/nutrition-details"

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "ingr": ing_list
    }

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

            # Extraer nutrientes ajustados por tamaño de porción
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

        # Crear el diccionario con los nutrientes totales y sus etiquetas
        recipe_summary = {}
        for key, label in relevant_nutrients.items():
            nutrient_data = nutrition_data.get("totalNutrients", {}).get(key, {})
            recipe_summary[label] = nutrient_data.get("quantity", 0)
        
        # Agregar etiquetas de salud al diccionario
        recipe_summary["HealthLabels"] = nutrition_data.get("healthLabels", [])
        recipe_summary["weight"] = total_weight
        recipe_summary["Serving Size"] = serving_size

        return nutrients_df, recipe_summary

    else:
        print("Error:", response.status_code, response.json())
        return response.status_code, response.status_code
    
import psycopg2
import json

# Configuración de conexión
DB_PARAMS = {
    "dbname": "FoodScope",
    "user": "postgres",
    "password": "admin",
    "host": "localhost",  # Cambia según tu entorno
    "port": 5432
}

# Conectar a la base de datos
def connect_db():
    conn = psycopg2.connect(**DB_PARAMS)
    return conn

import hashlib

def generate_ingredient_id(name):
    """
    Genera un ID único para un ingrediente basado en su nombre.

    Args:
        name (str): Nombre del ingrediente.

    Returns:
        int: ID único generado como hash.
    """
    return int(hashlib.md5(name.encode()).hexdigest()[:8], 16)


def get_or_create_ingredient(conn, ingredient_name, nutrients, name_en, name_es):
    """
    Busca un ingrediente por nombre o lo inserta si no existe.

    Args:
        conn: Conexión a la base de datos.
        ingredient_name (str): Nombre del ingrediente.
        nutrients (dict): Nutrientes del ingrediente (por 100 g): 'calories', 'proteins', 'carbs', 'fats'.

    Returns:
        int: ID del ingrediente.
    """
    with conn.cursor() as cur:
        # Buscar el ingrediente por nombre
        cur.execute("SELECT id FROM ingredients WHERE name = %s;", (ingredient_name,))
        result = cur.fetchone()

        if result:
            # Si existe, devolver el ID
            return result[0]
        else:
            # Generar un nuevo ID para el ingrediente
            ingredient_id = generate_ingredient_id(ingredient_name)
            
            # Insertar el nuevo ingrediente
            cur.execute(
                """
                INSERT INTO ingredients (id, name, calories, proteins, carbs, fats, sugars, fiber, name_en, name_es)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    ingredient_id,
                    ingredient_name,
                    float(nutrients.get("calories", 0.0)),
                    float(nutrients.get("protein", 0.0)),
                    float(nutrients.get("carbs", 0.0)),
                    float(nutrients.get("fat", 0.0)),
                    float(nutrients.get("sugar", 0.0)),
                    float(nutrients.get("fiber", 0.0)),
                    name_en,
                    name_es
                )
            )
            conn.commit()
            return ingredient_id
        
def insert_recipe(conn, recipe_name, name_en, name_es, recipe_url, weight, nutrients, serving_size):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO recipes (name, name_en, name_es, url, weight, calories, proteins, carbs, fats, sugars, fiber, servings)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (
            recipe_name,
            name_en,
            name_es,
            recipe_url,
            weight,
            float(nutrients.get("calories", 0))/serving_size,
            float(nutrients.get("protein", 0))/serving_size,
            float(nutrients.get("carbs", 0))/serving_size,
            float(nutrients.get("fat", 0))/serving_size,
            float(nutrients.get("sugar", 0))/serving_size,
            float(nutrients.get("fiber", 0))/serving_size,
            serving_size
            )
        )
        recipe_id = cur.fetchone()[0]
        conn.commit()
        return recipe_id

def insert_ingredient_recipe(conn, recipe_id, ingredient_id, amount):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO recipe_ingredients (recipe_id, ingredient_id, amount)
            VALUES (%s, %s, %s);
            """,
            (recipe_id, ingredient_id, amount)
        )
        conn.commit()

