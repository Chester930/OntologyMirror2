import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import os
import sys

# Add current directory to path so we can import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from sqlalchemy.exc import SQLAlchemyError
from connectors.sqlite import SQLiteConnector
from connectors.postgresql import PostgresConnector
from connectors.mysql import MySQLConnector
from connectors.mssql import MSSQLConnector

CONNECTIONS_FILE = "db_connections.json"

class DBConnectionDialog(tk.Toplevel):
    """
    Modal dialog for configuring database connections dynamically.
    """
    def __init__(self, parent, initial_data=None):
        super().__init__(parent)
        self.title("設定資料庫連線")
        self.geometry("450x450")
        self.result = None
        self.initial_data = initial_data or {}
        
        # Center the window
        self.transient(parent)
        self.grab_set()

        self._init_ui()
        self._load_initial_data()

    def _init_ui(self):
        pad_opts = {'padx': 5, 'pady': 5}
        
        # Connection Name
        tk.Label(self, text="連線名稱:").pack(anchor="w", **pad_opts)
        self.name_var = tk.StringVar()
        tk.Entry(self, textvariable=self.name_var).pack(fill=tk.X, **pad_opts)

        # Database Type
        tk.Label(self, text="資料庫類型:").pack(anchor="w", **pad_opts)
        self.type_var = tk.StringVar(value="SQLite")
        types = ["SQLite", "PostgreSQL", "MySQL", "MSSQL"]
        self.type_combo = ttk.Combobox(self, textvariable=self.type_var, values=types, state="readonly")
        self.type_combo.pack(fill=tk.X, **pad_opts)
        self.type_combo.bind("<<ComboboxSelected>>", self._on_type_change)

        # Dynamic Fields Frame
        self.fields_frame = tk.LabelFrame(self, text="連線參數", padx=10, pady=10)
        self.fields_frame.pack(fill=tk.BOTH, expand=True, **pad_opts)
        
        self.entries = {} # Store entry widgets
        
        # Generated String Preview
        tk.Label(self, text="連線字串預覽 (Connection String):").pack(anchor="w", **pad_opts)
        self.preview_var = tk.StringVar()
        self.preview_entry = tk.Entry(self, textvariable=self.preview_var, state="readonly", fg="gray")
        self.preview_entry.pack(fill=tk.X, **pad_opts)

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=10)
        tk.Button(btn_frame, text="儲存", command=self._on_save, bg="#e1f5fe", width=10).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="取消", command=self.destroy, width=10).pack(side=tk.RIGHT, padx=5)

    def _on_type_change(self, event=None):
        # Clear existing fields
        for widget in self.fields_frame.winfo_children():
            widget.destroy()
        self.entries = {}
        
        db_type = self.type_var.get()
        
        if db_type == "SQLite":
            self._add_field("檔案路徑 (File Path)", "path", browse=True)
            
        elif db_type in ["PostgreSQL", "MySQL", "MSSQL"]:
            default_port = "5432" if db_type == "PostgreSQL" else ("3306" if db_type == "MySQL" else "1433")
            user_default = "postgres" if db_type == "PostgreSQL" else "root"
            
            self._add_field("主機 (Host)", "host", "localhost")
            self._add_field("連接埠 (Port)", "port", default_port)
            self._add_field("資料庫名稱 (Database)", "database", "mydb")
            self._add_field("使用者 (Username)", "username", user_default)
            self._add_field("密碼 (Password)", "password", "", show="*")
            
            if db_type == "MSSQL":
                 self._add_field("驅動程式 (Driver, 選填)", "driver", "ODBC Driver 17 for SQL Server")

        self._update_preview()

    def _add_field(self, label_text, key, default="", show=None, browse=False):
        row = len(self.entries)
        lbl = tk.Label(self.fields_frame, text=label_text + ":")
        lbl.grid(row=row, column=0, sticky="w", padx=5, pady=2)
        
        val_var = tk.StringVar(value=default)
        val_var.trace("w", lambda *args: self._update_preview())
        
        ent = tk.Entry(self.fields_frame, textvariable=val_var, show=show, width=30)
        ent.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
        
        if browse:
            btn = tk.Button(self.fields_frame, text="瀏覽...", width=8, command=lambda: self._browse_file(val_var))
            btn.grid(row=row, column=2, padx=2)
            
        self.entries[key] = val_var

    def _browse_file(self, var):
        filename = filedialog.askopenfilename(filetypes=[("SQLite DB", "*.db"), ("All Files", "*.*")])
        if filename:
            var.set(filename)

    def _update_preview(self):
        db_type = self.type_var.get()
        data = {k: v.get() for k, v in self.entries.items()}
        
        conn_str = ""
        if db_type == "SQLite":
            conn_str = f"sqlite:///{data.get('path', '')}"
        
        elif db_type == "PostgreSQL":
            # postgresql://user:password@host:port/dbname
            conn_str = f"postgresql://{data.get('username')}:{data.get('password')}@{data.get('host')}:{data.get('port')}/{data.get('database')}"
            
        elif db_type == "MySQL":
            # mysql+pymysql://user:password@host:port/dbname
            conn_str = f"mysql+pymysql://{data.get('username')}:{data.get('password')}@{data.get('host')}:{data.get('port')}/{data.get('database')}"
            
        elif db_type == "MSSQL":
            # mssql+pyodbc://user:password@host:port/dbname?driver=...
            driver = data.get('driver', 'ODBC Driver 17 for SQL Server').replace(' ', '+')
            conn_str = f"mssql+pyodbc://{data.get('username')}:{data.get('password')}@{data.get('host')}:{data.get('port')}/{data.get('database')}?driver={driver}"
            
        self.preview_var.set(conn_str)

    def _load_initial_data(self):
        if not self.initial_data:
            self._on_type_change() # Load defaults
            return
            
        self.name_var.set(self.initial_data.get("name", ""))
        self.type_var.set(self.initial_data.get("type", "SQLite"))
        self._on_type_change() # Render fields
        
        # Populate fields
        params = self.initial_data.get("params", {})
        for key, value in params.items():
            if key in self.entries:
                self.entries[key].set(value)
        
        # Trigger preview update
        self._update_preview()

    def _on_save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("錯誤", "必須輸入連線名稱")
            return
            
        self.result = {
            "name": name,
            "type": self.type_var.get(),
            "connection_string": self.preview_var.get(),
            "params": {k: v.get() for k, v in self.entries.items()}
        }
        self.destroy()

class DBManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OntologyMirror 資料庫管理工具")
        self.root.geometry("900x600")

        self.connections = self.load_connections()
        self.connector = None
        
        # --- UI Layout ---
        
        # Top Frame: Connection List
        top_frame = tk.Frame(root, padx=10, pady=10)
        top_frame.pack(fill=tk.X)
        
        tk.Label(top_frame, text="已儲存的連線:").pack(side=tk.LEFT)
        self.conn_combo = ttk.Combobox(top_frame, state="readonly", width=30)
        self.conn_combo.pack(side=tk.LEFT, padx=5)
        self.conn_combo.bind("<<ComboboxSelected>>", self.on_select_connection)
        
        tk.Button(top_frame, text="新增連線", command=self.add_connection, bg="#f0f0f0").pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text="匯入 SQL (.sql)", command=self.import_sql, bg="#fff9c4").pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text="編輯", command=self.edit_connection).pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text="刪除", command=self.delete_connection).pack(side=tk.LEFT, padx=2)
        
        # Helper Label
        self.type_label = tk.Label(top_frame, text="", fg="gray")
        self.type_label.pack(side=tk.LEFT, padx=10)

        # Middle Frame: Actions
        action_frame = tk.Frame(root, padx=10, pady=5)
        action_frame.pack(fill=tk.X)
        
        tk.Button(action_frame, text="連線並查看資料庫 (Connect & Inspect)", command=self.connect_and_inspect, 
                  bg="#4caf50", fg="white", font=("Microsoft JhengHei", 10, "bold"), height=2).pack(fill=tk.X)

        # Bottom Frame: Inspection Results
        bottom_frame = tk.Frame(root, padx=10, pady=10)
        bottom_frame.pack(fill=tk.BOTH, expand=True)

        # Split View
        paned_window = tk.PanedWindow(bottom_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # Left: Table List
        left_frame = tk.LabelFrame(paned_window, text="資料表列表 (Tables)")
        paned_window.add(left_frame, width=250)
        
        self.table_list = tk.Listbox(left_frame)
        self.table_list.pack(fill=tk.BOTH, expand=True)
        self.table_list.bind("<<ListboxSelect>>", self.on_select_table)

        # Right: Data / Columns
        right_frame = tk.LabelFrame(paned_window, text="資料預覽 (前 5 筆)")
        paned_window.add(right_frame)
        
        self.data_text = tk.Text(right_frame, wrap=tk.NONE)
        self.data_text.pack(fill=tk.BOTH, expand=True)
        
        # Initial populate
        self.update_combo()

    def load_connections(self):
        if os.path.exists(CONNECTIONS_FILE):
            try:
                with open(CONNECTIONS_FILE, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_connections(self):
        with open(CONNECTIONS_FILE, "w") as f:
            json.dump(self.connections, f, indent=4)

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
            # Handle format
            db_type = data.get("type", "Unknown")
            conn_str = data.get("connection_string", "")
            self.type_label.config(text=f"[{db_type}] {conn_str}")

    def add_connection(self):
        dialog = DBConnectionDialog(self.root)
        self.root.wait_window(dialog)
        
        if dialog.result:
            name = dialog.result["name"]
            self.connections[name] = dialog.result
            self.save_connections()
            self.update_combo()
            self.conn_combo.set(name)
            self.on_select_connection(None)

    def import_sql(self):
        # 1. Select SQL File
        sql_file = filedialog.askopenfilename(
            title="選擇要匯入的 SQL 檔案",
            filetypes=[("SQL 檔案", "*.sql"), ("所有檔案", "*.*")]
        )
        if not sql_file: return

        # 2. Ask for Connection Name
        default_name = os.path.splitext(os.path.basename(sql_file))[0]
        conn_name = simpledialog.askstring("匯入 SQL", "請輸入此連線的名稱:", initialvalue=default_name)
        if not conn_name: return
        
        if conn_name in self.connections:
            if not messagebox.askyesno("覆蓋確認", f"連線 '{conn_name}' 已存在。是否覆蓋?"):
                return

        # 3. Create Import Directory
        import_dir = os.path.join(current_dir, "..", "data", "imported_dbs")
        os.makedirs(import_dir, exist_ok=True)
        
        # 4. Convert SQL to SQLite
        db_path = os.path.join(import_dir, f"{conn_name}.db")
        
        try:
            # Read SQL
            try:
                with open(sql_file, 'r', encoding='utf-8') as f: sql_script = f.read()
            except UnicodeDecodeError:
                with open(sql_file, 'r', encoding='latin-1') as f: sql_script = f.read()

            # Execute into new DB
            if os.path.exists(db_path): os.remove(db_path) # Clean start
            
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.executescript(sql_script)
            conn.commit()
            conn.close()

            # 5. Add to Connections
            new_conn = {
                "name": conn_name,
                "type": "SQLite",
                "connection_string": f"sqlite:///{db_path.replace(os.sep, '/')}",
                "params": {"path": db_path}
            }
            
            self.connections[conn_name] = new_conn
            self.save_connections()
            
            # 6. Update UI
            self.update_combo()
            self.conn_combo.set(conn_name)
            self.on_select_connection(None)
            
            messagebox.showinfo("成功", f"已匯入 '{os.path.basename(sql_file)}'\n至 '{db_path}'\n並新增為連線 '{conn_name}'。")
            
            # Auto Connect to verify
            self.connect_and_inspect()

        except Exception as e:
            messagebox.showerror("匯入失敗", f"將 SQL 轉換為 SQLite 時發生錯誤:\n{e}")

    def edit_connection(self):
        name = self.conn_combo.get()
        if not name or name not in self.connections: return
        
        data = self.connections[name]
        # Prepare data for dialog
        initial_data = data.copy()
        initial_data["name"] = name
        
        dialog = DBConnectionDialog(self.root, initial_data=initial_data)
        self.root.wait_window(dialog)
        
        if dialog.result:
            new_name = dialog.result["name"]
            # If name changed, delete old
            if new_name != name:
                del self.connections[name]
            
            self.connections[new_name] = dialog.result
            self.save_connections()
            self.update_combo()
            self.conn_combo.set(new_name)
            self.on_select_connection(None)

    def delete_connection(self):
        name = self.conn_combo.get()
        if name and messagebox.askyesno("確認", f"確定要刪除 {name} 嗎?"):
            del self.connections[name]
            self.save_connections()
            self.update_combo()

    def get_connector(self, db_type, conn_str):
        if db_type == "SQLite": return SQLiteConnector(conn_str)
        if db_type == "PostgreSQL": return PostgresConnector(conn_str)
        if db_type == "MySQL": return MySQLConnector(conn_str)
        if db_type == "MSSQL": return MSSQLConnector(conn_str)
        return SQLiteConnector(conn_str)

    def connect_and_inspect(self):
        name = self.conn_combo.get()
        if not name or name not in self.connections: 
            messagebox.showwarning("提示", "請先選擇一個連線")
            return

        data = self.connections[name]
        conn_str = data.get("connection_string")
        db_type = data.get("type", "SQLite")

        self.table_list.delete(0, tk.END)
        self.data_text.delete(1.0, tk.END)

        try:
            self.connector = self.get_connector(db_type, conn_str)
            self.connector.connect()
            
            tables = self.connector.get_tables()
            
            for table in tables:
                self.table_list.insert(tk.END, table)
            
            messagebox.showinfo("成功", f"成功連線至 {db_type}!\n找到 {len(tables)} 個資料表。")
            
        except SQLAlchemyError as e:
            messagebox.showerror("連線錯誤", str(e))
        except Exception as e:
            messagebox.showerror("錯誤", str(e))

    def on_select_table(self, event):
        if not self.table_list.curselection(): return
        if not self.connector: return

        table_name = self.table_list.get(self.table_list.curselection())
        self.data_text.delete(1.0, tk.END)
        
        try:
            # Show Columns
            columns = self.connector.get_columns(table_name)
            col_info = " | ".join([f"{col['name']} ({col['type']})" for col in columns])
            self.data_text.insert(tk.END, f"欄位定義 (Schema): {col_info}\n\n")
            self.data_text.insert(tk.END, "-"*50 + "\n數據預覽 (Data Preview):\n")

            # Show Data
            rows = self.connector.get_sample_data(table_name)
            if rows:
                for row in rows:
                    self.data_text.insert(tk.END, str(row) + "\n")
            else:
                self.data_text.insert(tk.END, "(無數據 / No data found)")

        except Exception as e:
            self.data_text.insert(tk.END, f"讀取數據發生錯誤: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DBManagerApp(root)
    root.mainloop()
