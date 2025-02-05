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
from src.support_recsys import get_recommendations, connect_supabase
from src.support_etl import translate_es_en, translate_en_es
# ====================================================
# CONFIGURACIÓN DE STREAMLIT
# ====================================================
st.set_page_config(page_title="FoodScope - Identifica ingredientes y descubre recetas",
                    page_icon="🍽️",
                    layout="wide"
)

favicon_html = """
    <link rel="icon" href="logo.png" type="image/x-icon">
"""
st.markdown(favicon_html, unsafe_allow_html=True)

meta_description = """
    <meta name="description" content="Explora ingredientes y encuentra recetas con FoodScope. Tu asistente inteligente para identificar productos y mejorar tu cocina.">
    <meta name="keywords" content="recetas, ingredientes, IA, reconocimiento de alimentos, comida, cocina inteligente, FoodScope">
    <meta name="author" content="FoodScope Team">
"""

st.markdown(meta_description, unsafe_allow_html=True)

# ====================================================
# CSS TEMA OSCURO + DETALLES NARANJA
# ====================================================
st.markdown("""
<style>
/* Fondo oscuro y texto claro */
[data-testid="stAppViewContainer"],
body, .main {
    background-color: #121212 !important; 
    color: #FFFFFF !important;
}
p, div, h1, h2, h3, h4, h5, h6, span, label {
    color: #FFFFFF !important;
}

/* Ocultar header y footer de Streamlit */
header[data-testid="stHeader"] {
    display: none;
}
footer {
    visibility: hidden;
}

/* Topbar naranja */
.topbar {
    position: sticky;
    top: 0;
    z-index: 9999;
    background-color: #F26722;
    height: 60px;
    display: flex;
    align-items: center;
    padding: 0 2rem;
    margin-bottom: 1rem;
}

/* Ajuste de padding en pantallas más estrechas */
@media screen and (max-width: 600px) {
    .topbar {
        padding: 0 1rem; /* Reduce el padding horizontal en móviles */
    }
}

.topbar-logo {
    display: flex;
    align-items: center;
    font-weight: bold;
    font-size: 1.3rem;
    color: #fff;
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
    flex-wrap: wrap;          /* Permite que, si no caben en una línea, pasen a la siguiente */
    justify-content: flex-end; /* Mantiene la alineación a la derecha */
}

.topbar-right a {
    color: #fff;
    text-decoration: none;
    font-weight: 600;
    font-size: 1rem;
}
.topbar-right a:hover {
    text-decoration: underline;
}

/* Si la pantalla es muy pequeña (por ejemplo < 450px), reducimos la fuente */
@media screen and (max-width: 450px) {
    .topbar-right a {
        font-size: 0.9rem;  /* o el tamaño que prefieras */
    }
}


/* Tabs en oscuro, tab activa en naranja */
[data-testid="stHorizontalBlock"] > div {
    border: none !important;
    background-color: #1F1F1F !important;
}
div [data-testid="stHorizontalBlock"] button[kind="tab"] {
    background-color: transparent !important;
    color: #FFFFFF !important;
    border: 1px solid #444 !important;
}
div [data-testid="stHorizontalBlock"] button[aria-selected="true"] {
    background-color: #F26722 !important;
    color: #FFF !important;
    border: none !important;
}

/* Cámara con ancho máximo (desktop) y 100% en móvil */
.camera-container {
    margin: 0 auto;
    width: 100%;
    max-width: 600px;
}
@media screen and (max-width: 768px) {
    .camera-container {
        max-width: 100%;
    }
}
.camera-container .stCamera {
    width: 100% !important;
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

/* Expander */
.st-expander {
    background-color: #1F1F1F !important; 
    border: 1px solid #FFA766 !important;
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

# 0 = Reconocimiento, 1 = Recomendaciones
if 'active_tab_idx' not in st.session_state:
    st.session_state.active_tab_idx = 0

# ====================================================
# FUNCIÓN PARA CARGAR LOGO EN BASE64
# (Si no lo encuentras, puedes omitir)
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
    # Cargamos el logo en base64, si existe
    encoded_logo = ""
    if os.path.exists("logo_transparent.png"):
        with open("logo_transparent.png", "rb") as f:
            encoded_logo = base64.b64encode(f.read()).decode("utf-8")

    if encoded_logo:
        logo_html = f'<img src="data:image/png;base64,{encoded_logo}" alt="Logo" />'
    else:
        logo_html = ""  # No se encontró el archivo, o dejas un texto

    topbar_html = f"""
    <div class="topbar">
        <div class="topbar-logo">
            {logo_html}
            FoodScope
        </div>
        <div class="topbar-right">
            <!-- Cambia a tu repositorio de GitHub u otro enlace -->
            <a href="https://i.ytimg.com/vi/DkC2Yx7lNOo/hq720.jpg?sqp=-oaymwEhCK4FEIIDSFryq4qpAxMIARUAAAAAGAElAADIQj0AgKJD&rs=AOn4CLBvwZqD4-cO0jI7S6Y9tziGkrDkOQ" target="_blank">Contacto</a>
            <a href="https://github.com/tu-org/tu-repo#readme" target="_blank">Acerca de</a>
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
    tab_names = ["Reconocimiento", "Recomendaciones"]
    tabs_obj = st.tabs(tab_names)
    tab_reco, tab_recom = tabs_obj[0], tabs_obj[1]
else:
    tab_names = ["Recomendaciones", "Reconocimiento"]
    tabs_obj = st.tabs(tab_names)
    tab_recom, tab_reco = tabs_obj[0], tabs_obj[1]


# ====================================================
# TAB RECONOCIMIENTO
# ====================================================
with tab_reco:
    st.subheader("📸 Detecta tus ingredientes")

    st.markdown('<div class="camera-container">', unsafe_allow_html=True)
    enable = st.toggle("Activar cámara", help="Activa la cámara para detectar ingredientes")
    img_file_buffer = st.camera_input("Haz una foto!", disabled=not enable, key="camera")
    st.markdown('</div>', unsafe_allow_html=True)

    # Procesar imagen
    if img_file_buffer and enable:
        bytes_data = img_file_buffer.getvalue()
        if bytes_data != st.session_state.last_uploaded_image:
            try:
                image = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
                detection_result = image_feed(image)
                st.session_state.detection_list = [translate_en_es(e) for e in set(detection_result)]
                st.session_state.last_uploaded_image = bytes_data
            except Exception as e:
                st.error(f"Error al procesar la imagen: {e}")

    # Barra de ingredientes detectados (en español)
    temp_detected_ingredients = set(
        stt.st_tags(
            value=st.session_state.detection_list,
            suggestions=[f["name_es"] for f in food_options],  # autocompletado en español
            label="Ingredientes detectados y seleccionados:",
            text="Escribe y presiona enter para añadir más"
        )
    )

    # Botón “Buscar Recetas” → cambia a la pestaña Recomendaciones
    if st.button("Buscar Recetas"):
        st.session_state.selected_ingredients = temp_detected_ingredients
        st.session_state.active_tab_idx = 1
        st.rerun()

# ====================================================
# TAB RECOMENDACIONES
# ====================================================
with tab_recom:
    st.title("🥘 Recetas Recomendadas")

    # Barra de ingredientes en español
    temp_selected_ingredients = set(
        stt.st_tags(
            value=list(st.session_state.selected_ingredients),
            suggestions=[f["name_es"] for f in food_options],
            label="Ingredientes seleccionados:",
            text="Escribe y presiona enter para añadir más"
        )
    )
    if st.button("Actualizar ingredientes"):
        st.session_state.selected_ingredients = temp_selected_ingredients
        st.success("Ingredientes actualizados. ¡Recargando recomendaciones!")

    st.write("---")
    # Si no hay ingredientes => TODAS las recetas (aleatorio)
    if not st.session_state.selected_ingredients:
        st.info("No hay ingredientes seleccionados. Mostrando TODAS las recetas en orden aleatorio.")
        recipe_data = supabase.table('recipes') \
            .select('id', 'name_es', 'url', 'calories', 'proteins', 'fats', 'carbs', 'img_url') \
            .execute().data
        random.shuffle(recipe_data)
    else:
        # Traducimos los ingredientes de ES a EN
        es_to_en_ings = [translate_es_en(ingr).strip().lower() for ingr in st.session_state.selected_ingredients]
        rec_ids = get_recommendations(
            supabase,
            raw_user_ingredients=" ".join(es_to_en_ings)
        )["recipe_id"]
        recipe_data = (
            supabase.table('recipes')
            .select('id', 'name_es', 'url', 'calories', 'proteins', 'fats', 'carbs', 'img_url')
            .in_('id', rec_ids)
            .execute()
            .data
        )

    recetas_por_pagina = 5
    total_paginas = (len(recipe_data) - 1) // recetas_por_pagina + 1
    p = st.session_state["pagina"]

    inicio = p * recetas_por_pagina
    fin = inicio + recetas_por_pagina
    recetas_mostradas = recipe_data[inicio:fin]

    if recetas_mostradas:
        for recipe in recetas_mostradas:
            st.markdown(f"#### 📖 {recipe['name_es']}")
            st.markdown(
                f"🔥 {round(recipe['calories'], 1)} kcal  |  "
                f"🥩 {round(recipe['proteins'], 1)} g  |  "
                f"🥑 {round(recipe['fats'], 1)} g  |  "
                f"🌾 {round(recipe['carbs'], 1)} g"
            )
            with st.expander("📜 Ver detalles"):

                # 1. CSS personalizado para el contenedor flex y la tabla
                flex_css = """
                <style>
                .recipe-flex-container {
                    display: flex;
                    flex-direction: row;       /* Lado a lado en escritorio */
                    justify-content: center;
                    align-items: flex-start;   /* Alinea arriba la tabla con la imagen */
                    gap: 2rem;                 /* Espacio horizontal entre imagen y tabla */
                    flex-wrap: wrap;           /* Permite que se apilen en pantalla pequeña */
                    margin-top: 1rem;
                }
                .recipe-flex-item {
                    text-align: center;
                }
                /* En móviles, apilamos uno debajo de otro */
                @media screen and (max-width: 768px) {
                .recipe-flex-container {
                    flex-direction: column;    /* Se apilan */
                    align-items: center;       /* Centrados */
                }
                }
                /* Estilo de la tabla */
                .ingredient-table {
                    border-collapse: collapse;
                    margin: 0 auto;           /* Centrar la tabla horizontalmente */
                }
                .ingredient-table th, .ingredient-table td {
                    border: 1px solid #FFA766;
                    padding: 0.5rem 1rem;
                }
                .ingredient-table th {
                    background-color: #1F1F1F; /* gris oscuro, acorde a tu tema */
                }
                </style>
                """
                st.markdown(flex_css, unsafe_allow_html=True)

                # 2. Obtenemos datos de ingredientes + cantidades
                recipe_ingredients_data = (
                    supabase.table("recipe_ingredients")
                    .select("ingredient_id, amount")
                    .eq("recipe_id", recipe["id"])
                    .execute()
                    .data
                )

                # 3. Creamos la tabla HTML (cabecera + filas)
                table_html = """
                <table class="ingredient-table">
                <thead>
                    <tr>
                    <th>Ingrediente</th>
                    <th>Cantidad</th>
                    </tr>
                </thead>
                <tbody>
                """

                for item in recipe_ingredients_data:
                    ingredient_id = item["ingredient_id"]
                    quantity = round(item["amount"])

                    # Consulta para obtener name_es
                    ing_data = (
                        supabase.table("ingredients")
                        .select("name_es")
                        .eq("id", ingredient_id)
                        .execute()
                        .data
                    )
                    if ing_data:
                        name_es = ing_data[0]["name_es"].capitalize()
                    else:
                        name_es = "Desconocido"

                    # Hipervínculo solo para el nombre
                    link_html = (
                        f'<a href="https://soysuper.com/search?q={name_es}" '
                        f'style="color:orange;" target="_blank">{name_es}</a>'
                    )

                    table_html += f"<tr><td>{link_html}</td><td>{quantity} g</td></tr>"

                table_html += "</tbody></table>"

                # 4. Construimos un contenedor flex con la imagen y la tabla
                flex_html = f"""
                <div class="recipe-flex-container">
                <!-- Imagen -->
                <div class="recipe-flex-item">
                    <img src="{recipe['img_url']}" style="max-width: 100%; height: auto;" />
                </div>

                <!-- Tabla -->
                <div class="recipe-flex-item">
                    {table_html}
                </div>
                </div>
                """

                # Renderizamos todo el bloque en HTML
                st.markdown(flex_html, unsafe_allow_html=True)

                st.write("\n")
                st.markdown("### Pasos")
                # 5. Pasos de la receta (abajo)
                steps_data = (
                    supabase.table("steps")
                    .select("description")
                    .eq("recipe_id", recipe["id"])
                    .execute()
                    .data
                )
                if steps_data:
                    recipe_steps = steps_data[0]["description"]

                    # Dividimos el texto por cada punto. 
                    # - Ojo: si tu base de datos ya almacena pasos separados, usa ese formato en vez de este split.
                    raw_parts = recipe_steps.split('.')

                    # Limpiamos espacios y descartamos partes vacías
                    steps_list = [part.strip() for part in raw_parts if part.strip()]

                    # Mostramos cada paso con numeración "Paso 1", "Paso 2", etc.
                    st.markdown("**Pasos de la Receta:**")
                    for i, step in enumerate(steps_list, start=1):
                        st.markdown("* " + step + ".")


        # Paginación (centrada)
        col1, col2, col3 = st.columns([2,1,2])
        with col1:
            st.markdown("<div style='text-align:right;'>", unsafe_allow_html=True)
            if p > 0:
                if st.button("⬅ Anterior"):
                    st.session_state["pagina"] -= 1
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown(
                f'<p style="text-align:center; font-size:20px;">'
                f'Página {p + 1} / {total_paginas}</p>',
                unsafe_allow_html=True
            )

        with col3:
            st.markdown("<div style='text-align:right;'>", unsafe_allow_html=True)
            if p < total_paginas - 1:
                if st.button("Siguiente ➡"):
                    st.session_state["pagina"] += 1
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No se encontraron recetas.")
