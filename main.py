import streamlit as st
import numpy as np
import cv2
from src.support_cv import *
from src.support_recsys import *
import dotenv
dotenv.load_dotenv()
url = "https://zrhsejedrpoqcyfvfzsr.supabase.co"
key = os.getenv("db_API_pass")
supabase = connect_supabase(url, key)
TEXT_PROMPT =  '''
        potato . onion . garlic . carrot . tomato . lettuce . spinach . cucumber . zucchini . broccoli . 
        cauliflower . apple . banana . orange . lemon . grape . pear . peach . plum . watermelon . pineapple . 
        strawberry . blueberry . raspberry . blackberry . mango . kiwi . avocado . ginger . parsley . cilantro . 
        mint . rosemary . thyme . basil . bay leaf . chili pepper . mushroom . green bean . pea . brussels sprout . 
        kale . cabbage . celery . asparagus . leek . eggplant . radish . pumpkin . butternut squash . 
        okra . artichoke . corn . fig . date . papaya . lime . cherry . coconut . melon . 
        cantaloupe . peanut . almond . walnut . chia seed . sunflower seed . sesame seed . bread . pasta . 
        chicken . beef . pork . egg . ham . tofu . milk . yogurt . cheese . butter . canned tuna . canned salmon . 
        crushed tomato . canned tomato . honey . jam . peanut butter . coffee . tea . chocolate . 
        rice . lentil . chickpeas . black bean . bell pepper . sausage . 
        '''

food_options = TEXT_PROMPT.split(" . ")


st.set_page_config(page_title = "FoodScope", page_icon = "🍽️", initial_sidebar_state='collapsed')

with st.sidebar:
    language = st.selectbox("Language", ["🇪🇸", "🇬🇧"], placeholder="Select a language")

st.title('FoodScope')

if language == "🇪🇸":
    st.write('¡Bienvenido a FoodScope! 🍽️🔍')


    # Inicializar estados si no existen
    if 'detection_list' not in st.session_state:
        st.session_state.detection_list = []
    if 'last_uploaded_image' not in st.session_state:
        st.session_state.last_uploaded_image = None

    enable = st.checkbox("Activar cámara")
    img_file_buffer = st.camera_input("Haz una foto!", disabled=not enable)

    if img_file_buffer is not None and enable:
    # Convertir imagen a bytes
        bytes_data = img_file_buffer.getvalue()

        # Si la imagen es diferente a la última procesada, actualizar detección
        if bytes_data != st.session_state.last_uploaded_image:
            try:
                # Abrir la imagen con PIL
                image = Image.open(img_file_buffer)
                # Convertir a RGB si es necesario
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                # Convertir a numpy array
                image_np = np.array(image)
            except Exception as e:
                st.error(f"Error al procesar la imagen: {e}")
                image_np = None

            if image_np is not None:
                # Procesar la imagen para detección de objetos
                detection_result = image_feed(image_np)
                st.session_state.detection_list = detection_result
                st.session_state.last_uploaded_image = bytes_data  # Guardar la imagen actual



    # Mantener los ingredientes detectados en el multiselect sin volver a detectar en cada cambio
    selected_ingredients = st.multiselect(
        'Selecciona los ingredientes que tienes:', 
        options=food_options,
        default=st.session_state.detection_list
    )

    button_recs = st.button("Obtener Recomendaciones")

    if button_recs:
        rec_ids = get_recommendations(supabase, raw_user_ingredients=" ".join(selected_ingredients))["recipe_id"]
        urls = supabase.table('recipes').select('url').in_('id', rec_ids).execute().data
        st.write(urls)

elif language == "🇬🇧":
    st.write("Welcome to FoodScope! 🍽️🔍")