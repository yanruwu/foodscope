from transformers import OwlViTProcessor, OwlViTForObjectDetection
from PIL import Image
import torch

# Cargar modelo y procesador en CPU
model = OwlViTForObjectDetection.from_pretrained("google/owlvit-base-patch32").to("cpu")
processor = OwlViTProcessor.from_pretrained("google/owlvit-base-patch32")

# Cargar imagen
image = Image.open('computervision/tomato.jpg')

# Lista de etiquetas para detectar
text_queries = [["tomato", "cheese", "bread", "yogurt", "chicken", "banana", "onion"]]

# Preprocesar la imagen y ejecutar inferencia
inputs = processor(images=image, text=text_queries, return_tensors="pt")
outputs = model(**inputs)

# Extraer bounding boxes, confianza y etiquetas detectadas
scores = outputs["logits"].sigmoid().detach().cpu()  # Confianza
boxes = outputs["pred_boxes"].detach().cpu()  # Coordenadas de los bounding boxes

# Umbral de confianza (ajústalo si detecta falsos positivos)
threshold = 0.01

# Obtener detecciones con confianza alta
detected_objects = []
for i, query in enumerate(text_queries[0]):  # Iterar sobre las etiquetas
    for j, score in enumerate(scores[0, i]):  # Iterar sobre cada predicción de la etiqueta
        if score > threshold:
            box = boxes[0, j].tolist()
            detected_objects.append((query, score.item(), box))

# Mostrar resultados
print("\n🔹 **Objetos detectados en la imagen:**")
for obj, conf, bbox in detected_objects:
    print(f"- {obj}: {conf:.2f} (Bounding Box: {bbox})")
