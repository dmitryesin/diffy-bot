CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    method TEXT NOT NULL,
    rounding SMALLINT NOT NULL,
    language TEXT NOT NULL,
    hints BOOLEAN NOT NULL
);

CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parameters JSONB NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE results (
    id SERIAL PRIMARY KEY,
    application_id INT NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    data JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);