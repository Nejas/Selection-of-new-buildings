ALTER TABLE public.new_buildings
    ADD COLUMN IF NOT EXISTS developer_name text,
    ADD COLUMN IF NOT EXISTS developer_global_id bigint,
    ADD COLUMN IF NOT EXISTS developer_inn character varying(12),
    ADD COLUMN IF NOT EXISTS developer_match_confidence numeric(5,2),
    ADD COLUMN IF NOT EXISTS developer_match_method character varying(50),
    ADD COLUMN IF NOT EXISTS developer_reliability_score numeric(5,2);

CREATE INDEX IF NOT EXISTS idx_new_buildings_developer_inn
    ON public.new_buildings (developer_inn);

