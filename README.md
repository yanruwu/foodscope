# FoodScope: See Beyond the Plate

## Idea principal
Crear una herramienta de sugerencias de recetas con un input visual de predicción de ingredientes, con llamadas a una BBDD de recetas con detalles de estas e información sobre sus ingredientes. Incluiría información nutricional para complementar al sistema de recomendación y credenciales de usuario para crear un sistema más completo colaborativo.

## Estructura del Proyecto

### 1. Scraping
- Scrapy:

    Usar scrapy para diseñar crawlers capaces de scrapear páginas de recetas individualmente. Páginas como [allrecipes](https://www.allrecipes.com/) o [seriouseats](https://www.seriouseats.com/).

- APIs:

    Usar APIs como la API de [tasty](https://tasty.co/) o [yummly](https://www.yummly.com/) para extraer la información de las recetas.
 
Estos dos métodos permitirán obtener datos más diversos de diferentes fuentes. Las APIs están limitadas a las que estén disponibles, mientras que usando webscraping se podría extraer información de cualquier página de receta existente.

### 2. Tratar Datos
- A partir de la información de las APIs, seguir la estructura del json para extraer la información útil y almacenarla en distintos dataframes.

- A partir de la información del webscraping, normalizar y limpiar el contenido, estructurarlos en dataframes e igualar la información con la obtenida en APIs.

Con ambas fuentes se obtendrán los diferentes ingredientes disponibles en las recetas, los cuales comformarán su propio dataframe, donde incluiremos:

- Nombre del ingrediente
- Información nutricional, extraída por herramientas como EDAMAM API, la cual permite obtener los datos nutricionales de los ingredientes.

A partir de aquí se calcularían índices de salud para cada receta, el cual nos servirá para categorizar cada una de estas.

### 3. Cargar Datos
Crearemos una BBDD en PostgreSQL, donde cargaremos toda la información de cada tabla que hayamos creado. 

### Diseño de la base de datos

```mermaid
erDiagram
    RECIPES {
        bigint id PK
        text name
        text url
        text description
    }
    INGREDIENTS {
        bigint id PK
        text name
        numeric calories
        numeric proteins
        numeric carbs
        numeric fats
    }
    RECIPE_INGREDIENTS {
        bigint id PK
        bigint recipe_id FK
        bigint ingredient_id FK
        numeric amount
        text unit
    }
    STEPS {
        bigint id PK
        bigint recipe_id FK
        int step_number
        text description
    }
    CATEGORIES {
        bigint id PK
        text name
    }
    RECIPE_CATEGORIES {
        bigint id PK
        bigint recipe_id FK
        bigint category_id FK
    }
    USERS {
        bigint id PK
        text username
        text email
        text password_hash
    }
    USER_FAVORITES {
        bigint id PK
        bigint user_id FK
        bigint recipe_id FK
    }
    COMMENTS {
        bigint id PK
        bigint recipe_id FK
        bigint user_id FK
        text comment_text
        timestamptz created_at
    }
    TAGS {
        bigint id PK
        text name
    }
    RECIPE_TAGS {
        bigint id PK
        bigint recipe_id FK
        bigint tag_id FK
    }

    RECIPES ||--o{ RECIPE_INGREDIENTS : contains
    INGREDIENTS ||--o{ RECIPE_INGREDIENTS : used_in
    RECIPES ||--o{ STEPS : has
    RECIPES ||--o{ RECIPE_CATEGORIES : categorized_as
    CATEGORIES ||--o{ RECIPE_CATEGORIES : includes
    USERS ||--o{ USER_FAVORITES : favorites
    RECIPES ||--o{ USER_FAVORITES : favorited_by
    RECIPES ||--o{ COMMENTS : receives
    USERS ||--o{ COMMENTS : writes
    RECIPES ||--o{ RECIPE_TAGS : tagged_as
    TAGS ||--o{ RECIPE_TAGS : includes
```

