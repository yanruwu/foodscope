import os
from groundingdino.util.inference import load_model, predict, annotate
from groundingdino.util.misc import nested_tensor_from_tensor_list
import groundingdino.datasets.transforms as T
import cv2
import torch
import numpy as np
from PIL import Image

def transform_image(frame):
    # La transformación del paquete de groundingdino (realizada por load_image), adaptada para transformar un frame de opencv.
    transform = T.Compose(
        [
            T.RandomResize([800], max_size=1333),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )

    # Convertir frame de OpenCV (BGR) a RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convertir a formato PIL
    image_source = Image.fromarray(frame_rgb)

    # Aplicar las transformaciones
    image_transformed, _ = transform(image_source, None)

    return frame_rgb, image_transformed


# Define la ruta base
BASE_DIR = r"C:\Proyecto-Final"

# Rutas absolutas
config_path = os.path.join(BASE_DIR, "GroundingDINO/groundingdino/config/GroundingDINO_SwinT_OGC.py")
weights_path = os.path.join(BASE_DIR, "GroundingDINO/weights/groundingdino_swint_ogc.pth")

# Parámetros del modelo
TEXT_PROMPT =  '''
potato . onion . garlic clove . carrot . tomato . lettuce . spinach . cucumber . zucchini . broccoli .
cauliflower . apple . banana . orange . lemon . grape . pear . peach . plum . watermelon . pineapple .
strawberry . blueberry . raspberry . blackberry . mango . kiwi . avocado . ginger . parsley . cilantro .
mint . rosemary . thyme . basil . bay leaf . chili pepper . mushroom . green bean . pea . brussels sprout .
kale . cabbage . celery . asparagus . leek . eggplant . radish . pumpkin . butternut squash .
okra . artichoke . corn . apricot . fig . date . papaya . lime . cherry . coconut . melon .
cantaloupe . peanut . almond . walnut . chia seed . sunflower seed . sesame seed . bread . pasta .
chicken . beef . pork . egg . ham . tofu . milk . yogurt . cheese . butter . canned tuna . canned salmon .
crushed tomato . canned tomato . honey . jam . peanut butter . coffee . tea . chocolate . 
rice . lentil . chickpeas . black bean . bell pepper . sausage . 
'''
BOX_TRESHOLD = 0.35
TEXT_TRESHOLD = 0.25

# Cargar modelo en CPU (en este caso no tengo GPU)
device = torch.device("cpu")
model = load_model(config_path, weights_path, device=device)

# Inicializar la cámara
# cap = cv2.VideoCapture(0)
cap = cv2.VideoCapture('http://192.168.1.146:4747/video')
cv2.namedWindow("Live Feed")

print("Presiona 'p' para realizar una predicción. Presiona 'ESC' para salir.")

# Estado inicial: Live Feed
show_annotated = False
annotated_frame = None

while cap.isOpened():
    # Capturar frame de la cámara
    ret, frame = cap.read()
    if not ret:
        print("No se pudo leer el frame de la cámara.")
        break

    if show_annotated and annotated_frame is not None:
        # Mostrar la imagen anotada hasta que se presione 'p' nuevamente
        cv2.imshow("Live Feed", annotated_frame)
    else:
        # Mostrar el flujo en vivo
        cv2.imshow("Live Feed", frame)

    # Esperar entrada del teclado
    key = cv2.waitKey(1) & 0xFF

    if key == 27:  # Salir con ESC
        break
    elif key == ord('p'):  # Alternar entre Live Feed y Predicción
        if show_annotated:
            # Volver al Live Feed
            show_annotated = False
            print("Volviendo al Live Feed...")
        else:
            # Capturar el frame actual y realizar la predicción
            print("Realizando predicción...")
            frame_source, captured_frame = transform_image(frame)

            # Realizar predicción
            boxes, logits, phrases = predict(
                model=model,
                image=captured_frame,
                caption=TEXT_PROMPT,
                box_threshold=BOX_TRESHOLD,
                text_threshold=TEXT_TRESHOLD,
                device=device
            )

            # Anotar el frame
            annotated_frame = annotate(image_source=frame_source, boxes=boxes, logits=logits, phrases=phrases)

            # Guardar la imagen anotada (opcional)
            output_path = os.path.join(BASE_DIR, "computervision/live_annotated_image.jpg")
            annotated_bgr = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)  # Convertir a BGR
            cv2.imwrite(output_path, annotated_bgr)
            print(f"Predicción completada. Frases detectadas: {phrases}")

            # Cambiar al estado de "Mostrar Imagen Anotada"
            show_annotated = True

# Liberar recursos
cap.release()
cv2.destroyAllWindows()
