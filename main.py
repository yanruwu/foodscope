import torch
# Guarda la función original
_original_getattr = torch.classes.__getattr__

def safe_getattr(name):
    if name == "__path__":
        # Devuelve una lista vacía o algún valor dummy
        return []
    return _original_getattr(name)

torch.classes.__getattr__ = safe_getattr
import streamlit as st
import os
import cv2
import dotenv
import base64
import numpy as np
import random
import streamlit_tags as stt

# Importa tus módulos o funciones personalizadas
from src.support_cv import image_feed
from src.support_recsys import connect_supabase, get_filtered_recommendations
from src.support_etl import translate_es_en, translate_en_es

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def filter_by_tags(supabase, recipe_list, selected_tag_names, tag_data):
    if not selected_tag_names:
        return recipe_list
    tag_map = {t["name_es"]: t["id"] for t in tag_data}
    selected_tag_ids = [tag_map[x] for x in selected_tag_names if x in tag_map]
    if not selected_tag_ids:
        return []
    
    # Cargar la tabla recipe_tags
    rec_tag_data = supabase.table("recipe_tags").select("recipe_id, tag_id").execute().data
    
    # index: rec_id -> set(tag_ids)
    from collections import defaultdict
    rec_to_tags = defaultdict(set)
    for row in rec_tag_data:
        rec_to_tags[row["recipe_id"]].add(row["tag_id"])
    
    # Filtramos
    filtered = []
    for r in recipe_list:
        rid = r["id"]
        if rid in rec_to_tags:
            # "al menos uno" => intersection
            if rec_to_tags[rid].intersection(selected_tag_ids):
                filtered.append(r)
    return filtered


# ====================================================
# CONFIGURACIÓN DE STREAMLIT
# ====================================================
st.set_page_config(page_title="FoodScope - Identifica ingredientes y descubre recetas",
                    page_icon="🧀",
                    layout="wide"
)

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
<style>
html, body, .stAppViewContainer, .stAppViewContainer * {
    font-family: 'Poppins', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)


meta_description = """
    <meta name="description" content="Explora ingredientes y encuentra recetas con FoodScope. Tu asistente inteligente para identificar productos y mejorar tu cocina.">
    <meta name="keywords" content="recetas, ingredientes, IA, reconocimiento de alimentos, comida, cocina inteligente, FoodScope">
    <meta name="author" content="FoodScope Team">
"""
st.markdown(meta_description, unsafe_allow_html=True)

