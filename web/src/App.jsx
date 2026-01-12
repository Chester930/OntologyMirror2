import React, { useState } from 'react';
import './App.css';

import ConnectionManager from './components/ConnectionManager';

function App() {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState("");
  const [rawTables, setRawTables] = useState([]);
  const [mappedTables, setMappedTables] = useState([]);
  const [finalOutput, setFinalOutput] = useState(null);

  // API Base URL (Proxy logic or direct)
  const API_URL = "http://localhost:8000";

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setLoading(true);
    setFileName(file.name);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_URL}/api/upload`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      setRawTables(data.tables);
      setStep(2);
    } catch (err) {
      console.error(err);
      alert("上傳失敗 (Upload failed)!");
    }
    setLoading(false);
  };

  const handleDbConnect = (tables, isLoadingState) => {
    if (isLoadingState !== undefined) {
      setLoading(isLoadingState);
    }
    if (tables) {
      setRawTables(tables);
      setFileName("Database Connection"); // Virtual filename
      setStep(2);
    }
  };

  const handleMapping = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/map`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tables: rawTables })
      });
      const data = await res.json();
      setMappedTables(data);
      setStep(3);
    } catch (err) {
      console.error(err);
      alert("映射失敗 (Mapping failed)!");
    }
    setLoading(false);
  };

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(mappedTables)
      });
      const data = await res.json();
      setFinalOutput(data);
    } catch (err) {
      console.error(err);
      alert("生成失敗 (Generation failed)!");
    }
    setLoading(false);
  }

  const handleExportToFolder = async () => {
    // Check for browser support
    if (!window.showDirectoryPicker) {
      alert("您的瀏覽器不支援資料夾選擇功能 (File System Access API)。請使用 Chrome 或 Edge (桌機版)。");
      return;
    }
    try {
      // 1. Prepare default folder name
      const baseName = fileName.replace(/\.[^/.]+$/, ""); // remove extension
      const defaultFolderName = `${baseName}_mapped`;

      const folderName = prompt("請確認要建立的資料夾名稱：", defaultFolderName);
      if (!folderName) return; // User cancelled prompt

      // 2. Ask user to pick the PARENT folder
      const parentDirHandle = await window.showDirectoryPicker();

      // 3. Create the subfolder
      const subDirHandle = await parentDirHandle.getDirectoryHandle(folderName, { create: true });

      // 4. Save SQL file in subfolder
      const sqlHandle = await subDirHandle.getFileHandle("schema_mapped.sql", { create: true });
      const sqlWritable = await sqlHandle.createWritable();
      await sqlWritable.write(finalOutput.sql);
      await sqlWritable.close();

      // 5. Save JSON report in subfolder
      const jsonHandle = await subDirHandle.getFileHandle("mapping_report.json", { create: true });
      const jsonWritable = await jsonHandle.createWritable();
      await jsonWritable.write(JSON.stringify(finalOutput.json, null, 2));
      await jsonWritable.close();

      alert("匯出成功 (Export successful)!");
    } catch (err) {
      console.error(err);
      // Ignore cancellation errors
      if (err.name !== 'AbortError') {
        alert("匯出失敗：" + err.message);
      }
    }
  };

  // --- New Logic for Human-in-the-loop ---
  const [editTableIndex, setEditTableIndex] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  const openEditModal = (idx) => {
    setEditTableIndex(idx);
    setSearchQuery("");
    setSearchResults([]);
  };

  const closeEditModal = () => {
    setEditTableIndex(null);
  };

  const handleSearch = async (e) => {
    const q = e.target.value;
    setSearchQuery(q);
    if (q.length < 2) return;

    setIsSearching(true);
    try {
      const res = await fetch(`${API_URL}/api/search?query=${encodeURIComponent(q)}`);
      const data = await res.json();
      setSearchResults(data);
    } catch (err) {
      console.error(err);
    }
    setIsSearching(false);
  };

  const applyEdit = (newClass) => {
    const updated = [...mappedTables];
    updated[editTableIndex] = {
      ...updated[editTableIndex],
      schema_class: newClass.name,
      rationale: `Manual override by user. (Selected: ${newClass.name})`,
      verification_status: 'CORRECTED'
      // confidence_score kept as original (mock/old value) or should we set it to null?
      // User said "keep original standard", so we leave it untouched.
    };
    setMappedTables(updated);
    closeEditModal();
  };

  const updateStatus = (status) => {
    const updated = [...mappedTables];
    updated[editTableIndex] = {
      ...updated[editTableIndex],
      verification_status: status
    };
    setMappedTables(updated);
    closeEditModal();
  };

  const ConfidenceBadge = ({ score }) => {
    // Default to 0.5 if score is missing
    const s = score !== undefined ? score : 0.5;
    let color = "#ef4444"; // red
    let text = "低信心";
    if (s >= 0.8) {
      color = "#22c55e"; // green
      text = "高信心";
    } else if (s >= 0.6) {
      color = "#eab308"; // yellow
      text = "普通";
    }

    return (
      <span style={{
        backgroundColor: color,
        color: '#000',
        padding: '2px 6px',
        borderRadius: '4px',
        fontSize: '0.75rem',
        fontWeight: 'bold',
        marginLeft: '8px'
      }}>
        {text} ({Math.round(s * 100)}%)
      </span>
    );
  };

  return (
    <div className="container">
      <header className="header">
        <h1>OntologyMirror <span className="version">v0.1</span></h1>
        <p>AI 驅動的 schema.org 語意映射工具</p>
      </header>

      {/* Edit Modal */}
      {editTableIndex !== null && (
        <div className="modal-overlay">
          <div className="modal-content glass">
            <h3>搜尋 Schema.org 類別</h3>
            <p>正在修正：<strong>{mappedTables[editTableIndex].original_table}</strong></p>

            <input
              type="text"
              placeholder="輸入關鍵字 (例如: Person, Event...)"
              value={searchQuery}
              onChange={handleSearch}
              autoFocus
              className="search-input"
            />

            {/* AI Search Keywords Suggestions */}
            {mappedTables[editTableIndex]?.search_keywords?.length > 0 && (
              <div className="keyword-suggestions" style={{ marginTop: '0.5rem', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '0.8rem', color: '#94a3b8', alignSelf: 'center' }}>AI 建議關鍵字:</span>
                {mappedTables[editTableIndex].search_keywords.map((kw, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setSearchQuery(kw);
                      // Trigger search immediately
                      setIsSearching(true);
                      fetch(`${API_URL}/api/search?query=${encodeURIComponent(kw)}`)
                        .then(res => res.json())
                        .then(data => setSearchResults(data))
                        .catch(console.error)
                        .finally(() => setIsSearching(false));
                    }}
                    style={{
                      backgroundColor: '#3b82f6',
                      border: 'none',
                      borderRadius: '12px',
                      color: 'white',
                      padding: '2px 10px',
                      fontSize: '0.8rem',
                      cursor: 'pointer',
                      transition: 'background 0.2s'
                    }}
                    onMouseOver={(e) => e.target.style.backgroundColor = '#2563eb'}
                    onMouseOut={(e) => e.target.style.backgroundColor = '#3b82f6'}
                  >
                    {kw}
                  </button>
                ))}
              </div>
            )}

            <div className="search-results">
              {isSearching && <div className="spinner">搜尋中...</div>}
              {searchResults.map((r, i) => (
                <div key={i} className="search-item" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ flex: 1, cursor: 'pointer' }} onClick={() => applyEdit(r)}>
                    <div className="search-item-title">{r.name}</div>
                    <div className="search-item-desc">
                      {r.translated_description ? (
                        <span style={{ color: '#86efac' }}>{r.translated_description}</span>
                      ) : (
                        <span>{r.description?.substring(0, 120)}...</span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      // Call translate API
                      fetch(`${API_URL}/api/translate?text=${encodeURIComponent(r.description || "")}`)
                        .then(res => res.json())
                        .then(data => {
                          const newResults = [...searchResults];
                          newResults[i].translated_description = data.translated;
                          setSearchResults(newResults);
                        });
                    }}
                    style={{ background: 'transparent', border: '1px solid #555', borderRadius: '50%', width: '30px', height: '30px', cursor: 'pointer', marginLeft: '10px' }}
                    title="翻譯成中文"
                  >
                    🌐
                  </button>
                </div>
              ))}
            </div>

            <button className="btn-secondary" onClick={closeEditModal} style={{ marginTop: '1rem' }}>
              取消
            </button>

            <div style={{ marginTop: '2rem', borderTop: '1px solid #333', paddingTop: '1rem' }}>
              <h4>其他狀態標記</h4>
              <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                <button className="btn-secondary" onClick={() => updateStatus('VERIFIED')} style={{ backgroundColor: '#22c55e', color: 'black' }}>✅ 確認無誤</button>
                <button className="btn-secondary" onClick={() => updateStatus('FLAGGED')} style={{ backgroundColor: '#f59e0b', color: 'black' }}>🚩 標記問題</button>
                <button className="btn-secondary" onClick={() => updateStatus('AI_GENERATED')}>🔄 重置狀態</button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="card glass">
        {loading && <div className="loader">處理中... AI 正在思考 🧠</div>}

        {!loading && step === 1 && (
          <>
            <div className="card upload-zone">
              <h2>方法一：上傳 SQL 檔案 (Upload SQL File)</h2>
              <input type="file" accept=".sql" onChange={handleFileUpload} disabled={loading} />
              {loading && <p>Processing...</p>}
            </div>

            <p style={{ margin: '20px 0', opacity: 0.5 }}>- 或 OR -</p>

            <ConnectionManager
              apiUrl={API_URL}
              onConnect={handleDbConnect}
              isLoading={loading}
            />
          </>
        )}

        {!loading && step === 2 && (
          <div className="review-zone">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2>步驟 2: 檢閱已提取的資料表</h2>
            </div>
            <div className="table-list">
              {rawTables.map((t, idx) => (
                <div key={idx} className="table-item">
                  📦 {t.name} <span className="badge">{t.columns.length} 欄位</span>
                </div>
              ))}
            </div>
            <button className="btn-primary" onClick={handleMapping}>
              開始語意映射 (AI) ✨
            </button>
          </div>
        )}

        {!loading && step === 3 && (
          <div className="result-zone">
            <h2>步驟 3: 映射結果與微調</h2>

            {!finalOutput ? (
              <div>
                <div className="mapping-grid">
                  {mappedTables.map((m, idx) => (
                    <div key={idx} className="mapping-card">
                      <div className="card-header">
                        <div className="left">
                          {m.original_table}
                        </div>
                        <div className="right-group">
                          <div className="arrow">➡️</div>
                          <div className="right neon-text">{m.schema_class}</div>
                          {/* Status Badge */}
                          {m.verification_status && m.verification_status !== "AI_GENERATED" && (
                            <span className="status-badge" style={{
                              backgroundColor: m.verification_status === 'VERIFIED' ? '#22c55e' : (m.verification_status === 'CORRECTED' ? '#3b82f6' : '#f59e0b'),
                              color: '#000',
                              padding: '2px 6px',
                              borderRadius: '4px',
                              fontSize: '0.75rem',
                              fontWeight: 'bold',
                              marginLeft: '8px'
                            }}>
                              {m.verification_status === 'VERIFIED' ? '已確認' : (m.verification_status === 'CORRECTED' ? '已修正' : '待確認')}
                            </span>
                          )}
                          <ConfidenceBadge score={m.confidence_score} />
                        </div>
                      </div>

                      <p className="rationale">"{m.rationale}"</p>

                      <button
                        className="btn-edit"
                        onClick={() => openEditModal(idx)}
                      >
                        ✏️ 修正 / 確認狀態
                      </button>
                    </div>
                  ))}
                </div>
                <button className="btn-primary" onClick={handleGenerate} style={{ marginTop: '20px' }}>
                  確認無誤，生成報告 🚀
                </button>
              </div>
            ) : (
              <div className="final-artifact">
                <h3>✅ 生成完成！</h3>
                <p style={{ marginBottom: '1rem', color: '#94a3b8' }}>預覽 SQL 結果：</p>
                <textarea readOnly value={finalOutput.sql} className="code-block"></textarea>
                <div className="actions">
                  <button className="btn-primary" onClick={handleExportToFolder}>
                    📂 匯出至指定資料夾
                  </button>
                  <button className="btn-secondary" onClick={() => window.location.reload()} style={{ marginLeft: '10px' }}>
                    重新開始
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {!loading && step === 2 && (
        <div style={{ marginTop: '20px' }}>
          <button className="btn-secondary" onClick={() => setStep(1)}>
            ↩ 返回重新選擇 (Back)
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
