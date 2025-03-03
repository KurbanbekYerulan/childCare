-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    whatsapp_number TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Children table
CREATE TABLE IF NOT EXISTS children (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    age INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES users (id)
);

-- App usage data
CREATE TABLE IF NOT EXISTS app_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id INTEGER NOT NULL,
    app_name TEXT NOT NULL,
    window_name TEXT,
    browser_url TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration INTEGER,  -- in seconds
    category TEXT,
    is_appropriate INTEGER,  
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES children (id)
);

-- Alerts
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    child_id INTEGER NOT NULL,
    app_name TEXT NOT NULL,
    window_name TEXT,
    browser_url TEXT,
    alert_type TEXT NOT NULL, 
    severity TEXT NOT NULL,    
    description TEXT NOT NULL,
    screenshot_path TEXT,
    is_notified INTEGER DEFAULT 0, 
    is_resolved INTEGER DEFAULT 0, 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES children (id)
);

-- App analysis cache
CREATE TABLE IF NOT EXISTS app_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name TEXT NOT NULL,
    window_name TEXT,
    browser_url TEXT,
    category TEXT,
    is_appropriate INTEGER, 
    age_rating TEXT,
    educational_value INTEGER,
    potential_concerns TEXT,
    alternatives TEXT,
    analysis_json TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

