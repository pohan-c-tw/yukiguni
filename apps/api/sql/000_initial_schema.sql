CREATE TABLE analysis_jobs (
    id UUID PRIMARY KEY,
    status TEXT NOT NULL CHECK (
        status IN ('uploaded', 'validating', 'processing', 'done', 'failed')
    ),
    original_filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    input_object_key TEXT NOT NULL,
    output_object_key TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
