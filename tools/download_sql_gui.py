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
def download_sql_files(repo_url, target_dir):
    """
    Clones a GitHub repository and copies all .sql files to the target directory.
    """
    # Create target directory if it doesn't exist
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"Created directory: {target_dir}")

    # Create a temporary directory for cloning
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Cloning {repo_url} into temporary directory...")
        # Shallow clone for speed (depth=1)
        Repo.clone_from(repo_url, temp_dir, depth=1)

        print("Searching for .sql files...")
        sql_files = []
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith(".sql"):
                    sql_files.append(os.path.join(root, file))

        if not sql_files:
            print("No .sql files found in the repository.")
            return

        print(f"Found {len(sql_files)} .sql file(s). Copying to {target_dir}...")
        
        for file_path in sql_files:
            file_name = os.path.basename(file_path)
            # Handle duplicate filenames by prepending parent folder name if needed
            # For this simple version, we'll just increment a counter if collision
            target_path = os.path.join(target_dir, file_name)
            
            base, extension = os.path.splitext(file_name)
            counter = 1
            while os.path.exists(target_path):
                target_path = os.path.join(target_dir, f"{base}_{counter}{extension}")
                counter += 1
            
            shutil.copy2(file_path, target_path)
            print(f"Saved: {os.path.basename(target_path)}")

    print("Done!")

def run_download_thread():
    """Runs the download in a separate thread to keep UI responsive."""
    url = url_entry.get().strip()
    if not url:
        messagebox.showwarning("輸入錯誤", "請輸入 GitHub 儲存庫網址。")
        return

    btn_download.config(state=tk.DISABLED, text="下載中... (Downloading)")
    status_label.config(text="狀態: 複製並搜尋中...", fg="blue")
    
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
        download_sql_files(url, target_dir)
        
        # Update UI in main thread (using thread-safe methods would be better but for simple GUI this usually works or use queue)
        # Tkinter is not thread-safe, so we should schedule the update using after()
        root.after(0, lambda: on_success(target_dir))
    except Exception as e:
        root.after(0, lambda: on_error(str(e)))

def on_success(target_dir):
    btn_download.config(state=tk.NORMAL, text="下載 SQL 檔案")
    status_label.config(text="狀態: 完成!", fg="green")
    messagebox.showinfo("成功", f"下載完成!\n檔案已儲存至:\n{target_dir}")

def on_error(error_msg):
    btn_download.config(state=tk.NORMAL, text="下載 SQL 檔案")
    status_label.config(text="狀態: 錯誤", fg="red")
    messagebox.showerror("錯誤", f"發生錯誤:\n{error_msg}")

# GUI Setup
root = tk.Tk()
root.title("OntologyMirror SQL 下載器")
root.geometry("500x180")
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
