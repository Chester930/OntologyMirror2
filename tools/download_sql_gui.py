import tkinter as tk
from tkinter import messagebox
import os
import sys
import threading
import shutil
import tempfile
import glob
from git import Repo

# Function to handle the actual downloading logic (Merged from tools/download_sql.py)
def parse_github_url(url):
    """
    Parses a GitHub URL into (repo_root, branch, sub_path).
    
    Supports:
    - https://github.com/user/repo
    - https://github.com/user/repo.git
    - https://github.com/user/repo/tree/branch/path/to/dir
    """
    if not url.startswith("http"):
        return url, None, None
        
    parts = url.rstrip("/").split("/")
    # Check if accessing a sub-path via 'tree'
    # Format: .../repo/tree/branch/path...
    try:
        if "tree" in parts:
            tree_index = parts.index("tree")
            # Repo root is everything before 'tree'
            repo_parts = parts[:tree_index]
            repo_root = "/".join(repo_parts)
            
            # Branch and path
            # parts[tree_index] is 'tree'
            # parts[tree_index+1] is branch
            # parts[tree_index+2:] is path
            if len(parts) > tree_index + 1:
                branch = parts[tree_index + 1]
                sub_path = "/".join(parts[tree_index + 2:]) if len(parts) > tree_index + 2 else ""
                return repo_root, branch, sub_path
    except:
        pass
        
    return url, None, None

def download_sql_files(url, target_dir):
    """
    Clones a GitHub repository (handling sub-paths) and copies valid .sql files.
    """
    # Create target directory if it doesn't exist
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"Created directory: {target_dir}")

    repo_url, branch, sub_path = parse_github_url(url)
    print(f"Parsed URL: Repo={repo_url}, Branch={branch}, Path={sub_path}")

    # Create a temporary directory for cloning
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Cloning {repo_url} into temporary directory...")
        
        # Prepare clone kwargs
        clone_kwargs = {'depth': 1}
        if branch:
            clone_kwargs['branch'] = branch
            
        try:
            Repo.clone_from(repo_url, temp_dir, **clone_kwargs)
        except Exception as e:
            # Fallback: Maybe depth=1 failed with specific branch, try full clone or default branch
            print(f"Shallow clone failed ({e}), trying full clone without branch spec...")
            Repo.clone_from(repo_url, temp_dir)

        # Determine search root
        search_dir = temp_dir
        if sub_path:
            search_dir = os.path.join(temp_dir, sub_path)
            if not os.path.exists(search_dir):
                print(f"Warning: Sub-path '{sub_path}' not found in repo.")
                # Fallback to searching whole repo if path is wrong
                search_dir = temp_dir

        print(f"Searching for .sql files in: {sub_path if sub_path else 'root'}...")
        sql_files = []
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                if file.endswith(".sql"):
                    sql_files.append(os.path.join(root, file))

        if not sql_files:
            raise Exception("在此路徑下找不到任何 .sql 檔案 (No .sql files found).")

        print(f"Found {len(sql_files)} .sql file(s). Copying to {target_dir}...")
        
        count = 0
        for file_path in sql_files:
            file_name = os.path.basename(file_path)
            
            # Check for name collision
            target_path = os.path.join(target_dir, file_name)
            base, extension = os.path.splitext(file_name)
            counter = 1
            while os.path.exists(target_path):
                target_path = os.path.join(target_dir, f"{base}_{counter}{extension}")
                counter += 1
            
            shutil.copy2(file_path, target_path)
            count += 1
            print(f"Saved: {os.path.basename(target_path)}")

    return count

def run_download_thread():
    """Runs the download in a separate thread to keep UI responsive."""
    url = url_entry.get().strip()
    if not url:
        messagebox.showwarning("輸入錯誤", "請輸入 GitHub 儲存庫網址。")
        return

    btn_download.config(state=tk.DISABLED, text="下載中... (下載可能會花一點時間)")
    status_label.config(text="狀態: 分析並下載中...", fg="blue")
    
    # Run the actual work in a separate thread
    thread = threading.Thread(target=perform_download, args=(url,))
    thread.start()

def perform_download(url):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Define output directory relative to the project root
        # tools/ -> project_root -> data/download sql
        project_root = os.path.dirname(current_dir)
        target_dir = os.path.join(project_root, "data", "download sql")
        
        # Ensure target dir exists (tool handles it, but good to be explicit/show path)
        count = download_sql_files(url, target_dir)
        
        # Update UI in main thread
        root.after(0, lambda: on_success(target_dir, count))
    except Exception as e:
        root.after(0, lambda: on_error(str(e)))

def on_success(target_dir, count):
    btn_download.config(state=tk.NORMAL, text="下載 SQL 檔案")
    status_label.config(text="狀態: 完成!", fg="green")
    messagebox.showinfo("下載成功", f"成功下載 {count} 個 .sql 檔案!\n檔案已儲存至:\n{target_dir}")

def on_error(error_msg):
    btn_download.config(state=tk.NORMAL, text="下載 SQL 檔案")
    status_label.config(text="狀態: 錯誤", fg="red")
    messagebox.showerror("下載錯誤", f"發生錯誤:\n{error_msg}")

# GUI Setup
root = tk.Tk()
root.title("OntologyMirror SQL 下載器 (支援 GitHub 子目錄)")
root.geometry("600x200")
root.resizable(False, False)

# Main Container
main_frame = tk.Frame(root, padx=20, pady=20)
main_frame.pack(fill=tk.BOTH, expand=True)

# URL Label and Entry
tk.Label(main_frame, text="GitHub 儲存庫網址 (Repository URL):").pack(anchor="w")
url_entry = tk.Entry(main_frame, font=("Arial", 10))
url_entry.pack(fill=tk.X, pady=(5, 15))

# Download Button
btn_download = tk.Button(main_frame, text="下載 SQL 檔案", command=run_download_thread, height=2, bg="#f0f0f0")
btn_download.pack(fill=tk.X)

# Status Label
status_label = tk.Label(main_frame, text="狀態: 就緒", pady=10, fg="gray")
status_label.pack()

if __name__ == "__main__":
    root.mainloop()
