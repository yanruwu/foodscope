import sys
import os



project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from src.support_recsys import *

print(get_recommendations("onion tomato garlic ginger salt oil", 5))