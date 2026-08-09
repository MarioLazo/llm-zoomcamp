-- query + response logs for monitoring
CREATE TABLE IF NOT EXISTS interactions (
    id            SERIAL PRIMARY KEY,
    ts            TIMESTAMPTZ NOT NULL DEFAULT now(),
    mode          TEXT NOT NULL,           -- chat | quotes | slides
    query         TEXT NOT NULL,
    rewritten     TEXT,
    answer        TEXT,
    model         TEXT,
    latency_ms    DOUBLE PRECISION,
    tokens_in     INTEGER,
    tokens_out    INTEGER,
    top_score     DOUBLE PRECISION,
    num_sources   INTEGER
);

-- thumbs up/down feedback, linked to an interaction
CREATE TABLE IF NOT EXISTS feedback (
    id             SERIAL PRIMARY KEY,
    interaction_id INTEGER REFERENCES interactions(id),
    ts             TIMESTAMPTZ NOT NULL DEFAULT now(),
    rating         TEXT NOT NULL,          -- up | down
    note           TEXT
);
