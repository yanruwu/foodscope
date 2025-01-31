import inflect
from supabase import create_client
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


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
    return df.groupby("recipe_id")["ingredient_name"].apply(lambda x: " ".join(x)).reset_index()

def vectorize_ingredients(recipe_ingredients):
    """Vectoriza los ingredientes de cada receta utilizando TF-IDF."""
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(recipe_ingredients['ingredient_name'])
    return vectorizer, X

def recommend_recipes(vectorizer, X, user_ingredients):
    """Recomienda recetas basadas en los ingredientes proporcionados por el usuario."""
    user_vec = vectorizer.transform([user_ingredients])
    # print([user_ingredients])
    similaridad = cosine_similarity(user_vec, X)
    return similaridad[0]


def boost_similarity_with_percentage(df, user_ingredients, similarities, alpha=1.0):
    """
    Ajusta las similitudes agregando un boost basado en el porcentaje de coincidencia de ingredientes.
    
    Args:
        df (pd.DataFrame): DataFrame con las recetas y sus ingredientes.
        user_ingredients (str): Lista de ingredientes del usuario como string.
        similarities (np.array): Array de similitudes calculadas (ej., similitud del coseno).
        alpha (float): Factor de importancia del porcentaje de coincidencia. A mayor alpha, mayor impacto.
    
    Returns:
        np.array: Similitudes ajustadas con el boost.
    """
    user_ingredient_set = set(user_ingredients.split())
    total_user_ingredients = len(user_ingredient_set)
    
    # Calcula el porcentaje de coincidencia para cada receta
    def match_percentage(ingredients):
        recipe_set = set(ingredients.split())
        matches = len(user_ingredient_set & recipe_set)  # Intersección
        return matches / total_user_ingredients
    
    # Aplica el porcentaje de coincidencia
    df['match_percentage'] = df['ingredient_name'].apply(match_percentage)
    
    # Ajusta la similitud sumando el boost basado en el porcentaje
    boosted_similarities = similarities + alpha * df['match_percentage'].values
    return boosted_similarities

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
        tag_id = supabase.table('tags').select('id').eq('name_norm', label).execute().data
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

def normalize_similarity(recipe_ingredients, similarities):
    """
    Normaliza la similitud dividiéndola por la raíz cuadrada del número total de ingredientes.
    """
    num_ingredients = recipe_ingredients['ingredient_name'].apply(lambda x: len(x.split()))
    normalized_similarities = similarities / (num_ingredients**0.5)  # Raíz cuadrada para suavizar el impacto
    return normalized_similarities

import numpy as np

def log_penalty_similarity(recipe_ingredients, similarities):
    """
    Aplica una penalización logarítmica para evitar que recetas con más ingredientes dominen el ranking.
    """
    num_ingredients = recipe_ingredients['ingredient_name'].apply(lambda x: len(x.split()))
    penalized_similarities = similarities / np.log1p(num_ingredients)  # log1p(x) = log(1 + x) evita dividir entre 0
    return penalized_similarities

def boost_similarity_with_coverage(df, user_ingredients, similarities, alpha=0.5):
    """
    Ajusta las similitudes para priorizar recetas donde el porcentaje de coincidencia es alto,
    no solo la cantidad absoluta de ingredientes coincidentes.
    """
    user_ingredient_set = set(user_ingredients.split())
    total_user_ingredients = len(user_ingredient_set)
    
    def match_coverage(ingredients):
        recipe_set = set(ingredients.split())
        matches = len(user_ingredient_set & recipe_set)
        return matches / max(len(recipe_set), total_user_ingredients)  # Normaliza por tamaño

    df['coverage'] = df['ingredient_name'].apply(match_coverage)
    
    # Ajustar la similitud con el boost
    boosted_similarities = similarities * (1 - alpha) + df['coverage'].values * alpha
    return boosted_similarities


def get_recommendations(supabase, raw_user_ingredients):
    # Obtener y procesar datos de ingredientes
    df = fetch_recipe_ingredients(supabase)
    recipe_ingredients = preprocess_ingredients(df)

    # Vectorizar los ingredientes
    vectorizer, X = vectorize_ingredients(recipe_ingredients)

    # Calcular similitud y recomendar
    p = inflect.engine()
    user_ingredients = [p.singular_noun(ing) if p.singular_noun(ing) else ing for ing in raw_user_ingredients.split()]
    user_ingredients = " ".join(user_ingredients)
    similarities = recommend_recipes(vectorizer, X, user_ingredients)

    # Ajustes adicionales para mejorar diversidad
    similarities = normalize_similarity(recipe_ingredients, similarities)  # Penaliza recetas largas
    similarities = log_penalty_similarity(recipe_ingredients, similarities)  # Aplica logaritmo
    similarities = boost_similarity_with_coverage(recipe_ingredients, user_ingredients, similarities, alpha=0.5)  # Prioriza cobertura

    # Asociar las similitudes ajustadas al DataFrame
    recipe_ingredients['similarity'] = similarities

    # Filtrar recetas sin coincidencias
    recipe_ingredients = recipe_ingredients[recipe_ingredients["similarity"] > 0]

    # Ordenar por la similitud ajustada
    recomendaciones = recipe_ingredients.sort_values(by='similarity', ascending=False)

    return recomendaciones


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
    
    return filtered_df
