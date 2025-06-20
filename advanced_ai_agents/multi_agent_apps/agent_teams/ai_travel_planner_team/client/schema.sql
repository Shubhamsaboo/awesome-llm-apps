-- Create trip_plan_status table
CREATE TABLE "trip_plan_status" (
  "id" TEXT NOT NULL,
  "tripPlanId" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'pending',
  "currentStep" TEXT,
  "error" TEXT,
  "startedAt" TIMESTAMP,
  "completedAt" TIMESTAMP,
  "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP NOT NULL,
  CONSTRAINT "trip_plan_status_pkey" PRIMARY KEY ("id"),
  CONSTRAINT "trip_plan_status_tripPlanId_key" UNIQUE ("tripPlanId"),
  CONSTRAINT "trip_plan_status_tripPlanId_fkey" FOREIGN KEY ("tripPlanId") REFERENCES "trip_plan"("id") ON DELETE CASCADE
);
-- Create trip_plan_output table
CREATE TABLE "trip_plan_output" (
  "id" TEXT NOT NULL,
  "tripPlanId" TEXT NOT NULL,
  "itinerary" TEXT NOT NULL,
  "summary" TEXT,
  "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP NOT NULL,
  CONSTRAINT "trip_plan_output_pkey" PRIMARY KEY ("id"),
  CONSTRAINT "trip_plan_output_tripPlanId_key" UNIQUE ("tripPlanId"),
  CONSTRAINT "trip_plan_output_tripPlanId_fkey" FOREIGN KEY ("tripPlanId") REFERENCES "trip_plan"("id") ON DELETE CASCADE
);
-- Create indexes for better query performance
CREATE INDEX "idx_trip_plan_status_tripPlanId" ON "trip_plan_status"("tripPlanId");
CREATE INDEX "idx_trip_plan_output_tripPlanId" ON "trip_plan_output"("tripPlanId");