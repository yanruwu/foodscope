# FoodScope: Optimización Inteligente de Recetas y Compras 🍽️

FoodScope es una solución integral que fusiona inteligencia artificial, visión por computadora, análisis de datos y sistemas de recomendación para optimizar la experiencia culinaria. La herramienta permite a los usuarios:

- **Detectar ingredientes** a partir de imágenes capturadas con la cámara.
- **Obtener recetas y recomendaciones** basadas en los ingredientes disponibles, preferencias nutricionales y etiquetas de salud.
- **Integrar información de supermercados** para sugerir la compra de ingredientes faltantes.
- **Procesar y almacenar datos de recetas** mediante un pipeline ETL que utiliza la API de EDAMAM y Supabase.

---

## Caso de Negocio 💡

FoodScope nace para resolver dos necesidades principales:

1. **Para el consumidor:**
   - Facilitar la identificación de ingredientes disponibles en casa.
   - Sugerir recetas que maximicen el uso de lo que ya se tiene.
   - Simplificar la compra de ingredientes faltantes mediante la conexión con inventarios de supermercados.

2. **Para los supermercados:**
   - Obtener visibilidad sobre la demanda de ciertos productos.
   - Potenciar la venta cruzada de productos complementarios.

---

## Características Principales ⭐

- **Reconocimiento de Ingredientes:**  
  Utiliza modelos de visión por computadora (incluyendo GroundingDINO, con pruebas de CLIP y OwlViT) para detectar ingredientes en imágenes capturadas con dispositivos móviles o cámaras web.

- **Sistema de Recomendación:**  
  Basado en técnicas de procesamiento de lenguaje natural y análisis de similitud (TF-IDF, Cosine Similarity), permite sugerir recetas acorde a los ingredientes detectados y filtros como el rango calórico o etiquetas de salud.

- **Pipeline ETL para Recetas:**  
  Un conjunto de scripts (en Python y Jupyter notebooks) que extraen, transforman y cargan datos de recetas, traducen ingredientes y obtienen información nutricional a través de la API de EDAMAM.

- **Integración con Supabase:**  
  Se utiliza Supabase para gestionar la base de datos de recetas, ingredientes, pasos y etiquetas, facilitando la consulta y actualización de datos en tiempo real.

- **Interfaz de Usuario con Streamlit:**  
  La aplicación principal, desarrollada con Streamlit, ofrece una experiencia interactiva donde el usuario puede activar la cámara, detectar ingredientes y explorar recetas recomendadas.

---

## Acceso a la Aplicación 🌐

¡La aplicación ya está deployeada en Streamlit Cloud! Puedes accederla directamente a través del siguiente enlace:

[foodscope.streamlit.app](https://foodscope.streamlit.app)

---

## Estructura del Proyecto 📁

La organización de directorios es la siguiente:


```
yanruwu-foodscope/
├── README.md                  # Documentación general del proyecto
├── dap_leftoff.json           # Archivo de seguimiento del progreso en el pipeline ETL
├── main.py                    # Aplicación Streamlit principal para interacción con FoodScope
├── packages.txt               # Dependencias de sistema (p.ej., libgl1-mesa-glx)
├── requirements.txt           # Dependencias de Python
├── GroundingDINO/             # Código del modelo y demos de GroundingDINO
├── computervision/            # Scripts y notebooks para pruebas de visión (CLIP, OwlViT, etc.)
├── etl_pipeline/              # Pipeline ETL (scripts y notebooks) para procesar datos de recetas
├── rec sys/                  # Módulo de sistema de recomendación de recetas
├── src/                      # Módulos de soporte:
│   ├── support_cv.py         # Funciones para procesamiento y transformación de imágenes
│   ├── support_etl.py        # Funciones para el proceso ETL de recetas y nutrición
└── └── support_recsys.py     # Funciones para la recomendación de recetas
```


---

## Instalación y Configuración

### Requisitos de Sistema

- **Python 3.12** (o versión compatible)

### Instalación de Dependencias

1. **Clonar el repositorio:**

    ```bash
    git clone https://github.com/yanruwu/foodscope.git
    cd foodscope
    ```

2. **Instalar las dependencias de Python:**

    ```bash
    pip install -r requirements.txt
    ```


### Configuración de Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto y define al menos las siguientes variables (ajusta los valores según tus credenciales):

```env
db_API_pass=tu_api_key_supabase
edamam_session_id=tu_app_id_edamam
edamam_api_key=tu_api_key_edamam
```

## Uso del Proyecto 🚀

### 1. Aplicación Streamlit 📸

La interfaz principal se ejecuta a través de Streamlit. Para iniciarla en local, ejecuta:

```bash
streamlit run main.py
```

La aplicación permite:

- **Activar la cámara** para capturar imágenes y detectar ingredientes.
- **Editar la lista de ingredientes detectados.**
- **Buscar y visualizar recetas recomendadas** según los ingredientes y filtros aplicados (rango calórico, etiquetas de salud).

> **Nota:** También puedes acceder a la versión deployeada en [foodscope.streamlit.app](https://foodscope.streamlit.app).

### 2. Pipeline ETL ⚙️

El pipeline ETL se encarga de procesar y cargar datos de recetas en la base de datos (Supabase). Para ejecutarlo:

```bash
python etl_pipeline/etl.py
```

Este proceso:

- Lee recetas desde un archivo JSONL.
- Traduce ingredientes y obtiene datos nutricionales - mediante la API de EDAMAM.
- Inserta recetas, ingredientes, pasos y etiquetas en la base de datos.

### 3. Módulos de Visión por Computadora 👀

Dentro de la carpeta `computervision/` encontrarás distintos scripts y notebooks para pruebas y demostraciones:

- **cliptest.py:** Prueba de reconocimiento de ingredientes utilizando el modelo CLIP.
- **cvtest.py:** Ejemplo de integración con GroundingDINO para detectar ingredientes en imágenes.
- **owlvittest.py:** Ejemplo de uso del modelo OwlViT para detección de objetos.

### 4. Sistema de Recomendación 🍽️
El sistema de recomendación se encuentra en `rec sys/recsys.py` y utiliza técnicas basadas en TF-IDF y similitud coseno para sugerir recetas según los ingredientes introducidos. Puedes probarlo ejecutando:

```bash
python rec sys/recsys.py
```

### 5. Módulos de Soporte 🔧

El directorio `src/` contiene funciones y utilidades que integran las diferentes partes del proyecto:

- **support_cv.py:** Funciones para la transformación y procesamiento de imágenes, integración con GroundingDINO y otros modelos.
- **support_etl.py:** Funciones para la extracción, transformación y carga (ETL) de datos de recetas.
- **support_recsys.py:** Funciones para la recomendación de recetas basadas en similitud y análisis de ingredientes.

---

### Contribuciones 🤝

Si deseas contribuir a FoodScope:

1. **Haz un fork** del repositorio.
2. **Crea una rama** para tu feature o corrección:
   ```bash
   git checkout -b feature/nueva-funcionalidad
   ```
3. **Realiza tus cambios** y haz commit:
   ```bash
   git commit -m "Añade nueva funcionalidad"
   ```
4. **Sube la rama** a tu repositorio:
   ```bash
   git push origin feature/nueva-funcionalidad
   ```
5. Abre un **Pull Request** en GitHub.

### Contacto 📬

Para dudas, sugerencias o reportar problemas, por favor abre un [issue en GitHub](https://github.com/yanruwu/foodscope/issues).

---

FoodScope es una herramienta en constante evolución que busca revolucionar la experiencia en la cocina mediante la integración de tecnologías de punta. ¡Esperamos tus comentarios y contribuciones! 😊