# ====================================================
# CSS PERSONALIZADO
# ====================================================
st.markdown("""
<style>
/* Ocultamos el header por defecto de Streamlit para que no compita con nuestro topbar */
header[data-testid="stHeader"] {
    display: none;
}


/* Estilos personalizados para el Topbar y elementos específicos */
.topbar {
    position: sticky;
    top: 0;
    z-index: 9999;
    background-color: #F26722;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    padding: 0.8rem 2rem;
    border-radius: 1rem;
    margin-bottom: 1rem;
    color : white;
}

.topbar-logo {
    display: flex;
    align-items: center;
    font-weight: bold;
    font-size: 1.7rem;
    /* Usamos 'inherit' para tomar el color definido por el tema */
    color: inherit;
    margin-right: auto;
}
.topbar-logo img {
    height: 40px;
    margin-right: 10px;
}

.topbar-right {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    flex-wrap: wrap;
    justify-content: flex-end;
}

.topbar-right a {
    color: inherit;
    text-decoration: none;
    font-weight: 600;
    font-size: 1.2rem;
}
.topbar-right a:hover {
    text-decoration: underline;
}

@media screen and (max-width: 450px) {
    .topbar {
        padding: 0.6rem 1rem;
    }
    .topbar-right a {
        font-size: 0.9rem;
    }
}

/* Tabs estilos */
[data-testid="stHorizontalBlock"] > div {
    border: none !important;
    background-color: transparent !important;
}
div [data-testid="stHorizontalBlock"] button[kind="tab"] {
    background-color: transparent !important;
    color: inherit !important;
    border: 1px solid #444 !important;
}
div [data-testid="stHorizontalBlock"] button[aria-selected="true"] {
    background-color: #F26722 !important;
    color: #FFF !important;
    border: none !important;
}

/* Center the camera container */
.camera-container {
    margin: 0 auto;
    width: 100vw;
    max-width: 600px;
    height: auto;
}

@media screen and (max-width: 768px) {
    .camera-container {
        max-width: 100vw;
        height: 100vh;
    }
}

.camera-container .stCamera {
    width: 100% !important;
    height: 100vh !important;
    object-fit: cover;
}

/* Botones en naranja */
div.stButton > button {
    background-color: #F26722 !important;
    color: #fff !important;
    border: none;
    border-radius: 6px;
    font-weight: bold;
    cursor: pointer;
}
div.stButton > button:hover {
    background-color: #D65A1A !important;
}

/* Toggle (Activar cámara) */
.stToggleSwitch label[data-baseweb="checkbox"] > div {
    background-color: #F26722 !important;
}
            
div[data-baseweb="tab-highlight"] {
    background-color: #F26722 !important;
}

/* Target the slider track */
div[data-baseweb="slider"] div[role="slider"] {
    background: #F26722 !important;
}

/* Target the submit button */
button[data-testid="stBaseButton-secondaryFormSubmit"] {
    background-color: #F26722 !important;
    color: white !important;
    border-radius: 8px !important;
    border: 2px solid #fab582 !important;
}

button[data-testid="stBaseButton-secondaryFormSubmit"]:hover {
    background-color: #fab582 !important;
}
            


</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Aplica el fondo anaranjado pastel al contenedor del expander y a sus partes internas */
div.stExpander[data-testid="stExpander"] details,
div.stExpander[data-testid="stExpander"] summary,
div.stExpander[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    background-color: #FFE0B2 !important;
    border: 1px solid #fab582 !important;
    border-radius: 1rem;
}

/* Si deseas cambiar también el color del texto dentro del expander, puedes agregar: */
div.stExpander[data-testid="stExpander"] p,
div.stExpander[data-testid="stExpander"] span,
div.stExpander[data-testid="stExpander"] a {
    color: #000000 !important;
}
</style>
""", unsafe_allow_html=True)


# ====================================================
# CONEXIÓN SUPABASE Y SESIÓN
# ====================================================
dotenv.load_dotenv()
url = "https://zrhsejedrpoqcyfvfzsr.supabase.co"
key = os.getenv("db_API_pass")
supabase = connect_supabase(url, key)

@st.cache_data
def get_food_options():
    food_options = supabase.table("ingredients").select("name_es", "name_en").execute().data
    return food_options

food_options = get_food_options()

if 'detection_list' not in st.session_state:
    st.session_state.detection_list = []
if 'last_uploaded_image' not in st.session_state:
    st.session_state.last_uploaded_image = None
if 'selected_ingredients' not in st.session_state:
    st.session_state.selected_ingredients = []
if 'pagina' not in st.session_state:
    st.session_state["pagina"] = 0

if 'active_tab_idx' not in st.session_state:
    st.session_state.active_tab_idx = 0

if "recipe_data" not in st.session_state:
    st.session_state["recipe_data"] = []

# ====================================================
# FUNCIÓN PARA CARGAR LOGO EN BASE64
# ====================================================
def load_logo_base64(path: str = "logo.png") -> str:
    """Lee un archivo .png en binario y retorna su contenido en base64."""
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")

# ====================================================
# RENDER TOPBAR (con LOGO base64)
# ====================================================
def render_topbar():
    encoded_logo = ""
    if os.path.exists("logo_transparent.png"):
        with open("logo_transparent.png", "rb") as f:
            encoded_logo = base64.b64encode(f.read()).decode("utf-8")

    if encoded_logo:
        logo_html = f'<img src="data:image/png;base64,{encoded_logo}" alt="Logo" />'
    else:
        logo_html = ""

    topbar_html = f"""
    <div class="topbar">
        <div class="topbar-logo">
            {logo_html}
            FoodScope
        </div>
        <div class="topbar-right">
            <a href="https://github.com/yanruwu/foodscope/issues/new?template=Blank+issue">Contacto</a>
            <a href="https://github.com/yanruwu/foodscope" target="_blank">Acerca de</a>
        </div>
    </div>
    """
    st.markdown(topbar_html, unsafe_allow_html=True)

