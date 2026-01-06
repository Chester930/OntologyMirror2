# OntologyMirror 操作指令說明 (Cheat Sheet)

本專案分為「後端 (Python API)」與「前端 (React 網頁)」，兩者需要同時啟動才能運作。

## 1. 啟動後端 (Backend)

負責處理 AI 邏輯與 API 請求。

**開啟第一個終端機 (Terminal 1)，執行：**

```bash
# 確保在專案根目錄 (D:\Project\OntologyMirror)
python -m ontologymirror.server
```

* 成功訊號：看到 `Uvicorn running on http://0.0.0.0:8000`。
* 停止方式：按 `Ctrl + C`。

## 2. 啟動前端 (Frontend)

負責顯示網頁操作介面。

**開啟第二個終端機 (Terminal 2)，執行：**

```bash
#進入 web 資料夾
cd web

# 啟動開發伺服器
npm run dev
```

* 成功訊號：看到 `Local: http://localhost:5173/`。
* 停止方式：按 `q` 或 `Ctrl + C`。

## 3. 開始使用

打開瀏覽器，網址輸入：
👉 **[http://localhost:5173](http://localhost:5173)**

---

## 常見問題

* **如何修改 AI 設定？**
  * 編輯根目錄下的 `.env` 檔案 (例如更換 API Key)。
  * 修改後**必須**重啟後端 (Terminal 1) 才會生效。
* **Port 被佔用 (WinError 10048)？**
  * 這代表之前的後端沒關乾淨。
  * 解法：關閉所有 Terminal 視窗，重新開啟 VS Code，再依照上述步驟啟動。
