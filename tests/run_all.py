"""
run_all.py — Convenient runner for Nexventory E2E Playwright tests.
Ensures correct environment paths and runs pytest on tests/e2e.
"""
import os
import sys
import subprocess

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    browsers_dir = os.path.join(root_dir, ".browsers")
    tmp_dir = os.path.join(root_dir, ".tmp")
    
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_dir
    os.environ["TEMP"] = tmp_dir
    os.environ["TMP"] = tmp_dir
    
    venv_python = os.path.join(root_dir, ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = sys.executable
        
    cmd = [
        venv_python,
        "-m", "pytest",
        os.path.join(root_dir, "tests", "e2e"),
        "-v",
        "--tb=short"
    ] + sys.argv[1:]
    
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