render_topbar()

st.markdown("### Usa tu cámara para obtener las mejores recetas!")

# ====================================================
# DEFINIMOS TABS Y “HACK” PARA ACTIVAR LA SEGUNDA
# ====================================================
if st.session_state.active_tab_idx == 0:
    tab_names = ["Reconocimiento", "Recomendaciones", "Stats"]
    tabs_obj = st.tabs(tab_names)
    tab_reco, tab_recom, tab_stats = tabs_obj[0], tabs_obj[1], tabs_obj[2]
else:
    tab_names = ["Recomendaciones", "Reconocimiento", "Stats"]
    tabs_obj = st.tabs(tab_names)
    tab_recom, tab_reco, tabs_stats = tabs_obj[0], tabs_obj[1], tabs_obj[2]

# =============================
# TAB RECONOCIMIENTO
# =============================
with tab_reco:
    st.subheader("📸 Detecta tus ingredientes")

    enable = st.toggle("Activar cámara", help="Activa la cámara para detectar ingredientes")
    img_file_buffer = st.camera_input("Haz una foto!", disabled=not enable, key="camera")

    if img_file_buffer and enable:
        bytes_data = img_file_buffer.getvalue()
        if bytes_data != st.session_state.last_uploaded_image:
            try:
                image = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
                detection_result = image_feed(image)  # Asume que da lista en inglés
                # Traducir a ES
                detection_checked_ind = supabase.table("ingredients").select("name").in_("name", detection_result).execute().data
                l_ind = {a["name"] for a in detection_checked_ind}
                detection_checked_coll = supabase.table("ingredients").select("name").in_("name", [p for l in detection_result for p in l.split()]).execute().data
                l_coll = {b["name"] for b in detection_checked_coll}
                elementos_unicos = l_ind | l_coll

                detected_es = [translate_en_es(e) for e in elementos_unicos]
                if not st.session_state.detection_list:
                    st.session_state.detection_list = detected_es
                else:
                    st.session_state.detection_list += detected_es
                    st.session_state.detection_list = list(set(st.session_state.detection_list))
                st.session_state.last_uploaded_image = bytes_data
            except Exception as e:
                st.error(f"Error al procesar la imagen: {e}")

    st.write("**Ingredientes detectados (puedes editarlos en la otra pestaña):**")
    st.write(", ".join(st.session_state.detection_list) or "Ninguno aún.")
