CREATE TABLE IF NOT EXISTS files (
    uid TEXT PRIMARY KEY,
    file_name TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    samplerate INTEGER NOT NULL,
    channels INTEGER NOT NULL,
    frames INTEGER NOT NULL,
    duration REAL NOT NULL,
    format TEXT NOT NULL,
    subtype TEXT NOT NULL,
    extra TEXT 
);

CREATE TABLE IF NOT EXISTS extractors (
    uid TEXT PRIMARY KEY,

    feature TEXT NOT NULL,
    feature_description TEXT NOT NULL,

    extractor TEXT NOT NULL,
    extractor_version TEXT NOT NULL,

    tool TEXT NOT NULL,
    tool_version TEXT NOT NULL,

    input_domain TEXT NOT NULL,

    output TEXT NOT NULL,   -- JSON serialized FeatureOutput

    parameters TEXT NOT NULL,        -- JSON
    dependencies TEXT NOT NULL       -- JSON
);

CREATE TABLE IF NOT EXISTS features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_uid TEXT NOT NULL,
    extractor_uid TEXT NOT NULL,
    value TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_uid)
        REFERENCES files(uid)
        ON DELETE CASCADE,
    FOREIGN KEY (extractor_uid)
        REFERENCES extractors(uid)
        ON DELETE CASCADE,
    UNIQUE(file_uid, extractor_uid)
);

CREATE TABLE IF NOT EXISTS logs (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    time      TEXT,
    level     TEXT,
    name      TEXT,
    message   TEXT,
    exception TEXT,
    context   TEXT
);

CREATE TABLE IF NOT EXISTS timing (
    name TEXT,
    category TEXT,
    start REAL,
    end REAL,
    duration REAL,
    call_site TEXT,
    iteration INTEGER,
    meta TEXT
);

CREATE TABLE runs (
    uid TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    metadata TEXT NOT NULL
);
