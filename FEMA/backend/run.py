import sys
import uvicorn
from app.config import settings

if __name__ == "__main__":
    reload = "--no-reload" not in sys.argv
    print(f"Starting {settings.APP_NAME} on {settings.HOST}:{settings.PORT} (reload={reload})...")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=reload,
        reload_dirs=["app"] if reload else None,
        reload_excludes=["*.db*", "*.sqlite*", "*data*", "*.json", "*.log", "__pycache__"] if reload else None,
        log_level=settings.LOG_LEVEL.lower()
    )
