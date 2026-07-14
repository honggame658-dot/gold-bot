import os
import shutil

source_dir = r"C:\Users\ADMIN\Desktop\Gold"
target_dir = r"C:\Users\ADMIN\Desktop\Gold_To_Upload"

# Clean target directory if exists
if os.path.exists(target_dir):
    shutil.rmtree(target_dir)

os.makedirs(target_dir)

# Items to ignore
ignore_list = ['.env', 'bot_database.db', 'data', '__pycache__', '.git', '.vscode', 'Gold_To_Upload']

for item in os.listdir(source_dir):
    if item in ignore_list or item.endswith('.db') or item.endswith('.sqlite3'):
        continue
        
    s = os.path.join(source_dir, item)
    d = os.path.join(target_dir, item)
    
    if os.path.isdir(s):
        shutil.copytree(s, d, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    else:
        shutil.copy2(s, d)

print(f"✅ Safe files copied to: {target_dir}")
