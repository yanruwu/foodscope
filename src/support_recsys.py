import os
import sys
import dotenv
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
        'ingredients(name)'
    ).execute()

    if not response.data:
        raise ValueError("No se encontraron resultados en recipe_ingredients")

    df = pd.DataFrame(response.data)
    df["ingredient_name"] = df["ingredients"].apply(lambda x: x["name"] if isinstance(x, dict) else None)
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
    print([user_ingredients])
    similaridad = cosine_similarity(user_vec, X)
    return similaridad[0]

def fetch_recipe_urls(supabase, recipe_ids):
    """Obtiene las URLs de las recetas recomendadas desde Supabase."""
    response = supabase.table("recipes").select("url").in_("id", recipe_ids).execute()
    if not response.data:
        return []
    return [item["url"] for item in response.data]

def filter_by_percentage(df, user_ingredients, threshold=0.7):
    """
    Filtra recetas que contengan al menos un porcentaje (threshold) de los ingredientes proporcionados.
    
    Args:
        df (pd.DataFrame): DataFrame con las recetas y sus ingredientes.
        user_ingredients (str): Lista de ingredientes del usuario como string.
        threshold (float): Porcentaje mínimo de coincidencia requerido (0.7 = 70%).
    
    Returns:
        pd.DataFrame: DataFrame filtrado con recetas que cumplen el umbral.
    """
    user_ingredient_set = set(user_ingredients.split())
    total_user_ingredients = len(user_ingredient_set)
    
    def match_percentage(ingredients):
        recipe_set = set(ingredients.split())
        matches = len(user_ingredient_set & recipe_set)  # Intersección
        return matches / total_user_ingredients
    
    # Calcular el porcentaje de coincidencia para cada receta
    df['match_percentage'] = df['ingredient_name'].apply(match_percentage)
    
    # Filtrar recetas que cumplen con el umbral
    filtered_df = df[df['match_percentage'] >= threshold].copy()
    return filtered_df


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
        tag_id = supabase.table('tags').select('id').eq('name', label).execute().data
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


def get_recommendations(supabase,user_ingredients):
        # Obtener y procesar datos de ingredientes
        df = fetch_recipe_ingredients(supabase)
        recipe_ingredients = preprocess_ingredients(df)

        # Vectorizar los ingredientes
        vectorizer, X = vectorize_ingredients(recipe_ingredients)

        # Calcular similitud y recomendar
        similaridad = recommend_recipes(vectorizer, X, user_ingredients)
        
        # Ajustar las similitudes con el boost
        boosted_similarities = boost_similarity_with_percentage(recipe_ingredients, user_ingredients, similaridad, alpha=1)

        # Asociar las similitudes ajustadas al DataFrame
        recipe_ingredients['boosted_similarity'] = boosted_similarities
        recipe_ingredients["similarity"] = similaridad

        recipe_ingredients = recipe_ingredients[recipe_ingredients["match_percentage"] > 0]

        # Ordenar por la similitud ajustada
        recomendaciones = recipe_ingredients.sort_values(by='boosted_similarity', ascending=False)
        # print(recomendaciones)
        # Ver las recomendaciones finales
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
