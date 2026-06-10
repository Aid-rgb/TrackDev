#!/usr/bin/env python3
"""
Скрипт для запуска FastAPI сервера
"""
import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    """Запуск FastAPI сервера"""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    print("=" * 50)
    print("🚀 Redmine API Server")
    print("=" * 50)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Docs: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
    print("=" * 50)
    print("Для остановки нажмите Ctrl+C")
    print()
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
