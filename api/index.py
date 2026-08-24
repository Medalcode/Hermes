import os
import sys

# Add the project root to the sys.path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.adapters.api.router import app  # noqa: F401
