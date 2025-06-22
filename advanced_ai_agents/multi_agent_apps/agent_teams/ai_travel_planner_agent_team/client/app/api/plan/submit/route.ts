import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

interface TripFormData {
  name: string;
  destination: string;
  startingLocation: string;
  travelDates: { start: string; end: string };
  dateInputType: "picker" | "text";
  duration: number;
  travelingWith: string;
  adults: number;
  children: number;
  ageGroups: string[];
  budget: number;
  budgetCurrency: string;
  travelStyle: string;
  budgetFlexible: boolean;
  vibes: string[];
  priorities: string[];
  interests?: string;
  rooms: number;
  pace: number[];
  beenThereBefore?: string;
  lovedPlaces?: string;
  additionalInfo?: string;
}

export async function POST(request: NextRequest) {
  try {
    const tripData: TripFormData = await request.json();

    // Log the trip data for debugging
    console.log('Received trip planning data:', JSON.stringify(tripData, null, 2));

    // Validate required fields
    if (!tripData.name || !tripData.destination || !tripData.startingLocation) {
      return NextResponse.json(
        {
          success: false,
          message: 'Missing required fields: name, destination, or starting location'
        },
        { status: 400 }
      );
    }

    // Save to database
    const savedTripPlan = await prisma.tripPlan.create({
      data: {
        name: tripData.name,
        destination: tripData.destination,
        startingLocation: tripData.startingLocation,
        travelDatesStart: tripData.travelDates.start,
        travelDatesEnd: tripData.travelDates.end || null,
        dateInputType: tripData.dateInputType || "picker",
        duration: tripData.duration || null,
        travelingWith: tripData.travelingWith,
        adults: tripData.adults || 1,
        children: tripData.children || 0,
        ageGroups: tripData.ageGroups || [],
        budget: tripData.budget,
        budgetCurrency: tripData.budgetCurrency || "USD",
        travelStyle: tripData.travelStyle,
        budgetFlexible: tripData.budgetFlexible || false,
        vibes: tripData.vibes || [],
        priorities: tripData.priorities || [],
        interests: tripData.interests || null,
        rooms: tripData.rooms || 1,
        pace: tripData.pace || [3],
        beenThereBefore: tripData.beenThereBefore || null,
        lovedPlaces: tripData.lovedPlaces || null,
        additionalInfo: tripData.additionalInfo || null,
        // userId can be added later when auth is implemented
        userId: null
      }
    });

    console.log('Trip plan saved to database:', savedTripPlan.id);

    const requestBody = {
      trip_plan_id: savedTripPlan.id,
      travel_plan: {
        name: tripData.name,
        destination: tripData.destination,
        starting_location: tripData.startingLocation,
        travel_dates: {
          start: tripData.travelDates.start,
          end: tripData.travelDates.end || ""
        },
        date_input_type: tripData.dateInputType,
        duration: tripData.duration,
        traveling_with: tripData.travelingWith,
        adults: tripData.adults,
        children: tripData.children,
        age_groups: tripData.ageGroups,
        budget: tripData.budget,
        budget_currency: tripData.budgetCurrency,
        travel_style: tripData.travelStyle,
        budget_flexible: tripData.budgetFlexible,
        vibes: tripData.vibes,
        priorities: tripData.priorities,
        interests: tripData.interests || "",
        rooms: tripData.rooms,
        pace: tripData.pace,
        been_there_before: tripData.beenThereBefore || "",
        loved_places: tripData.lovedPlaces || "",
        additional_info: tripData.additionalInfo || ""
      }
    }

    console.log('Request body:', JSON.stringify(requestBody, null, 2));

    // Call backend API to trigger trip planning
    const backendResponse = await fetch(`${process.env.BACKEND_API_URL}/api/plan/trigger`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    });

    if (!backendResponse.ok) {
      console.error('Backend API error:', await backendResponse.text());
      return NextResponse.json(
        {
          success: false,
          message: 'Failed to trigger trip planning'
        },
        { status: 500 }
      );
    }

    const responseData = await backendResponse.json();
    console.log('Backend response:', JSON.stringify(responseData, null, 2));

    return NextResponse.json(
      {
        success: true,
        message: 'Trip planning triggered successfully',
        response: responseData,
        tripPlanId: savedTripPlan.id
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Error processing trip submission:', error);
    return NextResponse.json(
      {
        success: false,
        message: 'Failed to save trip plan to database'
      },
      { status: 500 }
    );
  }
}