# =============================
# TAB RECOMENDACIONES
# =============================
with tab_recom:
    st.title("🥘 Recomendaciones")
    
    with st.form("search_form"):
        temp_selected_ingredients = set(
            stt.st_tags(
                value=(list(st.session_state.detection_list)
                       if not st.session_state.selected_ingredients 
                       else list(st.session_state.selected_ingredients)),
                label = "## Ingredientes:",
                suggestions=[f["name_es"] for f in food_options],
                text="Escribe y presiona enter para añadir más"
            )
        )

        tag_data = supabase.table("tags").select("id, name_es").execute().data
        all_tag_names = [row["name_es"] for row in tag_data]
        selected_tag_names = st.multiselect(
            label = "Tipo de dieta:",
            options = all_tag_names,
            default = [],
            placeholder = "Elige una opción (O deja en blanco si no tienes preferencias)"
        )

        min_cal, max_cal = st.slider(
            "## Rango de calorías",
            0, 2000, (0, 700), step=50,
            help="Filtra recetas por total de calorías en este rango"
        )

        submitted = st.form_submit_button("Iniciar búsqueda")

    if submitted:
        enable = False
        st.session_state.detection_list = []
        st.session_state["pagina"] = 0
        st.session_state.selected_ingredients = temp_selected_ingredients
        if not st.session_state.selected_ingredients:
            data_cal = (
                supabase.table("recipes")
                .select("id, name_es, url, calories, proteins, fats, carbs, servings, img_url")
                .gte("calories", min_cal)
                .lte("calories", max_cal)
                .execute()
                .data
            )
            filtered = filter_by_tags(supabase, data_cal, selected_tag_names, tag_data)
            random.shuffle(filtered)
            st.session_state["recipe_data"] = filtered
        else:
            es_to_en_ings = [translate_es_en(ing).strip().lower() for ing in st.session_state.selected_ingredients]
            for i in es_to_en_ings:
                searched_id = supabase.table("searched_ingredient").select("id").eq("name", i).execute().data
                if searched_id:
                    searched_id = searched_id[0]["id"]
                    count = supabase.table("searched_ingredient").select("count").eq("id", searched_id).execute().data[0]["count"]
                    new_count = count+1
                    supabase.table("searched_ingredient").update({"count" : new_count}).eq("id", searched_id).execute()
                else:
                    try:
                        iid = supabase.table("ingredients").select("id").eq("name_en", i).execute().data[0]["id"]
                    except Exception as e:
                        iid = None
                        print(e)
                    finally:
                        supabase.table("searched_ingredient").insert({"name" : i, "ingredient_id" : iid, "count" : 1}).execute()

        
            df = get_filtered_recommendations(
                ingredients=" ".join(es_to_en_ings),
                url=url,
                key=key,
                health_labels=selected_tag_names,
                min_calories=min_cal,
                max_calories=max_cal
            )
            if df.empty:
                st.session_state["recipe_data"] = []
            else:
                recipe_ids = list(df["recipe_id"])
                rec_info = (
                    supabase.table("recipes")
                    .select("id, name_es, url, calories, proteins, fats, carbs, servings, img_url")
                    .in_("id", recipe_ids)
                    .execute()
                    .data
                )
                result_map = {r["id"]: r for r in rec_info}
                ordered_recipe_data = []
                for rid in recipe_ids:
                    if rid in result_map:
                        ordered_recipe_data.append(result_map[rid])
                st.session_state["recipe_data"] = ordered_recipe_data

    recipe_data = st.session_state["recipe_data"]

    if not recipe_data:
        st.info("No se encontraron recetas o no has pulsado 'Iniciar búsqueda'.")
    else:
        p = st.session_state["pagina"]
        recetas_por_pagina = 5
        total_paginas = (len(recipe_data) - 1) // recetas_por_pagina + 1
        inicio = p * recetas_por_pagina
        fin = inicio + recetas_por_pagina
        recetas_mostradas = recipe_data[inicio:fin]

        if not recetas_mostradas:
            st.info("No hay recetas en esta página.")
        else:
            for recipe in recetas_mostradas:
                st.markdown(f"#### 📖 {recipe['name_es']}")
                st.markdown(
                    f"🔥 {round(recipe['calories'], 1)} kcal  |  "
                    f"🥩 {round(recipe['proteins'], 1)} g  |  "
                    f"🥑 {round(recipe['fats'], 1)} g  |  "
                    f"🌾 {round(recipe['carbs'], 1)} g  |  " 
                    f"👤 {recipe['servings']} p"
                )
                with st.expander("📋 **Ver detalles**"):
                    flex_css = """
                    <style>
                    .recipe-flex-container {
                        display: flex; flex-direction: row; 
                        justify-content: center; align-items: flex-start;
                        gap: 2rem; flex-wrap: wrap; margin-top: 1rem;
                    }
                    .recipe-flex-item {
                        text-align: center;
                    }
                    @media screen and (max-width: 768px) {
                        .recipe-flex-container {
                            flex-direction: column; align-items: center;
                        }
                    }
                    .ingredient-table {
                        border-collapse: collapse; margin: 0 auto;
                    }
                    .ingredient-table th, .ingredient-table td {
                        border: 1px solid #FFA766;
                        padding: 0.5rem 1rem;
                    }
                    .ingredient-table th {
                        background-color: #FCE4D6;
                    }

                    .ingredient-table td {
                        background-color: #FFF3E0;
                    }
                    </style>
                    """
                    st.markdown(flex_css, unsafe_allow_html=True)

                    recipe_ingredients_data = (
                        supabase.table("recipe_ingredients")
                        .select("ingredient_id, amount")
                        .eq("recipe_id", recipe["id"])
                        .execute()
                        .data
                    )

                    table_html = """
                    <table class="ingredient-table">
                      <thead>
                        <tr><th>Ingrediente</th><th>Cantidad</th><th>Precio</th></tr>
                      </thead>
                      <tbody>
                    """
                    for item in recipe_ingredients_data:
                        ingredient_id = item["ingredient_id"]
                        quantity = round(item["amount"])

                        ing_data = (
                            supabase.table("ingredients")
                            .select("name_es", "price_mercadona")
                            .eq("id", ingredient_id)
                            .execute()
                            .data
                        )
                        if ing_data:
                            name_es = ing_data[0]["name_es"].capitalize()
                            price_mercadona = ing_data[0]["price_mercadona"] if ing_data[0]["price_mercadona"] else "❔"
                        else:
                            name_es = "Desconocido"

                        link_html = (
                            f'<a href="https://tienda.mercadona.es/search-results?query={name_es}" '
                            f'style="color:orange;" target="_blank">{name_es}</a>'
                        )
                        table_html += f"<tr><td>{link_html}</td><td>{quantity} g</td><td>{price_mercadona} €</td></tr>"
                    table_html += "</tbody></table>"

                    flex_html = f"""
                    <div class="recipe-flex-container">
                      <div class="recipe-flex-item">
                        <img src="{recipe['img_url']}" style="max-width: 100%; height: auto;" />
                      </div>
                      <div class="recipe-flex-item">
                        {table_html}
                      </div>
                    </div>
                    """
                    st.markdown(flex_html, unsafe_allow_html=True)

                    steps_data = (
                        supabase.table("steps")
                        .select("description")
                        .eq("recipe_id", recipe["id"])
                        .execute()
                        .data
                    )
                    if steps_data:
                        recipe_steps = steps_data[0]["description"]
                        st.markdown("### Pasos")
                        raw_parts = recipe_steps.split('.')
                        steps_list = [part.strip() for part in raw_parts if part.strip()]
                        for i, step in enumerate(steps_list, start=1):
                            st.markdown(f"* {step}.")
                            
            col1, col2, col3 = st.columns([2,1,2])
            with col1:
                st.markdown("<div style='text-align:right;'>", unsafe_allow_html=True)
                if p > 0:
                    if st.button("⬅ Anterior"):
                        st.session_state["pagina"] -= 1
                st.markdown("</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: center; justify-content: center; min-height: 70px;">
                        <p style="text-align: center; font-size: 20px; margin: 0;">Página {p+1} / {total_paginas}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col3:
                st.markdown("<div style='text-align:right;'>", unsafe_allow_html=True)
                if p < total_paginas - 1:
                    if st.button("Siguiente ➡"):
                        st.session_state["pagina"] += 1
                st.markdown("</div>", unsafe_allow_html=True)


with tab_stats:
    def get_popular_searches(n_top=None):
        counts = pd.DataFrame(supabase.table("searched_ingredient").select("name", "count").execute().data).sort_values("count", ascending=False)
        if n_top:
            counts = counts.head(n_top)
        sns.set_theme(context="talk", style="whitegrid", rc={'axes.facecolor': '#FFF8E1', 'figure.facecolor': '#FFF8E1'})

        # Crear la figura
        fig, ax = plt.subplots(dpi=100, figsize=(12, 8))
        colors = sns.color_palette("Oranges", len(counts))
        bars = sns.barplot(data=counts, x="count", y="name", ax=ax, palette = colors, edgecolor="black", linewidth=1.2)

        for bar in bars.containers:
            bars.bar_label(bar, fmt='%d', label_type='edge', padding=5, fontsize=14, color='black', weight='bold')

        ax.set_title("Búsquedas de Ingredientes", fontdict={"fontsize": 24, "fontweight": "bold"}, pad=15)
        ax.set_xlabel("Número de Búsquedas", fontsize=16, fontweight="bold")
        ax.set_ylabel("Ingrediente", fontsize=16, fontweight="bold")

        plt.xticks(fontsize=12, fontweight="bold")
        plt.yticks(fontsize=12)
        return fig
    
    c1, _ = st.columns(2)
    with c1:
        st.write("Veamos el volumen de búsqueda de los ingredientes! 🥕")
        n_entries = st.number_input(label="Máximo de entradas que mostrar", min_value=1)
    fig = get_popular_searches(n_entries)
    st.pyplot(fig, clear_figure=True)