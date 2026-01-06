# OntologyMirror Web Interface Instructions

The Web Interface provides a modern GUI for the schema mapping process.

## Prerequisites

- Python 3.8+
- Node.js 16+

## 1. Start the Backend Server (Term 1)

This server runs the AI mapping engine and logic.

```bash
python -m ontologymirror.server
```

*Port*: `8000` (API Docs at `http://localhost:8000/docs`)

## 2. Start the Frontend Application (Term 2)

This runs the React dashboard.

```bash
cd web
npm run dev
```

*Port*: `5173` (Access at `http://localhost:5173`)

## 3. Usage Flow

1. Open `http://localhost:5173` in your browser.
2. **Step 1**: Drag & Drop your `.sql` file (e.g., `tests/fixtures/test_schema.sql`).
3. **Step 2**: Review the extracted tables (e.g., `auth_user`). Click "Start Semantic Mapping".
4. **Step 3**: Watch the AI map columns to Schema.org (e.g., `username` -> `alternateName`).
5. **Download**: Click "Generate SQL Artifacts" to get the result.
