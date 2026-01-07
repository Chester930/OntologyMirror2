import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import json
import chromadb
from typing import List, Dict, Any

# --- Configuration & Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DEFAULT_JSONLD_PATH = os.path.join(DATA_DIR, "knowledge_base", "schemaorg-current-https.jsonld")
VECTOR_DB_PATH = os.path.join(DATA_DIR, "vector_store")

# --- Core Logic: Build Vector Store ---

def build_vector_store(jsonld_path=DEFAULT_JSONLD_PATH, vector_db_path=VECTOR_DB_PATH, log_callback=print):
    """
    Parses JSON-LD and rebuilds the ChromaDB vector store.
    log_callback: Function to handle logging output (e.g., print or gui_log)
    """
    log_callback(f"正在從 {jsonld_path} 建立向量資料庫...")
    
    if not os.path.exists(jsonld_path):
        raise FileNotFoundError(f"找不到 JSON-LD 檔案: {jsonld_path}")

    # 1. Load JSON-LD
    try:
        with open(jsonld_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            graph = data.get('@graph', [])
            log_callback(f"已從 JSON-LD 載入 {len(graph)} 個節點。")
    except Exception as e:
        raise Exception(f"讀取 JSON-LD 時發生錯誤: {e}")

    # 2. Extract Classes and Properties
    documents = []
    metadatas = []
    ids = []
    
    count = 0
    for node in graph:
        node_id = node.get('@id', '')
        node_type = node.get('@type', '')
        
        # Filter for Classes and Properties
        is_class = 'rdfs:Class' in node_type or node_type == 'rdfs:Class'
        is_property = 'rdf:Property' in node_type or node_type == 'rdf:Property'
        
        if not (is_class or is_property):
            continue
            
        label = node.get('rdfs:label', '')
        if isinstance(label, dict): label = label.get('@value', '')
        
        comment = node.get('rdfs:comment', '')
        if isinstance(comment, dict): comment = comment.get('@value', '')
        
        # Create a rich text representation for embedding
        type_label = "Class" if is_class else "Property"
        content = f"{type_label}: {label}\nDescription: {comment}"
        
        # Add domain/range info for properties if available
        if is_property:
            def get_ids(field_name):
                val = node.get(field_name)
                if isinstance(val, dict):
                    return val.get('@id', '')
                elif isinstance(val, list):
                    return ', '.join([v.get('@id', '') for v in val if isinstance(v, dict)])
                return ''

            domain = get_ids('schema:domainIncludes')
            range_val = get_ids('schema:rangeIncludes')
            
            if domain: content += f"\nDomain: {domain}"
            if range_val: content += f"\nRange: {range_val}"

        if not node_id: continue

        documents.append(content)
        metadatas.append({
            "id": node_id,
            "label": str(label), 
            "source": "schema.org",
            "type": type_label
        })
        ids.append(node_id)
        count += 1

    log_callback(f"已處理 {count} 個有效項目 (類別/屬性)。")

    # 3. Initialize ChromaDB
    try:
        client = chromadb.PersistentClient(path=vector_db_path)
        # Delete existing to ensure fresh rebuild
        try:
             client.delete_collection("schema_org_classes")
        except:
             pass
        collection = client.get_or_create_collection(name="schema_org_classes")
        
        # Batch upsert
        batch_size = 5000 
        total_batches = (len(ids) + batch_size - 1) // batch_size
        
        log_callback(f"正在分 {total_batches} 批次匯入 ChromaDB...")
        
        for i in range(0, len(ids), batch_size):
            end = min(i + batch_size, len(ids))
            log_callback(f"批次 {i//batch_size + 1}/{total_batches}...")
            collection.upsert(
                documents=documents[i:end],
                metadatas=metadatas[i:end],
                ids=ids[i:end]
            )
            
        log_callback(f"成功！已於 {vector_db_path} 建立向量資料庫")
        log_callback(f"資料庫中總項目數: {collection.count()}")
        
    except Exception as e:
        raise Exception(f"使用 ChromaDB 時發生錯誤: {e}")


# --- GUI Implementation ---

class KBManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OntologyMirror 知識庫管理工具 (KB Manager)")
        self.root.geometry("600x400")
        
        self._init_ui()
        self._check_status()

    def _init_ui(self):
        # Header
        tk.Label(self.root, text="知識庫管理", font=("Microsoft JhengHei", 14, "bold"), pady=10).pack()
        
        # Status Frame
        status_frame = tk.LabelFrame(self.root, text="目前狀態", padx=10, pady=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = tk.Label(status_frame, text="檢查中...", fg="gray", font=("Microsoft JhengHei", 10))
        self.status_label.pack(anchor="w")
        
        # Actions Frame
        action_frame = tk.LabelFrame(self.root, text="更新知識庫 (Update Knowledge Base)", padx=10, pady=10)
        action_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(action_frame, text="選擇來源檔案 (JSON-LD):").pack(anchor="w")
        
        file_frame = tk.Frame(action_frame)
        file_frame.pack(fill=tk.X, pady=5)
        
        self.file_var = tk.StringVar(value=DEFAULT_JSONLD_PATH)
        tk.Entry(file_frame, textvariable=self.file_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(file_frame, text="瀏覽...", command=self._browse_file).pack(side=tk.LEFT, padx=5)
        
        self.build_btn = tk.Button(action_frame, text="重建向量資料庫 (Rebuild)", command=self._on_build, 
                                 bg="#2196f3", fg="white", font=("Microsoft JhengHei", 10, "bold"), height=2)
        self.build_btn.pack(fill=tk.X, pady=10)
        
        # Log
        self.log_text = tk.Text(self.root, height=8, bg="#f0f0f0", state="disabled")
        self.log_text.pack(fill=tk.BOTH, padx=10, pady=5)

    def _log(self, msg):
        def _update():
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, str(msg) + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")
        self.root.after(0, _update)

    def _browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON-LD", "*.jsonld"), ("All Files", "*.*")])
        if filename:
            self.file_var.set(filename)

    def _check_status(self):
        if not os.path.exists(VECTOR_DB_PATH):
            self.status_label.config(text="狀態: 未初始化 (資料夾不存在)", fg="red")
            return
            
        try:
            client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
            # Check for standard collection
            try:
                col = client.get_collection("schema_org_classes")
                count = col.count()
                self.status_label.config(text=f"狀態: 就緒 (包含 {count} 個項目)", fg="green")
            except:
                 self.status_label.config(text="狀態: 已初始化但內容為空", fg="orange")
        except Exception as e:
            self.status_label.config(text=f"狀態: 錯誤 ({str(e)})", fg="red")

    def _on_build(self):
        path = self.file_var.get()
        if not os.path.exists(path):
            messagebox.showerror("錯誤", "找不到檔案!")
            return
            
        if not messagebox.askyesno("確認重建", 
                                   "這將會刪除現有的 Vector Store 並重新建立。\n"
                                   "過程可能需要幾分鐘。\n\n確定要繼續嗎?"):
            return

        self._log(f"開始重建，來源: {path}...")
        self.build_btn.config(state="disabled", text="處理中... (Building)")
        
        # Run in thread to not freeze UI
        threading.Thread(target=self._run_build, args=(path,), daemon=True).start()

    def _run_build(self, jsonld_path):
        try:
            # Pass our GUI logging function as callback
            build_vector_store(jsonld_path=jsonld_path, vector_db_path=VECTOR_DB_PATH, log_callback=self._log)
            self.root.after(0, self._on_build_complete, True, "重建完成 (Rebuild Complete)!")
        except Exception as e:
            self.root.after(0, self._on_build_complete, False, str(e))

    def _on_build_complete(self, success, msg):
        self.build_btn.config(state="normal", text="重建向量資料庫 (Rebuild)")
        if success:
            self._log("SUCCESS: " + msg)
            messagebox.showinfo("完成", msg)
        else:
            self._log("ERROR: " + msg)
            messagebox.showerror("錯誤", msg)
        
        self._check_status()

if __name__ == "__main__":
    root = tk.Tk()
    app = KBManagerApp(root)
    root.mainloop()
