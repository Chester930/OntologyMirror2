import tkinter as tk
from tkinter import ttk, messagebox, filedialog

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
            conn_str = f"postgresql://{data.get('username')}:{data.get('password')}@{data.get('host')}:{data.get('port')}/{data.get('database')}"
            
        elif db_type == "MySQL":
            conn_str = f"mysql+pymysql://{data.get('username')}:{data.get('password')}@{data.get('host')}:{data.get('port')}/{data.get('database')}"
            
        elif db_type == "MSSQL":
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
