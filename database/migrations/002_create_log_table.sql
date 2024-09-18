-- SQL migration script
CREATE TABLE IF NOT EXISTS log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER,
    plans TEXT,
    language_count INTEGER,
    languages TEXT,
    status_code INTEGER,
    status TEXT,
    iframe_integrity_status TEXT,
    iframe_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE
);