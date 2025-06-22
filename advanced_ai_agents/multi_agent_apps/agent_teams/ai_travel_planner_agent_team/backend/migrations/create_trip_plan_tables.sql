-- Create trip_plan_status table
CREATE TABLE IF NOT EXISTS trip_plan_status (
    id text NOT NULL,
    "tripPlanId" text NOT NULL,
    status text NOT NULL DEFAULT 'pending',
    "currentStep" text,
    error text,
    "startedAt" timestamp without time zone,
    "completedAt" timestamp without time zone,
    "createdAt" timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT trip_plan_status_pkey PRIMARY KEY (id)
);

-- Create index on tripPlanId for faster lookups
CREATE INDEX IF NOT EXISTS idx_trip_plan_status_trip_plan_id ON trip_plan_status("tripPlanId");

-- Create trip_plan_output table
CREATE TABLE IF NOT EXISTS trip_plan_output (
    id text NOT NULL,
    "tripPlanId" text NOT NULL,
    itinerary text NOT NULL,
    summary text,
    "createdAt" timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT trip_plan_output_pkey PRIMARY KEY (id)
);

-- Create index on tripPlanId for faster lookups
CREATE INDEX IF NOT EXISTS idx_trip_plan_output_trip_plan_id ON trip_plan_output("tripPlanId");

-- Create trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW."updatedAt" = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for trip_plan_status
CREATE TRIGGER update_trip_plan_status_updated_at
    BEFORE UPDATE ON trip_plan_status
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for trip_plan_output
CREATE TRIGGER update_trip_plan_output_updated_at
    BEFORE UPDATE ON trip_plan_output
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();