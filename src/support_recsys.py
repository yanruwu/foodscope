import inflect
from supabase import create_client
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import numpy as np


def connect_supabase(url, key):
    return create_client(url, key)

def fetch_recipe_ingredients(supabase):
    """Obtiene los datos de la tabla recipe_ingredients desde Supabase."""
    response = supabase.table('recipe_ingredients').select(
        'recipe_id',
        'ingredients(name_norm)'
    ).execute()

    if not response.data:
        raise ValueError("No se encontraron resultados en recipe_ingredients")

    df = pd.DataFrame(response.data)
    df["ingredient_name"] = df["ingredients"].apply(lambda x: x["name_norm"] if isinstance(x, dict) else None)
    df.drop(columns=["ingredients"], inplace=True)

    return df

def preprocess_ingredients(df):
    """
    Agrupa los ingredientes por receta y los convierte en un conjunto único para evitar duplicados.
    """
    df = df.groupby("recipe_id")["ingredient_name"].apply(lambda x: " ".join(set(" ".join(x).split()))).reset_index()
    return df

def vectorize_ingredients(recipe_ingredients):
    """Vectoriza los ingredientes de cada receta utilizando TF-IDF."""
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(recipe_ingredients['ingredient_name'])
    return vectorizer, X

def compute_similarity(vectorizer, X, user_ingredients):
    """Calcula la similitud entre los ingredientes del usuario y las recetas."""
    user_vec = vectorizer.transform([user_ingredients])
    return cosine_similarity(user_vec, X)[0]

def rank_recipes(recipe_ingredients, user_ingredients, similarities):
    """
    Ordena las recetas siguiendo las reglas definidas:
    1. Recetas que solo contienen los ingredientes dados.
    2. Recetas que contienen los ingredientes dados y pocos extras.
    3. Recetas que contienen al menos un ingrediente, priorizando coincidencias.
    """
    user_ingredient_set = set(user_ingredients.split())

    # Convertir los ingredientes de cada receta en conjuntos
    recipe_ingredients["recipe_set"] = recipe_ingredients["ingredient_name"].apply(lambda x: set(x.split()))

    # Calcular métricas de coincidencia
    recipe_ingredients["matched_ingredients"] = recipe_ingredients["recipe_set"].apply(lambda x: len(x & user_ingredient_set))
    recipe_ingredients["extra_ingredients"] = recipe_ingredients["recipe_set"].apply(lambda x: len(x - user_ingredient_set))
    recipe_ingredients["missing_ingredients"] = recipe_ingredients["recipe_set"].apply(lambda x: len(user_ingredient_set - x))

    # Asociar similitudes
    recipe_ingredients["similarity"] = similarities

    # Orden de prioridad:
    # 1. Sin ingredientes extra
    # 2. Menos ingredientes extra
    # 3. Más coincidencias con el usuario
    # 4. Similitud por TF-IDF
    recipe_ingredients = recipe_ingredients[recipe_ingredients["matched_ingredients"] != 0]
    recipe_ingredients = recipe_ingredients.sort_values(
        by=["matched_ingredients","extra_ingredients", "similarity"],
        ascending=[False, True, False]
    )
    

    return recipe_ingredients

def get_recommendations(supabase, raw_user_ingredients):
    # Obtener datos de ingredientes
    df = fetch_recipe_ingredients(supabase)
    recipe_ingredients = preprocess_ingredients(df)

    # Convertir los ingredientes del usuario a singular
    p = inflect.engine()
    user_ingredients = [p.singular_noun(ing) if p.singular_noun(ing) else ing for ing in raw_user_ingredients.split()]
    user_ingredients = " ".join(user_ingredients)

    # Vectorizar y calcular similitud
    vectorizer, X = vectorize_ingredients(recipe_ingredients)
    similarities = compute_similarity(vectorizer, X, user_ingredients)

    # Ordenar y filtrar recetas
    recomendaciones = rank_recipes(recipe_ingredients, user_ingredients, similarities)

    return recomendaciones


def filter_health_labels(supabase, health_labels):
    """
    Filtra recetas por etiquetas de salud específicas.

    Esta función consulta la base de datos para encontrar recetas que coincidan con las etiquetas de salud proporcionadas.

    Args:
        supabase: Cliente de Supabase para realizar consultas a la base de datos.
        health_labels (list): Lista de strings con las etiquetas de salud a filtrar.

    Returns:
        list: Lista de IDs de recetas que coinciden con las etiquetas de salud especificadas.

    Ejemplo:
        >>> labels = ["Vegano", "Sin Gluten"]
        >>> recipe_ids = filter_health_labels(supabase, labels)
    """
    tag_ids = []
    for label in health_labels:
        tag_id = supabase.table('tags').select('id').eq('name_es', label).execute().data
        tag_ids.append(tag_id[0]["id"])
    response = [e["recipe_id"] for e in supabase.table('recipe_tags').select('recipe_id').in_('tag_id', tag_ids).execute().data]
    return response

def filter_calories(supabase, min_calories, max_calories):
    """
    Filtra recetas por rango de calorías.

    Esta función consulta la base de datos para encontrar recetas que estén dentro del rango de calorías especificado.

    Args:
        supabase: Cliente de Supabase para realizar consultas a la base de datos.
        min_calories (int): Calorías mínimas para filtrar.
        max_calories (int): Calorías máximas para filtrar.

    Returns:
        list: Lista de IDs de recetas que están dentro del rango de calorías especificado.

    Ejemplo:
        >>> min_cal = 100
        >>> max_cal = 500
        >>> recipe_ids = filter_calories(supabase, min_cal, max_cal)
    """
    response = [e["id"] for e in supabase.table('recipes').select('id').gte('calories', min_calories).lte('calories', max_calories).execute().data]
    return response


def get_filtered_recommendations(ingredients, url, key, health_labels, min_calories, max_calories):
    """
    Gets recipe recommendations filtered by health labels and calories.
    
    Args:
        ingredients (str): Space-separated string of ingredients
        url (str): Supabase URL
        key (str): Supabase key
        health_labels (list): List of health labels to filter by
        min_calories (int): Minimum calories
        max_calories (int): Maximum calories
        
    Returns:
        pd.DataFrame: Filtered recommendations dataframe
    """
    # Connect to Supabase
    supabase = connect_supabase(url, key)
    
    # Get initial recommendations
    df = get_recommendations(supabase, ingredients)

    # Filter by health labels
    if not health_labels:
        filter_label_df = df
    else:
        filter_label_df = df[df["recipe_id"].isin(filter_health_labels(supabase, health_labels))]
    
    # Filter by calories
    calories_filter = filter_calories(supabase, min_calories, max_calories)
    filtered_df = filter_label_df[filter_label_df["recipe_id"].isin(calories_filter)]
    # print(filtered_df.values)
    return filtered_df
