import streamlit as st
import numpy as np
import os
import cv2  # Asegúrate de importar OpenCV si no lo has hecho
from src.support_cv import *
from src.support_recsys import *
import dotenv
import streamlit_tags as stt


# Configuración y configuración
dotenv.load_dotenv()
url = "https://zrhsejedrpoqcyfvfzsr.supabase.co"
key = os.getenv("db_API_pass")
supabase = connect_supabase(url, key)

food_options = supabase.table("ingredients").select("name_es", "name_en").execute().data

# Configuración de la página
st.set_page_config(
    page_title="FoodScope",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed"
)
# CSS personalizado para la página y el botón fijo
st.markdown("""
    <style>
    /* Estilos generales */
    .main {
        padding: 2rem;
    }
    .stTitle {
        color: #2c3e50;
        font-size: 3rem !important;
    }
    .stButton button {
        background-color: #27ae60;
        color: white;
        border-radius: 10px;
    }

    /* Estilos para el botón fijo */
    .fixed-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
    }

    /* Opcional: Estilos adicionales para mejorar la apariencia */
    .fixed-button button {
        background-color: #e74c3c;
        color: white;
        border: none;
        padding: 15px;
        border-radius: 50%;
        font-size: 20px;
        cursor: pointer;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }

    .fixed-button button:hover {
        background-color: #c0392b;
    }
    </style>
    """, unsafe_allow_html=True)


# Sidebar
with st.sidebar:
    st.image("logo.png", width=100)  # Agrega tu logo
    language = st.selectbox(
        "🌍 Language / Idioma",
        ["🇪🇸 Español", "🇬🇧 English"],
        index=0
    )

# Inicializar estados de sesión
if 'detection_list' not in st.session_state:
    st.session_state.detection_list = []
if 'last_uploaded_image' not in st.session_state:
    st.session_state.last_uploaded_image = None
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'pagina' not in st.session_state:
    st.session_state.pagina = 0
if 'selected_ingredients' not in st.session_state:
    st.session_state.selected_ingredients = []  # Inicializar como lista vacía

# Contenido principal
st.title('🍽️ FoodScope')

