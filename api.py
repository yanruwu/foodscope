from flask import Flask, request, jsonify
import os
import dotenv
from PIL import Image
import numpy as np
from src.support_cv import image_feed
from src.support_etl import get_nutrients, get_supabase_client, process_recipes
from src.support_recsys import get_filtered_recommendations

dotenv.load_dotenv()


app = Flask(__name__)

# Conectar a Supabase
supabase = get_supabase_client()

@app.route('/')
def home():
    return jsonify({"message": "API de procesamiento de recetas y recomendacion"})

@app.route('/process-image', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({"error": "No se encontró imagen en la solicitud"}), 400
    
    image_file = request.files['image']
    image_pil = Image.open(image_file)
    detected_items = image_feed(image_pil)
    return jsonify({"detected_items": detected_items})

@app.route('/get-nutrients', methods=['POST'])
def get_nutritional_info():
    data = request.get_json()
    ingredients = data.get('ingredients', [])
    serving_size = data.get('serving_size', 1)
    
    nutrients_df, summary = get_nutrients(ingredients, serving_size)
    return jsonify({
        "nutrients": nutrients_df.to_dict(orient='records'),
        "summary": summary
    })

@app.route('/process-recipes', methods=['POST'])
def process_recipes_api():
    data = request.get_json()
    file_path = data.get('file_path')
    leftoff_path = data.get('leftoff_path')
    
    if not file_path or not leftoff_path:
        return jsonify({"error": "Faltan parámetros file_path o leftoff_path"}), 400
    
    process_recipes(file_path, leftoff_path)
    return jsonify({"message": "Procesamiento de recetas completado"})

@app.route('/recommend-recipes', methods=['POST'])
def recommend_recipes():
    data = request.get_json()
    ingredients = data.get('ingredients', "")
    health_labels = data.get('health_labels', [])
    min_calories = data.get('min_calories', 0)
    max_calories = data.get('max_calories', 10000)
    
    recommendations = get_filtered_recommendations(
        ingredients,
        url = "https://zrhsejedrpoqcyfvfzsr.supabase.co",
        key = os.getenv("db_API_pass"),
        health_labels = health_labels,
        min_calories = min_calories,
        max_calories = max_calories
    )

    recommendations = recommendations["recipe_id"].reset_index(drop = True)
    return jsonify(recommendations.to_dict())

if __name__ == '__main__':
    app.run(debug=True)
