-- CreateTable
CREATE TABLE "trip_plan" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "destination" TEXT NOT NULL,
    "startingLocation" TEXT NOT NULL,
    "travelDatesStart" TEXT NOT NULL,
    "travelDatesEnd" TEXT,
    "dateInputType" TEXT NOT NULL DEFAULT 'picker',
    "duration" INTEGER,
    "travelingWith" TEXT NOT NULL,
    "adults" INTEGER NOT NULL DEFAULT 1,
    "children" INTEGER NOT NULL DEFAULT 0,
    "ageGroups" TEXT[],
    "budget" DOUBLE PRECISION NOT NULL,
    "budgetCurrency" TEXT NOT NULL DEFAULT 'USD',
    "travelStyle" TEXT NOT NULL,
    "budgetFlexible" BOOLEAN NOT NULL DEFAULT false,
    "vibes" TEXT[],
    "priorities" TEXT[],
    "interests" TEXT,
    "rooms" INTEGER NOT NULL DEFAULT 1,
    "pace" INTEGER[],
    "planningStyle" TEXT,
    "beenThereBefore" TEXT,
    "lovedPlaces" TEXT,
    "additionalInfo" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "userId" TEXT,

    CONSTRAINT "trip_plan_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "trip_plan" ADD CONSTRAINT "trip_plan_userId_fkey" FOREIGN KEY ("userId") REFERENCES "user"("id") ON DELETE CASCADE ON UPDATE CASCADE;
