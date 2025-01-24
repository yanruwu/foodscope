import sys
import os
import pandas as pd

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from src.support_etl import *

# Configuración de rutas de archivos
jsonl_file_path = "recetas_scrapper/dap.jsonl"  # Ruta al archivo JSONL con las recetas
leftoff_file_path = "dap_leftoff.json"  # Archivo para guardar el progreso del ETL

# Crear archivo de progreso si no existe
if not os.path.exists(leftoff_file_path):
    with open(leftoff_file_path, "w", encoding="utf-8") as f:
        f.write('{"Position": 0}')

def main():
    """
    Función principal para ejecutar el proceso ETL de recetas.
    """
    try:
        print("Iniciando el proceso ETL...")
        
        # Ejecutar el proceso ETL
        process_recipes(
            file_path=jsonl_file_path,
            leftoff_path=leftoff_file_path,
            db_connection_func=connect_db
        )
        
        print("Proceso ETL completado con éxito.")
    except Exception as e:
        print(f"Error durante la ejecución del proceso ETL: {e}")

if __name__ == "__main__":
    main()
