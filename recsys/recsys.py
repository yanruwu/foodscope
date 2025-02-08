import sys
import os
import dotenv
import numpy as np



project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

dotenv.load_dotenv()
url = "https://zrhsejedrpoqcyfvfzsr.supabase.co"
key = os.getenv("db_API_pass")

from src.support_recsys import *

if __name__ == "__main__":
    ingredients = input("Introduzca una lista de ingredientes separados por espacios")
    print(get_filtered_recommendations(ingredients, url, key, [], 0, 1000))
