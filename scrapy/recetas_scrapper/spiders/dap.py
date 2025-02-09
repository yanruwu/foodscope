from scrapy.spiders import SitemapSpider
import random
import pandas as pd
import os
import re

# Obtenemos la ruta absoluta del directorio donde está el script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ruta a la carpeta de datos dentro del mismo directorio del script
data_dir = os.path.join(BASE_DIR, "data")

# Creamos la carpeta "data" si no existe
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# Luego, ya usamos esa carpeta para leer/escribir el archivo
jsonl_path = os.path.join(data_dir, "dap.jsonl")

if not os.path.exists(jsonl_path):
    with open(jsonl_path, "w", encoding="utf-8") as f:
        # Si quieres, puedes escribir algo inicial aquí
        pass

try:
    urls = set(pd.read_json(jsonl_path, lines = True)["url"])
except:
    urls = set()

class DapSpider(SitemapSpider):
    """
    Spider de Scrapy que rastrea el sitio directoalpaladar.com. Usa un sitemap principal
    para encontrar URLs de recetas. Filtra las URLs ya visitadas y extrae la siguiente 
    información de cada página:
      - título de la receta
      - ingredientes (nombre, cantidad y unidad)
      - número de raciones
      - instrucciones
      - dificultad
    """

    name = 'dap'
    allowed_domains = ['directoalpaladar.com']
    sitemap_urls = ['https://www.directoalpaladar.com/recipe/sitemap.xml']

    custom_settings = {
        "FEEDS": {
            "dap.jsonl": {"format": "jsonl", "encoding": "utf-8"}
        }
    }

    def sitemap_filter(self, entries):
        """
        Toma las entradas del sitemap, las desordena (random.shuffle) y omite las que ya
        estén en el conjunto 'urls'. Devuelve solamente las URLs nuevas.
        
        :param entries: Iterable con las entradas del sitemap.
        :yield: Entradas filtradas que no se han visitado previamente.
        """
        entries = list(entries)
        random.shuffle(entries)
        for entry in entries:
            if entry["loc"] in urls:
                continue
            else:
                yield entry

    def parse(self, response):
        """
        Parse de la respuesta de cada URL filtrada, extrayendo:
            - Título de la receta (h1.post-title)
            - Ingredientes (nombres, cantidades, unidades) dentro de la lista ul.asset-recipe-list
            - Raciones (número entero en div.asset-recipe-yield)
            - Instrucciones (div.asset-recipe-steps)
            - Dificultad (div.asset-recipe-difficulty)

        :param response: Objeto de respuesta de Scrapy con el HTML de la página.
        :return: Diccionario con la información extraída.
        """
        # Contenedor de ingredientes
        ingredient_container = response.css("ul.asset-recipe-list")[0]

        # Extraemos los nombres de cada ingrediente
        ingredientes_nombres = [
            e.css("span.asset-recipe-ingr-name span::text").get().strip()
            for e in ingredient_container.css("li")
        ]

        # Extraemos (cantidad, unidad) o None si no hay
        cantidades_unidades = [
            (
                float(a.css("span.asset-recipe-ingr-amount::text").get().strip()),
                a.css("span.asset-recipe-ingr-amount abbr::text").get()
            )
            if a.css("span.asset-recipe-ingr-amount") else None
            for a in ingredient_container.css("li")
        ]

        # Construimos el diccionario de ingredientes
        ingredient_dict = {
            "nombre": ingredientes_nombres,
            "cantidad": [i[0] if i else None for i in cantidades_unidades],
            "unidad": [i[1] if i else None for i in cantidades_unidades]
        }

        # Retornamos la información de la receta
        yield {
            'url': response.url,
            'titulo': response.css('h1.post-title::text').get().strip(),
            'ingredientes': ingredient_dict,
            'raciones': int(re.search(r'\d+', response.css('div.asset-recipe-yield::text').get().strip()).group(0)),
            'instrucciones': "".join(response.css('div.asset-recipe-steps p *::text').getall()),
            'dificultad': response.css('div.asset-recipe-difficulty::text').get().replace("Dificultad: ", "").strip(),
        }