if language == "🇪🇸 Español":
    st.markdown("### 📸 Detecta tus ingredientes")
    
    # Sección de cámara
    enable = st.toggle("Activar cámara", help="Activa la cámara para detectar ingredientes")
    img_file_buffer = st.camera_input(
        "Haz una foto!",
        disabled=not enable,
        key="camera"
    )

    # Procesar imagen y actualizar detecciones
    if img_file_buffer and enable:
        bytes_data = img_file_buffer.getvalue()
        if bytes_data != st.session_state.last_uploaded_image:
            try:
                image = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
                detection_result = image_feed(image)
                st.session_state.detection_list = detection_result
                st.session_state.last_uploaded_image = bytes_data
            except Exception as e:
                st.error(f"Error al procesar la imagen: {e}")

    # Selección de ingredientes con búsqueda (variable temporal)
    temp_selected_ingredients = set(stt.st_tags(value = st.session_state.detection_list,
                                             suggestions = [f["name_en"] for f in food_options], 
                                             label = "Ingredientes detectados y seleccionados:",
                                             text = "Escribe y presiona enter para añadir más"))

    # Botón para ir a recomendaciones
    if st.button("🔍 Ver Recomendaciones", use_container_width=True):
        st.session_state.selected_ingredients = temp_selected_ingredients
        st.session_state.page = 'recommendations'
        st.rerun()
    # Página de recomendaciones
    if st.session_state.page == 'recommendations':
        st.title("🥘 Recetas Recomendadas")
        
        with st.spinner('Buscando las mejores recetas...'):
            if not st.session_state.selected_ingredients:
                st.warning("No se han seleccionado ingredientes. Por favor, regresa y selecciona algunos ingredientes.")
            else:
                rec_ids = get_recommendations(supabase, raw_user_ingredients=" ".join(st.session_state.selected_ingredients))["recipe_id"]
                recipe_data = supabase.table('recipes').select('id', 'name_es', 'url','calories', 'proteins', 'fats', 'carbs', 'img_url').in_('id', rec_ids).execute().data
                
                # Definir el número de recetas por página
                recetas_por_pagina = 5

                # Número total de páginas
                total_paginas = (len(recipe_data) - 1) // recetas_por_pagina + 1

                # Inicializar página en sesión si no existe
                if "pagina" not in st.session_state:
                    st.session_state["pagina"] = 0

                # Obtener la página actual desde la sesión
                p = st.session_state["pagina"]

                # Calcular el rango de recetas a mostrar
                inicio = p * recetas_por_pagina
                fin = inicio + recetas_por_pagina
                recetas_mostradas = recipe_data[inicio:fin]

                if recetas_mostradas:
                    cols = st.columns(1)  # Puedes cambiar el número si quieres más columnas

                    for idx, recipe in enumerate(recetas_mostradas):
                        with cols[idx % 1]:
                            with st.container():
                                # Sección de vista previa con nombre y macros en una sola línea
                                st.markdown(
                                    f"#### 📖 {recipe['name_es']}  "
                                )
                                st.markdown(
                                    f"🔥 {round(recipe['calories'], 1)} kcal  |  "
                                    f"🥩 {round(recipe['proteins'], 1)} g  |  "
                                    f"🥑 {round(recipe['fats'], 1)} g  |  "
                                    f"🌾 {round(recipe['carbs'], 1)} g"
                                )

                                # Sección desplegable con imagen e ingredientes
                                with st.expander("📜 Ver detalles"):
                                    # Mostrar la imagen solo cuando se despliega
                                    st.image(recipe['img_url'], use_container_width =True)

                                    # Obtener los ingredientes
                                    recipe_ingredients_ids = [
                                        e["ingredient_id"]
                                        for e in supabase.table("recipe_ingredients")
                                        .select("ingredient_id")
                                        .eq("recipe_id", recipe['id'])
                                        .execute()
                                        .data
                                    ]
                                    recipe_ingredients = [
                                        ri["name_es"].capitalize()
                                        for ri in supabase.table("ingredients")
                                        .select("name_es")
                                        .in_("id", recipe_ingredients_ids)
                                        .execute()
                                        .data
                                    ]

                                    # Mostrar ingredientes
                                    # st.markdown(f"**Tienes:** {set(st.session_state.selected_ingredients) & set(recipe_ingredients)}")
                                    st.markdown("**Ingredientes:**")
                                    st.write(" | ".join(recipe_ingredients))
                                    st.write("**Pasos**")
                                    recipe_steps = supabase.table("steps").select("description").eq("recipe_id", recipe["id"]).execute().data[0]["description"]
                                    st.write(recipe_steps.replace(".", ".\n"))

                                    # # Botón para ver la receta completa (siempre visible)
                                    # st.page_link(label="Ver receta completa", page=recipe['url'], icon="⛓️‍💥")

                else:
                    st.info("No se encontraron recetas para los ingredientes seleccionados.")
# Botón fijo para volver a la cámara
st.markdown("""
    <div class="fixed-button">
        <form action="" method="get">
            <button type="submit" name="go_home">
                🔄
            </button>
        </form>
    </div>
    """, unsafe_allow_html=True)

# Botones de paginación
col1, col2, col3 = st.columns([1,2,1])

with col1:
    if st.session_state["pagina"] > 0:
        if st.button("⬅ Anterior"):
            st.session_state["pagina"] -= 1
            st.rerun()

with col2:
    st.markdown(f'<p style="text-align:center; font-size:20px;">Página {st.session_state["pagina"] + 1} / {total_paginas}</p>', unsafe_allow_html=True)

with col3:
    if st.session_state["pagina"] < total_paginas - 1:
        if st.button("Siguiente ➡"):
            st.session_state["pagina"] += 1
            st.rerun()

            