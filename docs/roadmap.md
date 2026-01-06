# OntologyMirror 未來優化建議 (Roadmap)

雖然 v0.1 已經能順利運作，但為了讓它成為企業級的工具，以下是幾個可以讓系統「更強大、更聰明」的改進方向：

## 1. 🧠 AI 核心與準確度 (Core AI)

目前的 RAG 是基於「Table vs Class」的粗略檢索。

* **人機協作學習 (Human-in-the-loop Learning)**:
  * **痛點**: AI 有時會判斷錯誤 (例如 `dept_emp` -> `Thing`)。
  * **解法**: 在 UI 允許使用者手動修正映射 (例如手選 `EmployeeRole`)。系統將這些修正存入 Vector DB，下次遇到類似結構時，AI 會優先參考使用者的歷史決定 (Few-shot Learning)。
* **屬性層級的 RAG (Property-level RAG)**:
  * **痛點**: 目前只檢索 Class，Column 的映射主要靠 LLM 通用知識。
  * **解法**: 建立 Schema.org **Properties** 的向量索引。當處理 `birth_date` 時，系統能具體檢索出 `birthDate`、`foundingDate` 等候選屬性給 LLM 參考。

## 2. 🔌 功能擴充 (Features)

目前僅支援上傳單一 `.sql` 檔案。

* **資料庫直連 (Direct DB Connection)**:
  * 支援輸入 Connection String (Postgres, MySQL)，直接從活體資料庫提取 Schema，省去手動匯出 SQL 的麻煩。
* **知識圖譜視覺化 (Knowledge Graph Visualization)**:
  * 利用 Mermaid 或 React Flow，將映射後的結果畫成關聯圖。
  * 顯示 Table 之間的 Foreign Key 如何轉換成 Schema.org 的 Object Property 關係。

## 3. 💻 使用者體驗 (User Experience)

目前 UI 是線性的 (上傳 -> 映射 -> 下載)。

* **互動式修正 (Interactive Mapping Editor)**:
  * 在 Step 3 不只是看結果，而是一個**編輯器**。
  * 點擊下拉選單更換 Class。
  * 點擊欄位更換 Property。
* **多檔案專案管理 (Project Management)**:
  * 允許保存「專案」，下次進來可以繼續編輯之前的映射結果，不用重跑。

## 4. ⚙️ 工程架構 (Engineering)

* **非同步列隊 (Async Queue)**:
  * 若 SQL 檔有 100 張表，現在的前端會卡住等待。
  * 引入 Celery 或 Redis Queue，讓映射在背景執行，前端顯示進度條。
* **Docker 化**:
  * 提供 `docker-compose.yml`，一鍵啟動所有服務 (無需手動開兩個終端機)。
