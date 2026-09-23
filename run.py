import uvicorn
import webbrowser
import threading
import time

def open_browser():
    time.sleep(1.5)
    print("\n[GeoGuide] Launching in your default browser at http://localhost:8000 ...")
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 GeoGuide: Location-Aware AI Place Companion")
    print("KogniVera Hackathon 2026 - Team Ctrl+Alt+Defeat")
    print("=" * 60)
    print("Starting FastAPI + SQLite + RAG Grounded Backend & Web App...")
    
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)
