import sys
import os
import dotenv
from bs4 import BeautifulSoup


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

dotenv.load_dotenv()


from src.support_etl import *

# Configuración de rutas de archivos
jsonl_file_path = "recetas_scrapper/recetas_scrapper/spiders/data/dap.jsonl"  # Ruta al archivo JSONL con las recetas
leftoff_file_path = "dap_leftoff.json"  # Archivo para guardar el progreso del ETL

# Crear archivo de progreso si no existe
if not os.path.exists(leftoff_file_path):
    with open(leftoff_file_path, "w", encoding="utf-8") as f:
        f.write('{"Position": 0}')

def images():
    supabase = get_supabase_client()
    print("Insertando imágenes faltantes")
    n_img = 0
    for e in supabase.table("recipes").select("url").is_("img_url", None).execute().data:
        response = requests.get(e["url"])
        soup = BeautifulSoup(response.content, 'html.parser')
        img = soup.find('img')["src"]
        supabase.table("recipes").update({"img_url": img}).eq("url", e["url"]).execute()
        n_img += 1
    print(f"Se han insertado {n_img} imágenes")

def main():
    """
    Función principal para ejecutar el proceso ETL de recetas.
    """
    images()    
    try:
        print("Iniciando el proceso ETL...")
        
        # Ejecutar el proceso ETL
        process_recipes(
            file_path=jsonl_file_path,
            leftoff_path=leftoff_file_path,
        )
        
        print("Proceso ETL completado con éxito.")
    except Exception as e: 
        print(f"Error durante la ejecución del proceso ETL: {e}")
    except KeyboardInterrupt:
        images()

if __name__ == "__main__":
    main()