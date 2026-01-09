import sys
import os
# Add project root to sys.path so 'from tools...' imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tools.db_manager_lib.ui.app import DBManagerApp

if __name__ == "__main__":
    root = tk.Tk()
    app = DBManagerApp(root)
    root.mainloop()
