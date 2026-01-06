OntologyMirror 專案結構建議這是一個基於 Python 的模組化結構，將提取（Extract）、分析（Analyze）與生成（Generate）分離，方便未來的擴充。OntologyMirror/
├── .env                    # 環境變數 (API Keys)
├── .gitignore
├── README.md               # 專案說明
├── requirements.txt        # Python 依賴列表
├── main.py                 # 程式進入點 (CLI Entry Point)
│
├── config/                 # 設定檔
│   └── settings.py         # 全域設定 (LLM model 選擇, Schema.org 版本等)
│
├── ontologymirror/         # 主要原始碼目錄
│   ├── __init__.py
│   │
│   ├── core/               # 核心邏輯
│   │   ├── llm_client.py   # 封裝 LLM 呼叫 (OpenAI/Gemini)
│   │   └── schema_org.py   # 處理 Schema.org 定義的載入與查詢
│   │
│   ├── extractors/         # [第一步] 提取器：負責從 Repo 抓取並解析檔案
│   │   ├── __init__.py
│   │   ├── base.py         # 定義 Extractor 的基礎類別 (Interface)
│   │   ├── git_loader.py   # 處理 Git Clone 邏輯
│   │   ├── sql_parser.py   # 解析 .sql 檔案
│   │   ├── django_parser.py# 解析 models.py
│   │   └── prisma_parser.py# 解析 schema.prisma
│   │
│   ├── mappers/            # [第二步] 映射器：負責將 Raw Schema 轉為 Semantic Schema
│   │   ├── __init__.py
│   │   └── semantic_mapper.py # 透過 LLM 進行欄位比對的主要邏輯
│   │
│   └── generators/         # [第三步] 生成器：輸出最終檔案
│       ├── __init__.py
│       ├── sql_generator.py   # 產出標準 SQL DDL
│       └── json_generator.py  # 產出 JSON-LD 或 Mapping Report
│
├── data/                   # 存放暫存資料
│   ├── raw_repos/          # Clone 下來的暫存 Repos
│   └── knowledge_base/     # Schema.org 的參考資料 (JSON/CSV)
│
└── tests/                  # 單元測試
    ├── test_extractors.py
    ├── test_mappers.py
    └── test_generators.py
建議安裝的 Python 套件 (requirements.txt)# Git 操作
gitpython

# LLM 整合框架
langchain
langchain-openai
langchain-google-genai

# 資料驗證與結構化
pydantic

# 環境變數管理
python-dotenv

# CLI 介面工具
typer
rich  # 讓 Terminal 輸出變漂亮
