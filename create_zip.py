"""
ZIP Packaging Utility for Gandiva Tunes.
Creates Gandiva_Tunes_Bot.zip containing the full deployment-ready project.
Credits: Syko Reddy
"""

import os
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ZIP_NAME = "Gandiva_Tunes_Bot.zip"
ZIP_PATH = BASE_DIR / ZIP_NAME

EXCLUDE_DIRS = {".git", "__pycache__", ".vscode", ".idea", ".pytest_cache"}
EXCLUDE_FILES = {ZIP_NAME, ".env", "gandiva_tunes.db", "gandiva_tunes.db-journal"}
EXCLUDE_EXTS = {".pyc", ".pyo", ".pyd"}


def create_zip():
    print(f"Creating {ZIP_NAME}...")
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BASE_DIR):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(BASE_DIR)

                if file in EXCLUDE_FILES or file_path.suffix in EXCLUDE_EXTS:
                    continue

                zipf.write(file_path, rel_path)
                print(f"  + Added: {rel_path}")

    size_kb = ZIP_PATH.stat().st_size / 1024
    print(f"\n[✓] Successfully packaged {ZIP_NAME} ({size_kb:.2f} KB) at:\n    {ZIP_PATH}")


if __name__ == "__main__":
    create_zip()
