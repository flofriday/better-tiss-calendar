-- Migrating from legacy statistics to daily statistics
CREATE TABLE statistics_daily (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT DEFAULT (DATE('now')),
                token_hash TEXT NOT NULL,
                UNIQUE(date, token_hash)
);