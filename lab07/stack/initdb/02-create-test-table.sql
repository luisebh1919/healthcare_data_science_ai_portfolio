-- Minimal table used to verify initdb execution.
CREATE TABLE IF NOT EXISTS cdm.test_table (
    test_id INTEGER PRIMARY KEY,
description VARCHAR(80) NOT NULL
);
