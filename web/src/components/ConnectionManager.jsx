import React, { useState, useEffect } from 'react';

function ConnectionManager({ apiUrl, onConnect, isLoading }) {
    const [connections, setConnections] = useState({});
    const [isAdding, setIsAdding] = useState(false);

    // Generic state for new connection form
    const [newConn, setNewConn] = useState({
        name: '',
        type: 'SQLite',
        path: '', // For SQLite
        host: 'localhost',
        port: '',
        username: '',
        password: '',
        database: '',
        isCustomStr: false,
        customStr: ''
    });

    useEffect(() => {
        fetchConnections();
    }, []);

    const fetchConnections = async () => {
        try {
            const res = await fetch(`${apiUrl}/api/connections`);
            const data = await res.json();
            setConnections(data);
        } catch (err) {
            console.error("Failed to fetch connections:", err);
        }
    };

    const handleDelete = async (name) => {
        if (!confirm(`確定要刪除連線 "${name}" 嗎?`)) return;
        try {
            await fetch(`${apiUrl}/api/connections/${name}`, { method: 'DELETE' });
            fetchConnections();
        } catch (err) {
            alert("刪除失敗");
        }
    };

    const handleConnect = async (name) => {
        if (isLoading) return;
        try {
            onConnect(null, true);
            const res = await fetch(`${apiUrl}/api/connect`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ connection_name: name })
            });
            if (!res.ok) throw new Error(await res.text());
            const data = await res.json();
            onConnect(data.tables, false);
        } catch (err) {
            console.error(err);
            alert(`連線失敗: ${err.message}`);
            onConnect(null, false);
        }
    };

    const buildConnectionString = () => {
        const { type, path, host, port, username, password, database, isCustomStr, customStr } = newConn;

        if (isCustomStr && customStr) return customStr;

        switch (type) {
            case 'SQLite':
                return `sqlite:///${path.replace(/\\/g, '/')}`;
            case 'PostgreSQL':
                // postgresql+psycopg2://user:password@host:port/dbname[?key=value&key=value...]
                return `postgresql+psycopg2://${username}:${password}@${host}${port ? ':' + port : ''}/${database}`;
            case 'MySQL':
                // mysql+pymysql://
                return `mysql+pymysql://${username}:${password}@${host}${port ? ':' + port : ''}/${database}`;
            case 'MSSQL':
                // mssql+pyodbc://
                return `mssql+pyodbc://${username}:${password}@${host}${port ? ':' + port : ''}/${database}?driver=ODBC+Driver+17+for+SQL+Server`;
            default:
                return '';
        }
    };

    const handleSave = async () => {
        if (!newConn.name) {
            alert("請輸入連線名稱");
            return;
        }

        const connStr = buildConnectionString();
        if (!connStr) {
            alert("請填寫完整的連線資訊");
            return;
        }

        const payload = {
            name: newConn.name,
            type: newConn.type,
            // Store params just for reference if needed, but mainly we use connection_string
            params: {
                path: newConn.path,
                host: newConn.host,
                database: newConn.database
            },
            connection_string: connStr
        };

        try {
            await fetch(`${apiUrl}/api/connections`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            setIsAdding(false);
            // Reset form defaults 
            setNewConn({ ...newConn, name: '', path: '', password: '', database: '' });
            fetchConnections();
        } catch (err) {
            alert("儲存失敗");
        }
    };

    return (
        <div className="connection-manager card-conn">
            {/* Reduced styled for inner card if needed, or just let App.css handle generic .card */}
            <h3 style={{ marginTop: 0 }}>資料庫連線 (Database Connections)</h3>

            <div className="conn-list">
                {Object.keys(connections).length === 0 ? (
                    <p style={{ color: '#888', fontStyle: 'italic' }}>目前沒有儲存的連線</p>
                ) : (
                    Object.values(connections).map(conn => (
                        <div key={conn.name} className="conn-item">
                            <div className="conn-info">
                                <strong>{conn.name}</strong>
                                <small style={{ opacity: 0.7, fontSize: '0.75rem' }}>{conn.type}</small>
                            </div>
                            <div className="conn-actions">
                                <button
                                    onClick={() => handleConnect(conn.name)}
                                    disabled={isLoading}
                                    className="btn-primary-small"
                                    title="Connect & Import"
                                >
                                    連線
                                </button>
                                <button
                                    onClick={() => handleDelete(conn.name)}
                                    disabled={isLoading}
                                    className="btn-danger-small"
                                    title="Remove"
                                >
                                    刪除
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {!isAdding ? (
                <button className="btn-secondary" onClick={() => setIsAdding(true)} style={{ width: '100%' }}>
                    + 新增連線 (Add New)
                </button>
            ) : (
                <div className="add-conn-form">
                    <h4 style={{ marginTop: 0, marginBottom: '10px', color: 'var(--neon)' }}>新增連線設定</h4>

                    <div className="form-group" style={{ marginBottom: '10px' }}>
                        <label>顯示名稱 (Name)</label>
                        <input
                            type="text"
                            placeholder="My Database"
                            value={newConn.name}
                            onChange={e => setNewConn({ ...newConn, name: e.target.value })}
                        />
                    </div>

                    <div className="form-group" style={{ marginBottom: '10px' }}>
                        <label>資料庫類型 (Type)</label>
                        <select
                            value={newConn.type}
                            onChange={e => setNewConn({ ...newConn, type: e.target.value })}
                        >
                            <option value="SQLite">SQLite (Local File)</option>
                            <option value="PostgreSQL">PostgreSQL</option>
                            <option value="MySQL">MySQL / MariaDB</option>
                            <option value="MSSQL">Microsoft SQL Server</option>
                        </select>
                    </div>

                    {newConn.type === 'SQLite' ? (
                        <div className="form-group">
                            <label>檔案路徑 (.db File Path)</label>
                            <input
                                type="text"
                                placeholder="C:/path/to/database.db"
                                value={newConn.path}
                                onChange={e => setNewConn({ ...newConn, path: e.target.value })}
                            />
                        </div>
                    ) : (
                        <>
                            <div style={{ display: 'flex', gap: '10px' }}>
                                <div style={{ flex: 2 }}>
                                    <label>主機 (Host)</label>
                                    <input
                                        type="text"
                                        placeholder="localhost"
                                        value={newConn.host}
                                        onChange={e => setNewConn({ ...newConn, host: e.target.value })}
                                    />
                                </div>
                                <div style={{ flex: 1 }}>
                                    <label>埠號 (Port)</label>
                                    <input
                                        type="text"
                                        placeholder={
                                            newConn.type === 'PostgreSQL' ? '5432' :
                                                newConn.type === 'MySQL' ? '3306' :
                                                    newConn.type === 'MSSQL' ? '1433' : ''
                                        }
                                        value={newConn.port}
                                        onChange={e => setNewConn({ ...newConn, port: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div style={{ display: 'flex', gap: '10px' }}>
                                <div style={{ flex: 1 }}>
                                    <label>使用者 (User)</label>
                                    <input
                                        type="text"
                                        placeholder="username"
                                        value={newConn.username}
                                        onChange={e => setNewConn({ ...newConn, username: e.target.value })}
                                    />
                                </div>
                                <div style={{ flex: 1 }}>
                                    <label>密碼 (Pwd)</label>
                                    <input
                                        type="password"
                                        placeholder="password"
                                        value={newConn.password}
                                        onChange={e => setNewConn({ ...newConn, password: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>資料庫名稱 (DB Name)</label>
                                <input
                                    type="text"
                                    placeholder="my_database"
                                    value={newConn.database}
                                    onChange={e => setNewConn({ ...newConn, database: e.target.value })}
                                />
                            </div>
                        </>
                    )}

                    <div className="form-actions" style={{ marginTop: '15px' }}>
                        <button onClick={handleSave} className="btn-primary-small">儲存連線</button>
                        <button onClick={() => setIsAdding(false)} className="btn-secondary-small">取消</button>
                    </div>
                </div>
            )}
        </div>
    );
}

export default ConnectionManager;
