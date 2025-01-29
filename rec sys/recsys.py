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

print(get_filtered_recommendations("eggs butter flour", url, key, [], 0, 1000))
