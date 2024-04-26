-- Migrating from legacy statistics to daily statistics
CREATE TABLE statistics_daily (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT DEFAULT (DATE('now')),
                token_hash TEXT NOT NULL,
                UNIQUE(date, token_hash)
);
INSERT INTO statistics_daily (date, token_hash)
SELECT DISTINCT date(date) date, token_hash 
FROM statistics;