import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import sys
import os

# Add project root to sys.path to ensure imports work
# Assuming this file is in tools/db_manager_lib/ui/
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
if project_root not in sys.path:
    sys.path.append(project_root)

from ontologymirror.mappers.schema_mapper import SchemaMapper

class MappingWindow(tk.Toplevel):
    def __init__(self, parent, connection_name, table_name, schema_info):
        """
        schema_info: List of dicts or tuples containing column info. 
                     Expected format from app.py: (cid, name, type, notnull, dflt_value, pk)
        """
        super().__init__(parent)
        self.title(f"Schema.org 映射工具 - {table_name} ({connection_name})")
        self.geometry("1000x700")
        
        self.connection_name = connection_name
        self.table_name = table_name
        self.schema_info = schema_info
        
        # Initialize Mapper
        self.mapper = SchemaMapper()
        
        # Data storage
        # Key: column_name, Value: Dict with mapping status
        self.mappings = {} 
        self._init_data()
        
        self._init_ui()
        
        # Auto-run mapping on start?
        # Let's do it automatically to match the workflow: Selection -> Automated Mapping -> Review
        self.run_auto_mapping()

    def _init_data(self):
        for col in self.schema_info:
            # col structure depends on pragma table_info
            col_name = col[1] 
            col_type = col[2]
            self.mappings[col_name] = {
                "original_column": col_name,
                "original_type": col_type,
                "schema_property": "Analyzing...",
                "confidence_score": 0.0,
                "verification_status": "AI_GENERATED", # AI_GENERATED, VERIFIED, CORRECTED, FLAGGED
                "rationale": "Pending analysis...",
                "suggestions": [] # Store top k suggestions here
            }

    def _init_ui(self):
        # Top Toolbar
        toolbar = tk.Frame(self, padx=10, pady=5, bg="#f0f0f0")
        toolbar.pack(fill=tk.X)
        
        tk.Label(toolbar, text=f"正在映射: {self.table_name}", font=("Microsoft JhengHei", 12, "bold"), bg="#f0f0f0").pack(side=tk.LEFT)
        
        tk.Button(toolbar, text="重新自動映射 (Re-Run AI)", command=self.run_auto_mapping).pack(side=tk.RIGHT, padx=5)
        tk.Button(toolbar, text="匯出目前的映射 (Export)", command=self.export_mapping).pack(side=tk.RIGHT, padx=5)

        # Main Content - Split into Left (List) and Right (Details/Edit)?
        # Or a Grid/Treeview Dashboard like the web prototype?
        # The web prototype used a card grid. Treeview is easier in Tkinter for lists.
        # Let's use a Treeview for the "Dashboard" feel.
        
        self.tree = ttk.Treeview(self, columns=("col", "type", "mapped_prop", "score", "status"), show="headings")
        self.tree.heading("col", text="原始欄位 (Column)")
        self.tree.heading("type", text="類型 (Type)")
        self.tree.heading("mapped_prop", text="Schema.org 屬性 (Property)")
        self.tree.heading("score", text="信心度 (Conf.)")
        self.tree.heading("status", text="狀態 (Status)")
        
        self.tree.column("col", width=150)
        self.tree.column("type", width=100)
        self.tree.column("mapped_prop", width=200)
        self.tree.column("score", width=80)
        self.tree.column("status", width=100)
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Legend / Actions
        bottom_frame = tk.Frame(self, padx=10, pady=5)
        bottom_frame.pack(fill=tk.X)
        tk.Label(bottom_frame, text="雙擊項目以編輯或確認 (Double-click to Edit/Verify)", fg="gray").pack(side=tk.LEFT)
        
        tk.Button(bottom_frame, text="關閉", command=self.destroy).pack(side=tk.RIGHT)

    def run_auto_mapping(self):
        # Run in thread
        threading.Thread(target=self._mapping_thread, daemon=True).start()
        
    def _mapping_thread(self):
        for col_name, data in self.mappings.items():
            suggestions = self.mapper.get_suggestion(col_name)
            
            if suggestions:
                top = suggestions[0]
                data["schema_property"] = f"{top['label']} ({top['id']})"
                data["confidence_score"] = top['score']
                data["rationale"] = f"AI matched '{col_name}' to '{top['label']}' with score {top['score']}"
                data["suggestions"] = suggestions
            else:
                data["schema_property"] = "No Match"
                data["confidence_score"] = 0.0
                data["rationale"] = "No suitable match found."
                data["suggestions"] = []
                
        self.after(0, self.refresh_tree)

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for col_name, data in self.mappings.items():
            score = data["confidence_score"]
            status = data["verification_status"]
            
            # Identify tags for coloring
            tags = ()
            if status == "VERIFIED": tags = ("verified",)
            elif status == "CORRECTED": tags = ("corrected",)
            elif status == "FLAGGED": tags = ("flagged",)
            elif score > 0.8: tags = ("high_conf",)
            elif score < 0.5: tags = ("low_conf",)
            
            self.tree.insert("", tk.END, iid=col_name, values=(
                col_name,
                data["original_type"],
                data["schema_property"],
                f"{int(score*100)}%",
                status
            ), tags=tags)
            
        # Configure tag colors
        self.tree.tag_configure("verified", background="#dcfce7") # green-ish
        self.tree.tag_configure("corrected", background="#dbeafe") # blue-ish
        self.tree.tag_configure("flagged", background="#fef9c3") # yellow-ish
        self.tree.tag_configure("low_conf", foreground="red")

    def on_double_click(self, event):
        item_id = self.tree.selection()
        if not item_id: return
        col_name = item_id[0]
        self.open_edit_modal(col_name)

    def open_edit_modal(self, col_name):
        data = self.mappings[col_name]
        
        modal = tk.Toplevel(self)
        modal.title(f"編輯映射: {col_name}")
        modal.geometry("600x500")
        
        # Header Info
        info_frame = tk.LabelFrame(modal, text="欄位資訊", padx=10, pady=5)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(info_frame, text=f"原始欄位: {col_name}").pack(anchor="w")
        tk.Label(info_frame, text=f"原始類型: {data['original_type']}").pack(anchor="w")
        tk.Label(info_frame, text=f"目前映射: {data['schema_property']}").pack(anchor="w")
        
        # AI Suggestions
        sugg_frame = tk.LabelFrame(modal, text="AI 建議", padx=10, pady=5)
        sugg_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(sugg_frame)
        scrollbar = ttk.Scrollbar(sugg_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def select_suggestion(s):
            data["schema_property"] = f"{s['label']} ({s['id']})"
            data["confidence_score"] = s['score']
            data["verification_status"] = "CORRECTED"
            data["rationale"] = f"Manual selection: {s['label']}"
            self.refresh_tree()
            modal.destroy()

        if data['suggestions']:
            for s in data['suggestions']:
                f = tk.Frame(scrollable_frame, borderwidth=1, relief="solid", padx=5, pady=5)
                f.pack(fill=tk.X, pady=2)
                
                header = tk.Frame(f)
                header.pack(fill=tk.X)
                tk.Label(header, text=f"{s['label']} ({s['id']})", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
                tk.Label(header, text=f"{int(s['score']*100)}%", fg="green").pack(side=tk.RIGHT)
                
                desc = s.get('description', 'No description').split('\n')[1] if '\n' in s.get('description', '') else s.get('description', '')
                tk.Label(f, text=desc, wraplength=500, justify="left", fg="#555").pack(anchor="w")
                
                tk.Button(f, text="採用此項", command=lambda s=s: select_suggestion(s), bg="#e0f7fa").pack(anchor="e", pady=2)
        else:
            tk.Label(scrollable_frame, text="無 AI 建議").pack()

        # Search / Manual Override
        manual_frame = tk.Frame(modal, padx=10, pady=10)
        manual_frame.pack(fill=tk.X)
        
        tk.Label(manual_frame, text="手動搜尋/輸入:").pack(side=tk.LEFT)
        search_var = tk.StringVar()
        entry = tk.Entry(manual_frame, textvariable=search_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        def do_search():
            term = search_var.get()
            if not term: return
            # Re-use mapper logic but with user term
            try:
                # Clear frame
                for widget in scrollable_frame.winfo_children(): widget.destroy()
                
                results = self.mapper.get_suggestion(term, k=5)
                if not results:
                     tk.Label(scrollable_frame, text="無搜尋結果").pack()
                     return
                     
                for s in results:
                    f = tk.Frame(scrollable_frame, borderwidth=1, relief="solid", padx=5, pady=5)
                    f.pack(fill=tk.X, pady=2)
                    
                    header = tk.Frame(f)
                    header.pack(fill=tk.X)
                    tk.Label(header, text=f"{s['label']} ({s['id']})", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
                    
                    desc = s.get('description', '')
                    tk.Label(f, text=desc, wraplength=500, justify="left", fg="#555").pack(anchor="w")
                    
                    tk.Button(f, text="採用此項", command=lambda s=s: select_suggestion(s), bg="#e0f7fa").pack(anchor="e", pady=2)
            except Exception as e:
                messagebox.showerror("錯誤", str(e))

        tk.Button(manual_frame, text="搜尋", command=do_search).pack(side=tk.LEFT)
        
        # Bottom Actions
        action_frame = tk.Frame(modal, padx=10, pady=10)
        action_frame.pack(fill=tk.X)
        
        def mark_verified():
            data["verification_status"] = "VERIFIED"
            self.refresh_tree()
            modal.destroy()
            
        def mark_flagged():
            data["verification_status"] = "FLAGGED"
            self.refresh_tree()
            modal.destroy()

        tk.Button(action_frame, text="✅ 確認正確 (Verified)", command=mark_verified, bg="#dcfce7").pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="🚩 標記問題 (Flag)", command=mark_flagged, bg="#fef9c3").pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="取消", command=modal.destroy).pack(side=tk.RIGHT)

    def export_mapping(self):
        # TODO: Implement export to JSON/SQL?
        messagebox.showinfo("提示", "匯出功能尚未實作 (Planned Feature)")
