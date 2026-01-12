# OntologyMirror2 專案啟動說明

本專案是一個由 AI 驅動的資料庫語意映射工具，旨在將遺留資料庫 (Legacy DB) 的 Schema 自動映射至 Schema.org 標準。專案包含 Python FastAPI 後端與 React 前端。

## 系統需求 (Prerequisites)

- **Python**: 3.10 或更高版本
- **Node.js**: 18.0.0 或更高版本 (建議使用 LTS)
- **Git**: 用於版本控制

## 快速啟動 (Quick Start)

請依序啟動 **後端 (Backend)** 與 **前端 (Frontend)**。

### 步驟 1: 啟動後端伺服器 (Server)

後端負責 SQL 解析、向量搜尋與 LLM 映射邏輯。

1. **開啟終端機 (Terminal)**，進入專案根目錄。
2. **啟動 Python 虛擬環境 (如果未啟動)**:

   ```powershell
   # Windows PowerShell
   .\venv\Scripts\activate
   ```

3. **安裝相依套件**:

   ```bash
   pip install -r requirements.txt
   ```

4. **啟動 FastAPI 伺服器**:

   ```bash
   # 這裡會同時啟動自動重載 (Reload) 模式以便開發
   python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
   ```

   > 成功啟動後，您應該會看到 `Uvicorn running on http://0.0.0.0:8000` 的訊息。
   > API 文件可於 `http://localhost:8000/docs` 查看。

### 步驟 2: 啟動前端介面 (Web Client)

前端提供圖形化操作介面。

1. **開啟一個新的終端機視窗**。
2. **進入 `web` 目錄**:

   ```bash
   cd web
   ```

3. **安裝 Node.js 套件**:

   ```bash
   npm install
   ```

4. **啟動開發伺服器**:

   ```bash
   npm run dev
   ```

5. **開啟瀏覽器**:
   點擊終端機顯示的連結 (通常是 `http://localhost:5173`) 即可開始使用。

## 使用指引 (Usage)

1. **上傳 (Upload)**: 在首頁點擊 "選擇檔案"，選取您的 `.sql` 轉儲檔 (例如 `data/instnwnd.sql`)。
2. **檢視 (Review)**: 系統會解析並顯示資料表結構。
3. **映射 (Map)**: 點擊 "開始映射 (Start Mapping)"，後端 AI 會嘗試為每個資料表與欄位找到最合適的 Schema.org 定義。
4. **生成 (Generate)** (開發中): 確認映射結果後，可匯出遷移腳本或報告。

## 常見問題

- **Q: 映射結果不準確?**
  - A: 請確認 `data/vector_store` 是否已正確建立。若需重建，請執行 `python rebuild_kb.py`。
- **Q: 前端無法連線?**
  - A: 請確認後端是否運行在 Port 8000，且無防火牆阻擋。
