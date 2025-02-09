import scrapy
from scrapy.spiders import SitemapSpider
import random
import os
import pandas as pd

# Obtenemos la ruta absoluta del directorio donde está el script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ruta a la carpeta de datos dentro del mismo directorio del script
data_dir = os.path.join(BASE_DIR, "data")

# Creamos la carpeta "data" si no existe
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# Luego, ya usamos esa carpeta para leer/escribir el archivo
jsonl_path = os.path.join(data_dir, "allrecipes.jsonl")

if not os.path.exists(jsonl_path):
    with open(jsonl_path, "w", encoding="utf-8") as f:
        # Si quieres, puedes escribir algo inicial aquí
        pass

try:
    urls = set(pd.read_json(jsonl_path, lines = True)["url"])
except:
    urls = set()

class AllRecipesSpider(SitemapSpider):
    name = 'allrecipes'
    allowed_domains = ['allrecipes.com']
    sitemap_urls = ['https://www.allrecipes.com/sitemap_1.xml']

    custom_settings = {
        "FEEDS": {
            "allrecipes.jsonl": {"format": "jsonl", "encoding": "utf-8"}
        }
    }
    def sitemap_filter(self, entries):
        entries = list(entries)
        random.shuffle(entries)
        for entry in entries:
            if '/recipe/' in entry['loc']:
                if entry['loc'] in urls:
                    continue
                else:
                    yield entry

    def parse(self, response):
        
        ingredients = response.css('#mm-recipes-structured-ingredients_1-0 > ul > li')
        quantities = []
        units = []
        ing_names = []
        for ingredient in ingredients:
            quantities.append(ingredient.css('span[data-ingredient-quantity="true"]::text').get())
            units.append(ingredient.css('span[data-ingredient-unit="true"]::text').get())
            ing_names.append(ingredient.css('span[data-ingredient-name="true"]::text').get())
        ingredient_dict = {
            "nombre": ing_names,
            "cantidad": quantities,
            "unidad": units
        }
        servings = response.xpath(
        '//div[@class="mm-recipes-details__label" and normalize-space(text())="Servings:"]'
        '/following-sibling::div[@class="mm-recipes-details__value"]/text()').get()

        yield {
            'url': response.url,
            'titulo': response.xpath('//*[@id="article-header--recipe_1-0"]/h1/text()').get().strip(),
            'ingredientes': ingredient_dict,
            'sevings' : int(servings),
            'instrucciones': "".join(response.css('#mm-recipes-steps__content_1-0 li p *::text').getall()),
            'img_url' : response.xpath('//*[@id="gallery-photo_1-0"]/div/img@data-src').get()
            }
        