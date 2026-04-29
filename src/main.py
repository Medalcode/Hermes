import os
import sys

import uvicorn

# Ensure project root is in pythonpath
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    print("🚀 Myna Web App (FastAPI) is starting...")
    # Import inside main to avoid path issues before sys.path append
    uvicorn.run("src.adapters.api.router:app", host="0.0.0.0", port=8000, reload=True)
