import torch
import clip
from PIL import Image

TEXT_PROMPT_LIST = [
    "potato", "onion", "garlic clove", "carrot", "tomato", "lettuce", "spinach", "cucumber", "zucchini", "broccoli",
    "cauliflower", "apple", "banana", "orange", "lemon", "grape", "pear", "peach", "plum", "watermelon", "pineapple",
    "strawberry", "blueberry", "raspberry", "blackberry", "mango", "kiwi", "avocado", "ginger", "parsley", "cilantro",
    "mint", "rosemary", "thyme", "basil", "bay leaf", "chili pepper", "mushroom", "green bean", "pea", "brussels sprout",
    "kale", "cabbage", "celery", "asparagus", "leek", "eggplant", "radish", "pumpkin", "butternut squash",
    "artichoke", "corn", "fig", "date", "papaya", "lime", "cherry", "coconut", "melon", "cantaloupe", "peanut", "almond", 
    "walnut", "chia seed", "sunflower seed", "sesame seed", "bread", "pasta", "blueberry", "celery"
    "chicken", "beef", "pork", "egg", "ham", "tofu", "milk", "yogurt", "cheese", "butter", "canned tuna", "canned salmon",
    "crushed tomato", "canned tomato", "chocolate", "rice", "lentil", "chickpeas", "black bean", "bell pepper", "sausage"
]

# Cargar modelo CLIP
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# Cargar imagen
image = preprocess(Image.open(r"computervision\bellpepper.jpg")).unsqueeze(0).to(device)

# Lista de etiquetas (puedes poner 50+ sin problemas)
labels = ["tomato", "cheese", "bread", "lettuce", "onion", "garlic", "chicken", "beef", "fish", "pepper",
          "carrot", "potato", "cucumber", "apple", "banana", "strawberry", "orange", "grape", "eggplant", "zucchini",
          "mushroom", "avocado", "blueberry", "raspberry", "cherry", "melon", "watermelon", "pineapple", "coconut",
          "mango", "pear", "plum", "kiwi", "papaya", "pomegranate", "fig", "dates", "lemon", "lime", "grapefruit",
          "almond", "walnut", "peanut", "cashew", "hazelnut", "pecan", "chestnut", "soybean", "tofu", "quinoa"]

labels = TEXT_PROMPT_LIST

# Tokenizar etiquetas
text_inputs = clip.tokenize(labels).to(device)

# Obtener embeddings de la imagen y las etiquetas
with torch.no_grad():
    image_features = model.encode_image(image)
    text_features = model.encode_text(text_inputs)

# Calcular similitud (más alto = mejor detección)
similarity = (image_features @ text_features.T).softmax(dim=-1)[0]

# **Filtrar etiquetas con un umbral de confianza**
threshold = 0.15  # Ajusta este valor según necesites
filtered_indices = (similarity > threshold).nonzero(as_tuple=True)[0]  # Obtener índices válidos

# Obtener etiquetas y sus scores correspondientes
filtered_labels = [labels[i] for i in filtered_indices.tolist()]
filtered_scores = similarity[filtered_indices].tolist()

# Ordenar etiquetas por confianza
sorted_results = sorted(zip(filtered_labels, filtered_scores), key=lambda x: x[1], reverse=True)

# Mostrar los resultados
print("Objetos detectados en la imagen:")
for label, score in sorted_results:
    print(f"- {label}: {score:.2f}")