CREATE TABLE IF NOT EXISTS sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_number TEXT NOT NULL,
    company_name TEXT NOT NULL,
    url TEXT NOT NULL,
    type TEXT NOT NULL,
    test_user_l1_login TEXT,
    test_user_l1_password TEXT,
    test_user_l2_login TEXT,
    test_user_l2_password TEXT,
    test_user_l3_login TEXT,
    test_user_l3_password TEXT,
    site_api_key TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_run TIMESTAMP
);
