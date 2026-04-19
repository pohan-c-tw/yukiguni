ALTER TABLE analysis_jobs
ADD COLUMN video_duration_seconds DOUBLE PRECISION,
ADD COLUMN video_width INTEGER,
ADD COLUMN video_height INTEGER;

UPDATE analysis_jobs
SET
    video_duration_seconds = 0,
    video_width = 0,
    video_height = 0
WHERE
    video_duration_seconds IS NULL
    OR video_width IS NULL
    OR video_height IS NULL;

ALTER TABLE analysis_jobs
ALTER COLUMN video_duration_seconds SET NOT NULL,
ALTER COLUMN video_width SET NOT NULL,
ALTER COLUMN video_height SET NOT NULL;
