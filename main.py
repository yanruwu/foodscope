import streamlit as st
import numpy as np
import os
import cv2  # Asegúrate de importar OpenCV si no lo has hecho
from src.support_cv import *
from src.support_recsys import *
import dotenv


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
    temp_selected_ingredients = st.multiselect(
        'Ingredientes detectados y seleccionados:',
        options=[f["name_en"] for f in food_options],
        default=st.session_state.detection_list,
        help="Puedes escribir para buscar ingredientes"
    )

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
                
                if recipe_data:
                    # Mostrar recetas en una cuadrícula
                    cols = st.columns(1)
                    for idx, recipe in enumerate(recipe_data):
                        with cols[idx % 1]:
                            with st.container():
                                st.markdown(f"#### 📖 {recipe['name_es']}")
                                st.markdown(f"[![Receta]({recipe['img_url']})]")
                                
                                # Información nutricional en formato tabular
                                st.markdown(f"""
                                | Nutriente | Cantidad |
                                |-----------|-----------|
                                | 🔥 Calorías | {round(recipe['calories'], ndigits=2)} kcal |
                                | 🥩 Proteína | {round(recipe['proteins'], ndigits=2)} g |
                                | 🥑 Grasa | {round(recipe['fats'], ndigits=2)} g |
                                | 🌾 Carbohidratos | {round(recipe['carbs'], ndigits=2)} g |
                                """)
                                st.markdown(f"[Ver receta completa]({recipe['url']})")
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