import streamlit as st
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(project_root)

from src.support_cv import *

st.title('FoodScope')
st.write('¡Bienvenido a FoodScope! 🍽️🔍')
target_img = st.camera_input("camera_feed")

detection_list = image_feed(target_img)
st.write('¡Listo! Aquí tienes el resultado de la detección de objetos:')
st.image(detection_list, use_column_width=True)