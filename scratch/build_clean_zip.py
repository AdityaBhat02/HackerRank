import os
import shutil
import zipfile

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
code_dir = os.path.join(repo_root, "code")
zip_path = os.path.join(repo_root, "code.zip")

# Remove any duplicate zip inside code/
if os.path.exists(os.path.join(code_dir, "code.zip")):
    try:
        os.remove(os.path.join(code_dir, "code.zip"))
    except Exception:
        pass

# Remove any __pycache__ or .pyc before zipping
for root, dirs, files in os.walk(code_dir):
    for d in list(dirs):
        if d == "__pycache__":
            shutil.rmtree(os.path.join(root, d), ignore_errors=True)
            dirs.remove(d)
    for f in files:
        if f.endswith((".pyc", ".pyo")):
            try:
                os.remove(os.path.join(root, f))
            except Exception:
                pass

# Create root code.zip
if os.path.exists(zip_path):
    os.remove(zip_path)

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(code_dir):
        # Exclude pycache and hidden dirs
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
        for file in files:
            if file.endswith((".pyc", ".pyo", ".zip", ".env")):
                continue
            full_path = os.path.join(root, file)
            # Store relative path inside zip starting at code/ contents (NOT nested under code/)
            rel_path = os.path.relpath(full_path, code_dir)
            zf.write(full_path, rel_path)

print(f"Created clean root {zip_path}")
print("Contents of code.zip (Root layout):")
with zipfile.ZipFile(zip_path, "r") as zf:
    for info in zf.infolist():
        print(f"  {info.filename} ({info.file_size} bytes)")
