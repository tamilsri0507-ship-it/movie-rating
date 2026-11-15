"""CineScope AI FastAPI Server Runner."""

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("  🎬 CineScope AI - Professional FastAPI Backend Server")
    print("  🎨 Theme: Light Lavender & Soft Purple (#F7F3FF / #7952B3)")
    print("  📖 Swagger UI Docs: http://127.0.0.1:8000/docs")
    print("  🌐 Web Dashboard:    http://127.0.0.1:8000/")
    print("=" * 60)
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
