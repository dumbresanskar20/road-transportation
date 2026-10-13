-- Schema for Road Transportation Expert System Assessment History

CREATE TABLE IF NOT EXISTS assessments (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    traffic TEXT NOT NULL,
    weather TEXT NOT NULL,
    road_condition TEXT NOT NULL,
    road_status TEXT NOT NULL,
    vehicle_condition TEXT NOT NULL,
    fuel TEXT NOT NULL,
    accident_reported TEXT NOT NULL,
    emergency_reported TEXT NOT NULL,
    input_facts_json TEXT NOT NULL,
    activated_rule_ids_json TEXT NOT NULL,
    recommendations_json TEXT NOT NULL,
    explanations_json TEXT NOT NULL,
    summary TEXT NOT NULL,
    highest_priority TEXT NOT NULL,
    rule_count INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_assessments_timestamp ON assessments(timestamp);
CREATE INDEX IF NOT EXISTS idx_assessments_priority ON assessments(highest_priority);
CREATE INDEX IF NOT EXISTS idx_assessments_traffic ON assessments(traffic);
CREATE INDEX IF NOT EXISTS idx_assessments_weather ON assessments(weather);
