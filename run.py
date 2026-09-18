"""
Unified Development Launcher for RoadDamageAI.
Starts FastAPI backend server on http://localhost:8000
and Vite React frontend on http://localhost:5173 concurrently.
"""

import subprocess
import sys
import os
import time
import signal

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")

    print("=" * 65)
    print("  ROADDAMAGE AI - Intelligent Road Infrastructure Platform")
    print("  Hackathon Problem M15 Solution")
    print("=" * 65)
    print("Starting Backend API server (FastAPI + Uvicorn)...")

    # Start backend
    backend_cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    backend_proc = subprocess.Popen(backend_cmd, cwd=root_dir)

    time.sleep(2)

    print("Starting Frontend Development server (Vite + React)...")
    # Start frontend (using npx vite or npm run dev)
    frontend_cmd = ["npm.cmd" if os.name == "nt" else "npm", "run", "dev"]
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=frontend_dir)

    print("\n" + "=" * 65)
    print("  SYSTEM RUNNING:")
    print("  -> Web Dashboard:  http://localhost:5173")
    print("  -> API Swagger:    http://localhost:8000/docs")
    print("  -> Sample API:     http://localhost:8000/api/demo-samples")
    print("  Press Ctrl+C to terminate both servers.")
    print("=" * 65 + "\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
        backend_proc.wait()
        frontend_proc.wait()
        print("All servers stopped successfully.")

if __name__ == "__main__":
    main()
