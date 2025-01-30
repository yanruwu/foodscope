import os
import cv2
import torch
from PIL import Image
import sys
import numpy as np

sys.path.append(r'GroundingDINO')

# GroundingDINO imports
from groundingdino.util.inference import load_model, predict, annotate, load_image
import groundingdino.datasets.transforms as T

def transform_image(frame):
    """
    Transforma un frame de OpenCV (BGR) a formato de entrada del modelo GroundingDINO.
    - Convierte el frame de BGR a RGB.
    - Lo transforma a objeto PIL.
    - Aplica las transformaciones de GroundingDINO (normalización, resize, etc.)
    
    Retorna:
        frame_rgb (np.ndarray): imagen en formato RGB (para anotaciones posteriores).
        image_transformed (torch.Tensor): imagen lista para ingresar al modelo.
    """
    transform = T.Compose(
        [
            T.RandomResize([800], max_size=1333),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )

    # OpenCV usa BGR, convertimos a RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convertir a formato PIL
    image_source = Image.fromarray(frame_rgb)

    # Aplicar las transformaciones
    image_transformed, _ = transform(image_source, None)

    return frame_rgb, image_transformed

def transform_pil_image(image_pil):
    """
    Transforma una imagen PIL a formato de entrada del modelo GroundingDINO.
    - Aplica las transformaciones de GroundingDINO (normalización, resize, etc.)
    
    Args:
        image_pil (PIL.Image.Image): Imagen en formato PIL.

    Returns:
        image_rgb (np.ndarray): Imagen en formato RGB (para anotaciones posteriores).
        image_transformed (torch.Tensor): Imagen lista para ingresar al modelo.
    """
    transform = T.Compose([
        T.RandomResize([800], max_size=1333),
        T.ToTensor(),
        T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    # Convertir PIL a NumPy array (para anotaciones posteriores)
    image_rgb = np.array(image_pil)

    # Aplicar las transformaciones
    image_transformed, _ = transform(image_pil, None)

    return image_rgb, image_transformed

def initialize_model(base_dir):
    """
    Inicializa el modelo GroundingDINO.
    - Carga configuraciones y pesos desde las rutas especificadas.
    - Detecta si existe GPU, en caso contrario usa CPU.
    
    Retorna:
        model (nn.Module): modelo de GroundingDINO listo para predecir.
        device (torch.device): dispositivo usado (cuda o cpu).
    """
    config_path = os.path.join(base_dir, "GroundingDINO", "groundingdino", "config", "GroundingDINO_SwinT_OGC.py")
    weights_path = os.path.join(base_dir, "GroundingDINO", "weights", "groundingdino_swint_ogc.pth")

    # Verifica si existe GPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Utilizando dispositivo: {device}")

    # Carga el modelo
    model = load_model(config_path, weights_path, device=device)
    return model, device

def remote_feed():
    # Define la ruta base de tu proyecto
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Inicializa el modelo
    model, device = initialize_model(BASE_DIR)

    # Parámetros para la detección
    TEXT_PROMPT =  '''
        potato . onion . garlic clove . carrot . tomato . lettuce . spinach . cucumber . zucchini . broccoli .
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
    BOX_THRESHOLD = 0.30
    TEXT_THRESHOLD = 0.25

    # Fuente de video (cámara IP, archivo, cámara local, etc.)
    # En tu ejemplo usas la IP: 'http://172.26.1.129:4747/video'
    cap = cv2.VideoCapture(0)  # Cambia aquí según necesites
    cv2.namedWindow("Live Feed", cv2.WINDOW_NORMAL)

    # Indica al usuario cómo interactuar
    print("Presiona 'p' para realizar una predicción. Presiona 'ESC' para salir.")

    show_annotated = False
    annotated_frame = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("No se pudo leer el frame de la cámara.")
            break

        if show_annotated and annotated_frame is not None:
            # Muestra la imagen con las anotaciones
            cv2.imshow("Live Feed", annotated_frame)
        else:
            # Muestra el feed en vivo sin anotaciones
            cv2.imshow("Live Feed", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # Tecla ESC para salir
            break
        elif key == ord('p'):  # Alterna entre Live Feed y Predicción
            if show_annotated:
                # Volver al Live Feed
                show_annotated = False
                print("Volviendo al Live Feed...")
            else:
                # Capturar el frame actual y realizar la predicción
                print("Realizando predicción...")
                frame_source, captured_frame = transform_image(frame)

                # Realizar predicción con el modelo
                boxes, logits, phrases = predict(
                    model=model,
                    image=captured_frame,
                    caption=TEXT_PROMPT,
                    box_threshold=BOX_THRESHOLD,
                    text_threshold=TEXT_THRESHOLD,
                    device=device
                )

                # Anotar el frame original (en RGB)
                annotated_frame = annotate(
                    image_source=frame_source,
                    boxes=boxes,
                    logits=logits,
                    phrases=phrases
                )

                # Convertimos a BGR para guardar en disco con OpenCV
                annotated_frame_bgr = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)

                # Guardar la imagen anotada
                output_path = os.path.join(BASE_DIR, "computervision", "live_annotated_image.jpg")
                cv2.imwrite(output_path, annotated_frame_bgr)
                
                print(f"Predicción completada. Frases detectadas: {phrases}")

                # Cambiar al modo "Mostrar Imagen Anotada"
                show_annotated = True

    # Liberar recursos
    cap.release()
    cv2.destroyAllWindows()

def image_feed(img):
    # Define la ruta base de tu proyecto
    BASE_DIR = r"C:\Proyecto-Final"

    # Inicializa el modelo
    model, device = initialize_model(BASE_DIR)

    # Parámetros para la detección
    TEXT_PROMPT =  '''
        potato , onion , garlic , carrot , tomato , lettuce , spinach , cucumber , zucchini , broccoli ,
        cauliflower , apple , banana , orange , lemon , grape , pear , peach , plum , watermelon , pineapple ,
        strawberry , blueberry , raspberry , blackberry , mango , kiwi , avocado , ginger , parsley , cilantro ,
        mint , rosemary , thyme , basil , bay leaf , chili pepper , mushroom , green bean , pea , brussels sprout ,
        kale , cabbage , celery , asparagus , leek , eggplant , radish , pumpkin , butternut squash ,
        okra , artichoke , corn , fig , date , papaya , lime , cherry , coconut , melon ,
        cantaloupe , peanut , almond , walnut , chia seed , sunflower seed , sesame seed , bread , pasta ,
        chicken , beef , pork , egg , ham , tofu , milk , yogurt , cheese , butter , canned tuna , canned salmon ,
        crushed tomato , canned tomato , honey , jam , peanut butter , coffee , tea , chocolate , 
        rice , lentil , chickpeas , black bean , bell pepper , sausage , 
        '''
    BOX_THRESHOLD = 0.30
    TEXT_THRESHOLD = 0.25


    frame_source, captured_frame = transform_image(img)

    # Realizar predicción con el modelo
    boxes, logits, phrases = predict(
        model=model,
        image=captured_frame,
        caption=TEXT_PROMPT,
        box_threshold=BOX_THRESHOLD,
        text_threshold=TEXT_THRESHOLD,
        device=device
    )

    # Anotar el frame original (en RGB)
    annotated_frame = annotate(
        image_source=frame_source,
        boxes=boxes,
        logits=logits,
        phrases=phrases
    )

    # Guardar la imagen anotada
    output_path = os.path.join(BASE_DIR, "computervision", "live_annotated_image.jpg")
    cv2.imwrite(output_path, annotated_frame)
    
    print(f"Predicción completada. Frases detectadas: {phrases}")
    return phrases
