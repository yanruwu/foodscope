# ETL
## 1. Extracción de los datos
Para la extracción de los datos para este proyecto, se construyeron dos scrapeadores usando [Scrapy](https://scrapy.org/), uno para cada web de recetas seleccionada. En este caso las páginas son:
- allrecipes.com para recetas en inglés.
- directoalpaladar.com para recetas en español.

Se contruyeron dos spiders que almacenarán la información de cada una de las páginas:

```py
## ALLRECIPES
# Obtenemos la ruta absoluta del directorio donde está el script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ruta a la carpeta de datos dentro del mismo directorio del script
data_dir = os.path.join(BASE_DIR, "data")

# Creamos la carpeta "data" si no existe
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# Luego, ya usamos esa carpeta para leer/escribir el archivo
jsonl_path = os.path.join(data_dir, "allrecipes.jsonl")

urls = set(pd.read_json(jsonl_path, lines = True)["url"])

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
            'instrucciones': "".join(response.css('#mm-recipes-steps__content_1-0 li p *::text').getall())        }

```

```py
## DAP
urls = set(pd.read_json(r"C:\Proyecto-Final\recetas_scrapper\recetas_scrapper\recetas_dap.jsonl", lines = True)["url"])

class DapSpider(SitemapSpider):
    name = 'recetas_sitemap'
    allowed_domains = ['directoalpaladar.com']
    sitemap_urls = ['https://www.directoalpaladar.com/recipe/sitemap.xml']

    custom_settings = {
        "FEEDS": {
            "dap.jsonl": {"format": "jsonl", "encoding": "utf-8"}
        }
    }


    def sitemap_filter(self, entries):
        entries = list(entries)
        random.shuffle(entries) 
        for entry in entries:
            if entry["loc"] in urls:
                continue
            else:
                yield entry
    
    def parse(self, response):

        ingredient_container = response.css("ul.asset-recipe-list")[0]
        
        ingredientes_nombres = [
            e.css("span.asset-recipe-ingr-name span::text").get().strip()
            for e in ingredient_container.css("li")
        ]
        cantidades_unidades = [
            (
                float(a.css("span.asset-recipe-ingr-amount::text").get().strip()),
                a.css("span.asset-recipe-ingr-amount abbr::text").get()
            )
            if a.css("span.asset-recipe-ingr-amount") else None
            for a in ingredient_container.css("li")
        ]
        ingredient_dict = {
            "nombre": ingredientes_nombres,
            "cantidad": [i[0] if i else None for i in cantidades_unidades],
            "unidad": [i[1] if i else None for i in cantidades_unidades]
        }
        
        yield {
            'url': response.url,
            'titulo': response.css('h1.post-title::text').get().strip(),
            'ingredientes': ingredient_dict,
            'raciones' :  int(re.search(r'\d+', response.css('div.asset-recipe-yield::text').get().strip()).group(0)),
            'instrucciones': "".join(response.css('div.asset-recipe-steps p *::text').getall()),
            'dificultad' : response.css('div.asset-recipe-difficulty::text').get().replace("Dificultad: ", "").strip(),
        }
```