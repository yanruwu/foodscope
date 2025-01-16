# FoodScope: Optimización Inteligente de Recetas y Compras

## 1. Descripción del Caso de Negocio

### Contexto de la Empresa
FoodScope es una herramienta que combina inteligencia artificial y análisis de datos para ayudar a los consumidores a optimizar su experiencia culinaria y de compras. Su objetivo principal es sugerir recetas basadas en ingredientes disponibles y simplificar la adquisición de los faltantes en supermercados asociados.

### Problema que Afecta al Negocio
1. **Para los consumidores:**
   - Identificar los ingredientes disponibles en casa y planificar recetas puede ser tedioso.
   - Comprar los ingredientes faltantes sin salir de la receta resulta poco eficiente con las herramientas actuales.

2. **Para los supermercados:**
   - Falta de visibilidad sobre qué productos tienen mayor demanda para recetas específicas.
   - Oportunidades perdidas en la venta cruzada de ingredientes complementarios.

### Solución Propuesta
FoodScope se basa en:

1. **Clasificación Zero-Shot para Identificación de Ingredientes:** Uso de un modelo preentrenado que no requiere ajustes específicos para detectar ingredientes en imágenes.
2. **Recomendación de Recetas Basada en Ingredientes Detectados:** Enriquecida con información nutricional extraída de APIs.
3. **Posible conexión con Inventarios de Supermercados:** Los ingredientes faltantes pueden vincularse con productos disponibles, incluyendo precios.

---

## 2. Estructura del Proyecto

### 1. Scraping y APIs
- **Extracción de datos:**
   - APIs públicas como EDAMAM para información nutricional.
   - Scrapy para obtener datos de páginas web como AllRecipes o SeriousEats.

- **Procesamiento de datos:**
   - Limpieza, traducción y normalización para garantizar consistencia.
   - Almacenamiento en una base de datos relacional.

### 2. Base de Datos Relacional
- Almacenamiento de:
   - **Recetas:** Nombre, URL, instrucciones.
   - **Ingredientes:** Valores nutricionales y relación con recetas.

- Implementación en **PostgreSQL**.

### 3. Visión por Computadora
- Uso de un clasificador **zero-shot** para detectar y clasificar ingredientes en imágenes proporcionadas por los usuarios.
- Los ingredientes detectados se mapean con los disponibles en la base de datos.

### 4. Sistema de Recomendación
- **Recomendación Basada en Contenido:**
   - Sugerencia de recetas según los ingredientes detectados y las preferencias del usuario.
- **Conexión con Supermercados:**
   - Mapeo de ingredientes faltantes con productos en inventarios y sus precios.

---

## 3. Impacto de Negocio

### Para los consumidores
- **Optimización y Ahorro:** Planificación eficiente de comidas, maximizando el uso de ingredientes disponibles y simplificando la compra de faltantes.
- **Sostenibilidad:** Reducción del desperdicio alimentario.

### Para los supermercados
- **Incremento en ventas:** Promoción de productos faltantes para completar recetas.
- **Datos para la toma de decisiones:** Visibilidad sobre productos más demandados para ajustar inventarios.

---

## 4. Entregables del MVP
1. **Pipeline ETL Funcional:** 
   - Extracción, limpieza y almacenamiento de datos en una base de datos PostgreSQL.
2. **Clasificador Zero-Shot:** 
   - Sistema funcional para identificar ingredientes en imágenes sin necesidad de entrenamiento adicional.
3. **Sistema de Recomendación:** 
   - Sugerencias de recetas basadas en los ingredientes detectados, enriquecidas con datos de nutrición y precios.
