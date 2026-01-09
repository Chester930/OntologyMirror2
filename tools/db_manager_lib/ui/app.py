import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import os
import threading
from tools.db_manager_lib.ui.dialogs import DBConnectionDialog
from tools.db_manager_lib.core.importer import ImportManager

CONNECTIONS_FILE = "db_connections.json"

class DBManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OntologyMirror 資料庫管理工具")
        self.root.geometry("900x600")
        
        # Paths
        self.current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # tools/ui -> tools -> root
        # Actually simplest to trust "db_connections.json" is in CWD or relative to script entry
        self.connections = self.load_connections()
        self.connector = None
        self.importer = ImportManager(os.path.dirname(os.path.abspath(__file__)))
        
        self._init_ui()

    def _init_ui(self):
        # Top Frame: Connection List
        top_frame = tk.Frame(self.root, padx=10, pady=10)
        top_frame.pack(fill=tk.X)
        
        tk.Label(top_frame, text="已儲存的連線:").pack(side=tk.LEFT)
        self.conn_combo = ttk.Combobox(top_frame, state="readonly", width=30)
        self.conn_combo.pack(side=tk.LEFT, padx=5)
        self.conn_combo.bind("<<ComboboxSelected>>", self.on_select_connection)
        
        tk.Button(top_frame, text="新增連線", command=self.add_connection, bg="#f0f0f0").pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text="匯入 SQL (.sql)", command=self.import_sql, bg="#fff9c4").pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text="編輯", command=self.edit_connection).pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text="刪除", command=self.delete_connection).pack(side=tk.LEFT, padx=2)
        
        self.type_label = tk.Label(top_frame, text="", fg="gray")
        self.type_label.pack(side=tk.LEFT, padx=10)

        # Middle Frame: Actions
        action_frame = tk.Frame(self.root, padx=10, pady=5)
        action_frame.pack(fill=tk.X)
        tk.Button(action_frame, text="連線並查看資料庫", command=self.connect_and_inspect, 
                  bg="#4caf50", fg="white", font=("Microsoft JhengHei", 10, "bold"), height=2).pack(fill=tk.X)

        # Bottom Frame: Inspection Results
        bottom_frame = tk.Frame(self.root, padx=10, pady=10)
        bottom_frame.pack(fill=tk.BOTH, expand=True)

        paned_window = tk.PanedWindow(bottom_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.LabelFrame(paned_window, text="資料表列表 (Tables)")
        paned_window.add(left_frame, width=250)
        self.table_list = tk.Listbox(left_frame)
        self.table_list.pack(fill=tk.BOTH, expand=True)
        self.table_list.bind("<<ListboxSelect>>", self.on_select_table)

        right_frame = tk.LabelFrame(paned_window, text="資料預覽 (前 5 筆)")
        paned_window.add(right_frame)
        self.data_text = tk.Text(right_frame, wrap=tk.NONE)
        self.data_text.pack(fill=tk.BOTH, expand=True)
        
        self.update_combo()

    def load_connections(self):
        if os.path.exists(CONNECTIONS_FILE):
            try:
                with open(CONNECTIONS_FILE, "r") as f: return json.load(f)
            except: return {}
        return {}

    def save_connections(self):
        with open(CONNECTIONS_FILE, "w") as f: json.dump(self.connections, f, indent=4)

    def update_combo(self):
        names = list(self.connections.keys())
        self.conn_combo['values'] = names
        if names:
            self.conn_combo.current(0)
            self.on_select_connection(None)
        else:
            self.conn_combo.set('')
            self.type_label.config(text="")

    def on_select_connection(self, event):
        name = self.conn_combo.get()
        if name in self.connections:
            data = self.connections[name]
            self.type_label.config(text=f"[{data.get('type', 'Unknown')}] {data.get('connection_string', '')}")

    def add_connection(self):
        dialog = DBConnectionDialog(self.root)
        self.root.wait_window(dialog)
        if dialog.result:
            self.connections[dialog.result["name"]] = dialog.result
            self.save_connections()
            self.update_combo()
            self.conn_combo.set(dialog.result["name"])
            self.on_select_connection(None)
            
    def edit_connection(self):
        name = self.conn_combo.get()
        if not name or name not in self.connections: return
        dialog = DBConnectionDialog(self.root, initial_data=self.connections[name])
        self.root.wait_window(dialog)
        if dialog.result:
            if dialog.result["name"] != name: del self.connections[name]
            self.connections[dialog.result["name"]] = dialog.result
            self.save_connections()
            self.update_combo()
            self.conn_combo.set(dialog.result["name"])

    def delete_connection(self):
        name = self.conn_combo.get()
        if not name: return
        if messagebox.askyesno("確認", f"確定要刪除 '{name}' 嗎?"):
            if name in self.connections:
                del self.connections[name]
                self.save_connections()
                self.update_combo()

    def connect_and_inspect(self):
        name = self.conn_combo.get()
        if not name or name not in self.connections: return
        
        # Simple SQLite Inspector for now
        data = self.connections[name]
        if data['type'] == 'SQLite':
            try:
                path = data['params'].get('path')
                if not path: return
                if path.startswith("sqlite:///"): path = path[10:]
                
                import sqlite3
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                self.table_list.delete(0, tk.END)
                for t in tables: self.table_list.insert(tk.END, t[0])
                
                self.active_conn = conn
                messagebox.showinfo("成功", f"已連線至 {name}")
            except Exception as e:
                messagebox.showerror("錯誤", str(e))

    def on_select_table(self, event):
        if not self.table_list.curselection(): return
        table = self.table_list.get(self.table_list.curselection())
        try:
            if hasattr(self, 'active_conn'):
                cursor = self.active_conn.cursor()
                
                # 1. Fetch Schema Info
                cursor.execute(f'PRAGMA table_info("{table}")')
                columns_info = cursor.fetchall()
                
                # Format Schema Output
                display = "=== Table Schema ===\n"
                for col in columns_info:
                    # cid, name, type, notnull, dflt_value, pk
                    name = col[1]
                    dtype = col[2]
                    notnull = col[3]
                    dflt = col[4]
                    is_pk = col[5]
                    
                    line_parts = []
                    if is_pk: line_parts.append("[PK]")
                    line_parts.append(f"{name} ({dtype})")
                    
                    reqs = []
                    if notnull: reqs.append("Not Null")
                    else: reqs.append("Nullable")
                    
                    if dflt is not None:
                        reqs.append(f"Default: {dflt}")
                        
                    line_parts.append("- " + ", ".join(reqs))
                    
                    display += " ".join(line_parts) + "\n"
                
                display += "\n=== Data Preview (Top 5) ===\n"
                
                # 2. Fetch Data Preview
                cursor.execute(f'SELECT * FROM "{table}" LIMIT 5')
                rows = cursor.fetchall()
                # cols = [description[0] for description in cursor.description] # Already have schema
                
                if not rows:
                    display += "(No data)"
                else:
                    for row in rows:
                        display += str(row) + "\n"
                
                self.data_text.delete(1.0, tk.END)
                self.data_text.insert(tk.END, display)
        except Exception as e:
            self.data_text.delete(1.0, tk.END)
            self.data_text.insert(tk.END, f"Error: {e}\n\nTraceback:\n")
            import traceback
            self.data_text.insert(tk.END, traceback.format_exc())

    def import_sql(self):
        file_paths = filedialog.askopenfilenames(title="選擇要匯入的 SQL 檔案", filetypes=[("SQL", "*.sql"), ("All", "*.*")])
        if not file_paths: return
        
        first_file = file_paths[0]
        default_name = os.path.splitext(os.path.basename(first_file))[0]
        for suffix in ['_schema', '-schema', '_data', '-data']:
            if default_name.lower().endswith(suffix): default_name = default_name[:-len(suffix)]
                
        conn_name = simpledialog.askstring("匯入 SQL", "請為新連線命名:", initialvalue=default_name)
        if not conn_name: return
        
        # Tools path hack
        import_dir = os.path.join("data", "imported_dbs")
        os.makedirs(import_dir, exist_ok=True)
        db_path = os.path.join(import_dir, f"{conn_name}.db")
        
        mode = "overwrite"
        if os.path.exists(db_path):
            if messagebox.askyesno("存在", "覆蓋 (Yes) 或 附加 (No)?"):
                try: os.remove(db_path)
                except: pass
            else: mode = "append" # Logic simplified for brevity
            
        # Sorting Logic
        sorted_files = sorted(file_paths)
        
        def log_callback(msg):
            print(msg)
            if "Error" in msg or "錯誤" in msg:
                self.root.after(0, lambda: messagebox.showerror("匯入錯誤", msg))
            elif "成功" in msg:
                self.root.after(0, lambda: messagebox.showinfo("匯入完成", msg))

        self.importer.run_import_thread(sorted_files, conn_name, db_path, mode, log_callback)
