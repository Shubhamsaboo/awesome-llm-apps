"use client";

import { useEffect, useState, useCallback } from "react";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  CalendarDays,
  Clock,
  DollarSign,
  Globe,
  Info,
  Landmark,
  MapPin,
  Moon,
  Paperclip,
  Plane,
  Sun,
  Users,
  Heart,
  Home,
  Loader2,
  Lightbulb,
  Utensils,
  Receipt,
} from "lucide-react";
import Link from "next/link";
import { format } from "date-fns";
import { useParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";

// Type Definitions
interface DayPlan {
  day: number;
  date: string;
  morning: string;
  afternoon: string;
  evening: string;
  notes?: string;
}

interface Hotel {
  hotel_name: string;
  price: string;
  rating: string;
  address: string;
  amenities: string[];
  description?: string;
  url?: string;
}

interface Attraction {
  name: string;
  description?: string;
}

interface Flight {
  duration: string;
  price: string;
  departure_time: string;
  arrival_time: string;
  airline: string;
  flight_number?: string;
  url?: string;
  stops?: number;
}

interface Restaurant {
  name: string;
  description?: string;
  location?: string;
  url?: string;
}

interface Itinerary {
  day_by_day_plan: DayPlan[];
  hotels: Hotel[];
  attractions: Attraction[];
  flights: Flight[];
  restaurants?: Restaurant[];
  tips?: string[];
  budget_insights?: string[];
}

interface TripDetails {
  id: string;
  name?: string;
  status: "pending" | "completed" | "failed" | "in-progress";
  itinerary?: Itinerary;
  // Raw agent responses
  budget_agent_response?: string;
  destination_agent_response?: string;
  flight_agent_response?: string;
  restaurant_agent_response?: string;
  itinerary_agent_response?: string;
  current_step?: string;
  // Input details
  destination?: string;
  startingLocation?: string;
  travelDatesStart?: string;
  travelDatesEnd?: string;
  dateInputType?: string;
  duration?: number;
  travelingWith?: string;
  adults?: number;
  children?: number;
  ageGroups?: string[];
  budget?: number;
  budgetCurrency?: string;
  travelStyle?: string;
  budgetFlexible?: boolean;
  vibes?: string[];
  priorities?: string[];
  interests?: string;
  rooms?: number;
  pace?: number[];
  beenThereBefore?: string;
  lovedPlaces?: string;
  additionalInfo?: string;
}

// Helper functions
const formatCurrency = (amount?: number, currency?: string) => {
  if (!amount) return "Not specified";
  const symbols: Record<string, string> = {
    USD: "$",
    EUR: "€",
    GBP: "£",
    INR: "₹",
    JPY: "¥",
  };
  return `${symbols[currency || "USD"] || "$"}${amount.toLocaleString()}`;
};

const formatDate = (dateString?: string, inputType?: string) => {
  if (!dateString || inputType === "text") {
    return dateString || "Flexible dates";
  }
  try {
    return format(new Date(dateString), "MMM dd, yyyy");
  } catch {
    return dateString;
  }
};

const getPaceDescription = (pace?: number[]) => {
  if (!pace || !pace.length) return "Balanced";
  const paceValue = pace[0] || 3;
  const descriptions = {
    1: "Very relaxed",
    2: "Mostly relaxed",
    3: "Balanced",
    4: "Quite busy",
    5: "Action-packed",
  };
  return descriptions[paceValue as keyof typeof descriptions] || "Balanced";
};

// Helper function to render status badge
function StatusBadge({ status }: { status: TripDetails["status"] }) {
  let variant: "default" | "secondary" | "destructive" | "outline" = "default";
  let text = status.toUpperCase();

  switch (status) {
    case "completed":
      variant = "default"; // Using Tailwind's green for success
      text = "Completed";
      break;
    case "pending":
      variant = "secondary"; // Using Tailwind's yellow for pending
      text = "Pending";
      break;
    case "in-progress":
      variant = "outline"; // Using Tailwind's blue for in-progress
      text = "In Progress";
      break;
    case "failed":
      variant = "destructive";
      text = "Failed";
      break;
  }
  return (
    <Badge
      variant={variant}
      className={
        status === "completed"
          ? "bg-green-500 hover:bg-green-600 text-white"
          : status === "pending"
          ? "bg-yellow-500 hover:bg-yellow-600 text-black"
          : status === "in-progress"
          ? "bg-blue-500 hover:bg-blue-600 text-white"
          : ""
      }
    >
      {text}
    </Badge>
  );
}

export default function TripDetailsPage() {
  const params = useParams<{ id: string }>();
  const tripId = params.id;

  const [trip, setTrip] = useState<TripDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [polling, setPolling] = useState(false);
  const [retryLoading, setRetryLoading] = useState(false);

  // Function to fetch trip details
  const fetchTripDetails = useCallback(async () => {
    if (!tripId) return;

    try {
      setLoading(true);
      const response = await fetch(`/api/plans/${tripId}`);
      const data = await response.json();

      console.log("API Response:", data);

      if (!response.ok) {
        throw new Error(data.message || "Failed to fetch trip details");
      }

      if (data.success && data.tripPlan) {
        // Convert raw data to our TripDetails format
        const tripPlan = data.tripPlan;
        console.log("Trip plan data:", tripPlan);

        // Map the database status to our TripDetails status
        let status: TripDetails["status"] = "pending";
        if (tripPlan.status) {
          switch (tripPlan.status.status) {
            case "completed":
              status = "completed";
              break;
            case "processing":
              status = "in-progress";
              break;
            case "failed":
              status = "failed";
              break;
            default:
              status = "pending";
          }
        }

        // Parse the itinerary JSON if it exists
        let itinerary: Itinerary | undefined;

        // Extract all agent responses from the parsed JSON
        let budget_agent_response = "";
        let destination_agent_response = "";
        let flight_agent_response = "";
        let restaurant_agent_response = "";
        let itinerary_agent_response = "";

        if (tripPlan.output?.itinerary) {
          try {
            // First parse the outer JSON string
            const parsedOutput = JSON.parse(tripPlan.output.itinerary);
            console.log("Parsed output:", parsedOutput);

            // Extract agent responses from the parsed JSON
            budget_agent_response = parsedOutput.budget_agent_response || "";
            destination_agent_response =
              parsedOutput.destination_agent_response || "";
            flight_agent_response = parsedOutput.flight_agent_response || "";
            restaurant_agent_response =
              parsedOutput.restaurant_agent_response || "";
            itinerary_agent_response =
              parsedOutput.itinerary_agent_response || "";

            if (parsedOutput.itinerary) {
              // Then parse the inner JSON string to get the actual itinerary
              itinerary = JSON.parse(parsedOutput.itinerary) as Itinerary;
              console.log("Parsed itinerary:", itinerary);
            }
          } catch (e) {
            console.error("Failed to parse itinerary JSON:", e);
          }
        }

        console.log("Budget agent response:", budget_agent_response);
        console.log("Destination agent response:", destination_agent_response);

        const tripDetails: TripDetails = {
          id: tripPlan.id,
          name: tripPlan.name,
          status,
          itinerary,
          // Extract current step from status if available
          current_step: tripPlan.status?.currentStep || undefined,
          // Raw agent responses
          budget_agent_response,
          destination_agent_response,
          flight_agent_response,
          restaurant_agent_response,
          itinerary_agent_response,
          // Input details
          destination: tripPlan.destination,
          startingLocation: tripPlan.startingLocation,
          travelDatesStart: tripPlan.travelDatesStart
            ? String(tripPlan.travelDatesStart)
            : undefined,
          travelDatesEnd: tripPlan.travelDatesEnd
            ? String(tripPlan.travelDatesEnd)
            : undefined,
          dateInputType: tripPlan.dateInputType,
          duration: tripPlan.duration ?? undefined,
          travelingWith: tripPlan.travelingWith,
          adults: tripPlan.adults,
          children: tripPlan.children,
          ageGroups: tripPlan.ageGroups as string[],
          budget: tripPlan.budget,
          budgetCurrency: tripPlan.budgetCurrency,
          travelStyle: tripPlan.travelStyle,
          budgetFlexible: tripPlan.budgetFlexible,
          vibes: tripPlan.vibes as string[],
          priorities: tripPlan.priorities as string[],
          interests: tripPlan.interests ?? undefined,
          rooms: tripPlan.rooms,
          pace: tripPlan.pace as number[],
          beenThereBefore: tripPlan.beenThereBefore ?? undefined,
          lovedPlaces: tripPlan.lovedPlaces ?? undefined,
          additionalInfo: tripPlan.additionalInfo ?? undefined,
        };

        console.log("Setting trip state:", tripDetails);
        setTrip(tripDetails);
      } else {
        setError("Trip plan not found");
      }
    } catch (err) {
      console.error("Error fetching trip details:", err);
      setError(
        `Failed to fetch trip details: ${
          err instanceof Error ? err.message : "Unknown error"
        }`
      );
    } finally {
      setLoading(false);
    }
  }, [tripId]);

  // Function to retry a failed trip plan
  const retryTripPlan = async () => {
    if (!tripId) return;

    try {
      setRetryLoading(true);
      const response = await fetch(`/api/plans/${tripId}/retry`, {
        method: "POST",
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Failed to retry trip plan");
      }

      // Refresh trip details after retry
      await fetchTripDetails();

      // Start polling again
      setPolling(true);
    } catch (err) {
      console.error("Error retrying trip plan:", err);
      setError(
        `Failed to retry trip plan: ${
          err instanceof Error ? err.message : "Unknown error"
        }`
      );
    } finally {
      setRetryLoading(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchTripDetails();
  }, [fetchTripDetails]);

  // Setup polling
  useEffect(() => {
    if (!trip) return;

    // Check if we should poll
    const shouldPoll = trip.status !== "completed" && trip.status !== "failed";

    if (shouldPoll) {
      setPolling(true);
      const pollInterval = setInterval(fetchTripDetails, 5000);

      return () => {
        clearInterval(pollInterval);
        setPolling(false);
      };
    } else {
      setPolling(false);
    }
  }, [trip, trip?.status, tripId, fetchTripDetails]);

  // Render loading state
  if (loading && !trip) {
    return (
      <div className="container mx-auto p-4 flex flex-col items-center justify-center min-h-[calc(100vh-10rem)]">
        <Loader2 size={48} className="animate-spin text-primary mb-4" />
        <h1 className="text-2xl font-semibold mb-2">Loading Trip Details</h1>
        <p className="text-muted-foreground text-center">
          Fetching your trip plan...
        </p>
      </div>
    );
  }

  // Render error state
  if (error || !trip) {
    return (
      <div className="container mx-auto p-4 flex flex-col items-center justify-center min-h-[calc(100vh-10rem)]">
        <Landmark size={64} className="text-muted-foreground mb-4" />
        <h1 className="text-2xl font-semibold mb-2">Trip Not Found</h1>
        <p className="text-muted-foreground text-center">
          {error ||
            "The trip you are looking for does not exist or could not be loaded."}
        </p>
        <Link href="/plans" className="mt-4 text-primary hover:underline">
          Go to your trip plans
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 md:p-8 space-y-8">
      <header className="flex flex-col space-y-2">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between">
          <div>
            {trip.destination && (
              <h1 className="text-3xl md:text-4xl font-bold tracking-tight flex items-center">
                <MapPin className="h-6 w-6 mr-2 text-primary" />
                {trip.destination}
              </h1>
            )}
            {trip.name && trip.name !== trip.destination && (
              <p className="text-xl text-muted-foreground mt-1">{trip.name}</p>
            )}
          </div>
          <div className="flex items-center gap-2">
            {polling && (
              <div className="flex items-center text-sm text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin mr-1" />
                Updating...
              </div>
            )}
            <StatusBadge status={trip.status} />
          </div>
        </div>
      </header>

      <Separator />

      {/* Trip Input Details Section */}
      <section className="bg-muted/30 rounded-lg p-6 border border-border">
        <h2 className="text-2xl font-semibold mb-4 flex items-center">
          <Globe className="mr-3 h-6 w-6 text-primary" /> Trip Details
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Destination and Location */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center">
                <MapPin className="h-4 w-4 mr-2 text-primary" />
                Destination
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div>
                  <span className="font-medium">To:</span>{" "}
                  <span className="text-muted-foreground">
                    {trip.destination}
                  </span>
                </div>
                <div>
                  <span className="font-medium">From:</span>{" "}
                  <span className="text-muted-foreground">
                    {trip.startingLocation}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Dates and Duration */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center">
                <CalendarDays className="h-4 w-4 mr-2 text-primary" />
                Travel Dates
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div>
                  <span className="font-medium">From:</span>{" "}
                  <span className="text-muted-foreground">
                    {formatDate(trip.travelDatesStart, trip.dateInputType)}
                  </span>
                </div>
                {trip.travelDatesEnd && (
                  <div>
                    <span className="font-medium">To:</span>{" "}
                    <span className="text-muted-foreground">
                      {formatDate(trip.travelDatesEnd, trip.dateInputType)}
                    </span>
                  </div>
                )}
                {trip.duration && (
                  <div>
                    <span className="font-medium">Duration:</span>{" "}
                    <span className="text-muted-foreground">
                      {trip.duration} days
                    </span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Travelers */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center">
                <Users className="h-4 w-4 mr-2 text-primary" />
                Travelers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div>
                  <span className="font-medium">Type:</span>{" "}
                  <span className="text-muted-foreground">
                    {trip.travelingWith}
                  </span>
                </div>
                <div>
                  <span className="font-medium">Group:</span>{" "}
                  <span className="text-muted-foreground">
                    {trip.adults} adult{trip.adults !== 1 ? "s" : ""}
                    {trip.children && trip.children > 0
                      ? `, ${trip.children} child${
                          trip.children !== 1 ? "ren" : ""
                        }`
                      : ""}
                  </span>
                </div>
                {trip.ageGroups && trip.ageGroups.length > 0 && (
                  <div>
                    <span className="font-medium">Ages:</span>{" "}
                    <span className="text-muted-foreground">
                      {trip.ageGroups.join(", ")}
                    </span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Accommodation */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center">
                <Home className="h-4 w-4 mr-2 text-primary" />
                Accommodation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div>
                  <span className="font-medium">Type:</span>{" "}
                  <span className="text-muted-foreground">
                    {trip.travelStyle}
                  </span>
                </div>
                <div>
                  <span className="font-medium">Rooms:</span>{" "}
                  <span className="text-muted-foreground">{trip.rooms}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Budget */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center">
                <DollarSign className="h-4 w-4 mr-2 text-primary" />
                Budget
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div>
                  <span className="font-medium">Amount:</span>{" "}
                  <span className="text-muted-foreground">
                    {formatCurrency(trip.budget, trip.budgetCurrency)} per
                    person
                  </span>
                </div>
                <div>
                  <span className="font-medium">Flexible:</span>{" "}
                  <span className="text-muted-foreground">
                    {trip.budgetFlexible ? "Yes" : "No"}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Trip Style */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center">
                <Heart className="h-4 w-4 mr-2 text-primary" />
                Trip Style
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <span className="font-medium">Pace:</span>{" "}
                  <span className="text-muted-foreground">
                    {getPaceDescription(trip.pace)}
                  </span>
                </div>
                {trip.vibes && trip.vibes.length > 0 && (
                  <div>
                    <span className="font-medium block mb-1">Vibes:</span>
                    <div className="flex flex-wrap gap-1">
                      {trip.vibes.map((vibe) => (
                        <Badge
                          key={vibe}
                          variant="secondary"
                          className="text-xs"
                        >
                          {vibe}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                {trip.priorities && trip.priorities.length > 0 && (
                  <div>
                    <span className="font-medium block mb-1">Priorities:</span>
                    <div className="flex flex-wrap gap-1">
                      {trip.priorities.map((priority) => (
                        <Badge
                          key={priority}
                          variant="outline"
                          className="text-xs"
                        >
                          {priority}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Additional Information */}
        {(trip.interests ||
          trip.beenThereBefore ||
          trip.lovedPlaces ||
          trip.additionalInfo) && (
          <div className="mt-6">
            <h3 className="text-xl font-semibold mb-3">
              Additional Information
            </h3>
            <Card>
              <CardContent className="pt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                {trip.interests && (
                  <div>
                    <h4 className="font-medium mb-1">Specific Interests:</h4>
                    <p className="text-muted-foreground text-sm">
                      {trip.interests}
                    </p>
                  </div>
                )}
                {trip.beenThereBefore && (
                  <div>
                    <h4 className="font-medium mb-1">Previous Visits:</h4>
                    <p className="text-muted-foreground text-sm">
                      {trip.beenThereBefore}
                    </p>
                  </div>
                )}
                {trip.lovedPlaces && (
                  <div>
                    <h4 className="font-medium mb-1">Loved Places:</h4>
                    <p className="text-muted-foreground text-sm">
                      {trip.lovedPlaces}
                    </p>
                  </div>
                )}
                {trip.additionalInfo && (
                  <div className="md:col-span-2">
                    <h4 className="font-medium mb-1">
                      Additional Information:
                    </h4>
                    <p className="text-muted-foreground text-sm">
                      {trip.additionalInfo}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </section>

      {/* Show loading message or itinerary based on status */}
      {(trip.status === "pending" ||
        trip.status === "in-progress" ||
        trip.status === "failed") && (
        <div className="text-center py-10 border rounded-lg">
          <Info size={48} className="text-muted-foreground mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">
            {trip.status === "pending" && "Trip Plan in Progress"}
            {trip.status === "in-progress" && "Trip Plan is Being Generated"}
            {trip.status === "failed" && "Failed to Generate Trip Plan"}
          </h2>
          <p className="text-muted-foreground">
            {trip.status === "pending" &&
              "Your trip itinerary is currently being planned. Please wait as we create your personalized travel plan."}
            {trip.status === "in-progress" &&
              "We are working on your trip details. This might take a few moments. The page will automatically update when your plan is ready."}
            {trip.status === "failed" &&
              "Something went wrong while generating your trip plan. Please try again or contact support."}
          </p>

          {/* Show current step when available */}
          {(trip.status === "pending" || trip.status === "in-progress") &&
            trip.current_step && (
              <div className="mt-4 bg-muted/30 p-4 rounded-lg max-w-md mx-auto">
                <h3 className="font-medium text-sm mb-1">Current Progress:</h3>
                <p className="text-primary font-medium">{trip.current_step}</p>
              </div>
            )}

          {(trip.status === "pending" || trip.status === "in-progress") && (
            <div className="flex justify-center mt-4">
              <div className="flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full">
                <Loader2 className="h-4 w-4 animate-spin" />
                Updating automatically...
              </div>
            </div>
          )}

          {/* Add retry button for failed plans */}
          {trip.status === "failed" && (
            <div className="flex justify-center mt-6">
              <button
                onClick={retryTripPlan}
                disabled={retryLoading}
                className="flex items-center gap-2 bg-primary text-primary-foreground px-6 py-2 rounded-md hover:bg-primary/90 transition-colors"
              >
                {retryLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Retrying...
                  </>
                ) : (
                  <>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M21 2v6h-6"></path>
                      <path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path>
                      <path d="M3 22v-6h6"></path>
                      <path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path>
                    </svg>
                    Retry Plan Generation
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Show tabbed content when completed */}
      {trip.status === "completed" && (
        <Tabs defaultValue="itinerary" className="w-full">
          <TabsList className="mb-4 flex w-full justify-start overflow-auto">
            <TabsTrigger value="itinerary" className="flex items-center">
              <CalendarDays className="h-4 w-4 mr-2" /> Itinerary
            </TabsTrigger>
            <TabsTrigger value="guide" className="flex items-center">
              <Lightbulb className="h-4 w-4 mr-2" /> Destination Guide
            </TabsTrigger>
            <TabsTrigger value="hotels" className="flex items-center">
              <Home className="h-4 w-4 mr-2" /> Hotels
            </TabsTrigger>
            <TabsTrigger value="flights" className="flex items-center">
              <Plane className="h-4 w-4 mr-2" /> Flights
            </TabsTrigger>
            <TabsTrigger value="dining" className="flex items-center">
              <Utensils className="h-4 w-4 mr-2" /> Dining
            </TabsTrigger>
            <TabsTrigger value="budget" className="flex items-center">
              <Receipt className="h-4 w-4 mr-2" /> Budget
            </TabsTrigger>
          </TabsList>

          {/* Itinerary Tab Content */}
          <TabsContent value="itinerary" className="space-y-8">
            {trip.itinerary && (
              <div className="space-y-12">
                {/* Day-by-Day Plan Section */}
                <section>
                  <h2 className="text-2xl font-semibold mb-6 flex items-center">
                    <CalendarDays className="mr-3 h-6 w-6 text-primary" /> Daily
                    Itinerary
                  </h2>
                  <div className="grid grid-cols-1 gap-6">
                    {trip.itinerary.day_by_day_plan.map((dayPlan) => (
                      <Card
                        key={dayPlan.day}
                        className="overflow-hidden border-l-4 border-l-primary"
                      >
                        <CardHeader className="bg-muted/50 pb-3">
                          <div className="flex items-center justify-between">
                            <CardTitle className="text-xl flex items-center">
                              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground mr-3">
                                {dayPlan.day}
                              </span>
                              <span>Day {dayPlan.day}</span>
                            </CardTitle>
                            {dayPlan.date && (
                              <Badge variant="outline" className="ml-auto">
                                <CalendarDays className="mr-1 h-3 w-3" />
                                {new Date(dayPlan.date).toLocaleDateString(
                                  undefined,
                                  {
                                    year: "numeric",
                                    month: "long",
                                    day: "numeric",
                                  }
                                )}
                              </Badge>
                            )}
                          </div>
                        </CardHeader>
                        <CardContent className="pt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
                          <div className="bg-muted/30 p-4 rounded-lg border border-border">
                            <div className="flex items-center mb-3">
                              <Sun className="h-5 w-5 mr-2 text-yellow-500" />
                              <h3 className="font-medium">Morning</h3>
                            </div>
                            <p className="text-muted-foreground whitespace-pre-line">
                              {dayPlan.morning}
                            </p>
                          </div>
                          <div className="bg-muted/30 p-4 rounded-lg border border-border">
                            <div className="flex items-center mb-3">
                              <Sun className="h-5 w-5 mr-2 text-orange-500" />
                              <h3 className="font-medium">Afternoon</h3>
                            </div>
                            <p className="text-muted-foreground whitespace-pre-line">
                              {dayPlan.afternoon}
                            </p>
                          </div>
                          <div className="bg-muted/30 p-4 rounded-lg border border-border">
                            <div className="flex items-center mb-3">
                              <Moon className="h-5 w-5 mr-2 text-indigo-500" />
                              <h3 className="font-medium">Evening</h3>
                            </div>
                            <p className="text-muted-foreground whitespace-pre-line">
                              {dayPlan.evening}
                            </p>
                          </div>
                        </CardContent>
                        {dayPlan.notes && (
                          <div className="px-6 py-3 bg-muted/10">
                            <div className="flex items-start">
                              <Paperclip className="h-5 w-5 mr-2 mt-0.5 text-primary flex-shrink-0" />
                              <p className="text-sm text-muted-foreground">
                                <span className="font-medium">Note:</span>{" "}
                                {dayPlan.notes}
                              </p>
                            </div>
                          </div>
                        )}
                      </Card>
                    ))}
                  </div>
                </section>

                {/* Attractions Section */}
                {trip.itinerary.attractions &&
                  trip.itinerary.attractions.length > 0 && (
                    <section>
                      <h2 className="text-2xl font-semibold mb-6 flex items-center">
                        <Landmark className="mr-3 h-6 w-6 text-primary" />{" "}
                        Attractions & Activities
                      </h2>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {trip.itinerary.attractions.map((attraction, index) => (
                          <Card
                            key={index}
                            className="group hover:shadow-md transition-all duration-300 border-b-4 border-b-transparent hover:border-b-primary"
                          >
                            <CardHeader>
                              <CardTitle className="text-lg group-hover:text-primary transition-colors">
                                {attraction.name}
                              </CardTitle>
                            </CardHeader>
                            {attraction.description && (
                              <CardContent>
                                <p className="text-sm text-muted-foreground whitespace-pre-line">
                                  {attraction.description}
                                </p>
                              </CardContent>
                            )}
                          </Card>
                        ))}
                      </div>
                    </section>
                  )}

                {/* Tips Section */}
                {trip.itinerary.tips && trip.itinerary.tips.length > 0 && (
                  <section>
                    <h2 className="text-2xl font-semibold mb-6 flex items-center">
                      <Lightbulb className="mr-3 h-6 w-6 text-primary" /> Travel
                      Tips
                    </h2>
                    <Card>
                      <CardContent className="pt-6">
                        <ul className="space-y-2">
                          {trip.itinerary.tips.map((tip, index) => (
                            <li key={index} className="flex items-start">
                              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-primary mr-3 flex-shrink-0">
                                {index + 1}
                              </span>
                              <span className="text-muted-foreground">
                                {tip}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  </section>
                )}
              </div>
            )}
          </TabsContent>

          {/* Guide Tab Content */}
          <TabsContent value="guide" className="space-y-8">
            {trip.destination_agent_response ? (
              <Card className="overflow-hidden">
                <CardHeader className="bg-muted/30">
                  <CardTitle className="flex items-center">
                    <Lightbulb className="h-5 w-5 mr-2 text-primary" />{" "}
                    Destination Guide
                  </CardTitle>
                  <CardDescription>
                    Tourist information and recommendations for{" "}
                    {trip.destination}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-6">
                  <div className="prose prose-sm max-w-none dark:prose-invert prose-headings:font-bold prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg">
                    <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>
                      {trip.destination_agent_response}
                    </ReactMarkdown>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="text-center py-10 border rounded-lg">
                <Info
                  size={48}
                  className="text-muted-foreground mx-auto mb-4"
                />
                <h2 className="text-xl font-semibold mb-2">
                  Destination Guide Not Available
                </h2>
                <p className="text-muted-foreground">
                  Destination guide information is not available for this trip.
                </p>
              </div>
            )}
          </TabsContent>

          {/* Hotels Tab Content */}
          <TabsContent value="hotels" className="space-y-8">
            {trip.itinerary &&
            trip.itinerary.hotels &&
            trip.itinerary.hotels.length > 0 ? (
              <section>
                <h2 className="text-2xl font-semibold mb-6 flex items-center">
                  <Home className="mr-3 h-6 w-6 text-primary" /> Recommended
                  Accommodations
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {trip.itinerary.hotels.map((hotel, index) => (
                    <Card
                      key={index}
                      className="overflow-hidden border-l-4 border-l-primary"
                    >
                      <CardHeader className="bg-muted/30">
                        <div className="flex justify-between items-start">
                          <div>
                            <CardTitle className="text-lg">
                              {hotel.hotel_name}
                            </CardTitle>
                            {hotel.rating && (
                              <CardDescription className="flex items-center mt-1">
                                <span className="text-yellow-500 flex items-center">
                                  {Array(Math.floor(Number(hotel.rating) || 0))
                                    .fill(0)
                                    .map((_, i) => (
                                      <svg
                                        key={i}
                                        xmlns="http://www.w3.org/2000/svg"
                                        viewBox="0 0 24 24"
                                        fill="currentColor"
                                        className="w-4 h-4"
                                      >
                                        <path
                                          fillRule="evenodd"
                                          d="M10.788 3.21c.448-1.077 1.976-1.077 2.424 0l2.082 5.007 5.404.433c1.164.093 1.636 1.545.749 2.305l-4.117 3.527 1.257 5.273c.271 1.136-.964 2.033-1.96 1.425L12 18.354 7.373 21.18c-.996.608-2.231-.29-1.96-1.425l1.257-5.273-4.117-3.527c-.887-.76-.415-2.212.749-2.305l5.404-.433 2.082-5.006z"
                                          clipRule="evenodd"
                                        />
                                      </svg>
                                    ))}
                                </span>
                                <span className="ml-1">{hotel.rating}</span>
                              </CardDescription>
                            )}
                          </div>
                          <Badge variant="outline" className="font-medium">
                            {hotel.price}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="pt-6">
                        <div className="space-y-4">
                          <div className="flex items-start">
                            <MapPin className="h-5 w-5 mr-2 mt-0.5 text-primary flex-shrink-0" />
                            <p className="text-sm text-muted-foreground">
                              {hotel.address}
                            </p>
                          </div>

                          {hotel.description && (
                            <div className="mt-4">
                              <p className="text-sm text-muted-foreground whitespace-pre-line">
                                {hotel.description}
                              </p>
                            </div>
                          )}

                          {hotel.amenities && hotel.amenities.length > 0 && (
                            <div className="mt-4">
                              <h3 className="text-sm font-medium mb-2">
                                Amenities:
                              </h3>
                              <div className="flex flex-wrap gap-1.5">
                                {hotel.amenities.map((amenity, i) => (
                                  <Badge
                                    key={i}
                                    variant="secondary"
                                    className="text-xs"
                                  >
                                    {amenity}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </CardContent>
                      {hotel.url && (
                        <CardFooter className="bg-muted/30 border-t">
                          <a
                            href={hotel.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary hover:underline text-sm flex items-center"
                          >
                            View Hotel / Book{" "}
                            <Globe className="h-4 w-4 ml-1.5" />
                          </a>
                        </CardFooter>
                      )}
                    </Card>
                  ))}
                </div>
              </section>
            ) : (
              <div className="text-center py-10 border rounded-lg">
                <Info
                  size={48}
                  className="text-muted-foreground mx-auto mb-4"
                />
                <h2 className="text-xl font-semibold mb-2">
                  Hotel Information Not Available
                </h2>
                <p className="text-muted-foreground">
                  Hotel recommendations are not available for this trip.
                </p>
              </div>
            )}
          </TabsContent>

          {/* Flights Tab Content */}
          <TabsContent value="flights" className="space-y-8">
            {trip.flight_agent_response ||
            (trip.itinerary &&
              trip.itinerary.flights &&
              trip.itinerary.flights.length > 0) ? (
              <div className="space-y-8">
                {/* Flights from itinerary */}
                {trip.itinerary &&
                  trip.itinerary.flights &&
                  trip.itinerary.flights.length > 0 && (
                    <section>
                      <h2 className="text-2xl font-semibold mb-6 flex items-center">
                        <Plane className="mr-3 h-6 w-6 text-primary" /> Selected
                        Flights
                      </h2>
                      <div className="space-y-6">
                        {trip.itinerary.flights
                          .filter(
                            (flight) =>
                              flight.airline !== "TBD" &&
                              flight.departure_time !== "TBD"
                          )
                          .map((flight, index) => (
                            <Card
                              key={index}
                              className="border-r-4 border-r-primary overflow-hidden"
                            >
                              <CardHeader className="bg-muted/30">
                                <CardTitle className="text-xl flex items-center">
                                  <Plane className="h-5 w-5 mr-2 text-primary" />
                                  {flight.airline}
                                </CardTitle>
                                {flight.flight_number &&
                                  flight.flight_number !== "N/A" &&
                                  flight.flight_number !== "TBD" && (
                                    <CardDescription>
                                      Flight {flight.flight_number}
                                    </CardDescription>
                                  )}
                              </CardHeader>
                              <CardContent className="py-6">
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                                  <div className="bg-muted/20 p-3 rounded-lg">
                                    <p className="font-medium flex items-center">
                                      <Clock className="h-4 w-4 mr-2 text-primary" />
                                      Duration:
                                    </p>
                                    <p className="text-muted-foreground mt-1">
                                      {flight.duration}
                                    </p>
                                  </div>
                                  <div className="bg-muted/20 p-3 rounded-lg">
                                    <p className="font-medium flex items-center">
                                      <DollarSign className="h-4 w-4 mr-2 text-primary" />
                                      Price:
                                    </p>
                                    <p className="text-muted-foreground mt-1">
                                      {flight.price}
                                    </p>
                                  </div>
                                  <div className="bg-muted/20 p-3 rounded-lg">
                                    <p className="font-medium flex items-center">
                                      <Clock className="h-4 w-4 mr-2 text-green-500" />
                                      Departure:
                                    </p>
                                    <p className="text-muted-foreground mt-1">
                                      {flight.departure_time || "Not specified"}
                                    </p>
                                  </div>
                                  <div className="bg-muted/20 p-3 rounded-lg">
                                    <p className="font-medium flex items-center">
                                      <Clock className="h-4 w-4 mr-2 text-red-500" />
                                      Arrival:
                                    </p>
                                    <p className="text-muted-foreground mt-1">
                                      {flight.arrival_time || "Not specified"}
                                    </p>
                                  </div>
                                  {typeof flight.stops !== "undefined" && (
                                    <div className="bg-muted/20 p-3 rounded-lg">
                                      <p className="font-medium">Stops:</p>
                                      <p className="text-muted-foreground mt-1">
                                        {flight.stops}
                                      </p>
                                    </div>
                                  )}
                                </div>
                              </CardContent>
                              {flight.url &&
                                flight.url !== "N/A" &&
                                flight.url !== "TBD" && (
                                  <CardFooter className="bg-muted/30 border-t">
                                    <a
                                      href={flight.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-primary hover:underline text-sm flex items-center"
                                    >
                                      Book / View Flight{" "}
                                      <Globe className="h-4 w-4 ml-1.5" />
                                    </a>
                                  </CardFooter>
                                )}
                            </Card>
                          ))}
                      </div>
                    </section>
                  )}
              </div>
            ) : (
              <div className="text-center py-10 border rounded-lg">
                <Info
                  size={48}
                  className="text-muted-foreground mx-auto mb-4"
                />
                <h2 className="text-xl font-semibold mb-2">
                  Flight Information Not Available
                </h2>
                <p className="text-muted-foreground">
                  Flight information is not available for this trip.
                </p>
              </div>
            )}
          </TabsContent>

          {/* Dining Tab Content */}
          <TabsContent value="dining" className="space-y-8">
            {trip.restaurant_agent_response ||
            (trip.itinerary &&
              trip.itinerary.restaurants &&
              trip.itinerary.restaurants.length > 0) ? (
              <div className="space-y-8">
                {/* Restaurant suggestions from agent */}
                {trip.restaurant_agent_response && (
                  <Card className="overflow-hidden">
                    <CardHeader className="bg-muted/30">
                      <CardTitle className="flex items-center">
                        <Utensils className="h-5 w-5 mr-2 text-primary" />{" "}
                        Restaurant Recommendations
                      </CardTitle>
                      <CardDescription>
                        Dining options for your trip
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="pt-6">
                      <div className="prose prose-sm max-w-none dark:prose-invert prose-headings:font-bold prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm, remarkBreaks]}
                        >
                          {trip.restaurant_agent_response}
                        </ReactMarkdown>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Restaurants from itinerary */}
                {trip.itinerary &&
                  trip.itinerary.restaurants &&
                  trip.itinerary.restaurants.length > 0 && (
                    <section>
                      <h2 className="text-2xl font-semibold mb-6 flex items-center">
                        <Utensils className="mr-3 h-6 w-6 text-primary" />{" "}
                        Selected Restaurants
                      </h2>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {trip.itinerary.restaurants.map((restaurant, index) => (
                          <Card
                            key={index}
                            className="group hover:shadow-md transition-all duration-300 border-b-4 border-b-transparent hover:border-b-primary"
                          >
                            <CardHeader>
                              <CardTitle className="text-lg group-hover:text-primary transition-colors">
                                {restaurant.name}
                              </CardTitle>
                              {restaurant.location && (
                                <CardDescription className="flex items-center mt-1">
                                  <MapPin className="h-3.5 w-3.5 mr-1 text-muted-foreground" />
                                  {restaurant.location}
                                </CardDescription>
                              )}
                            </CardHeader>
                            {restaurant.description && (
                              <CardContent>
                                <p className="text-sm text-muted-foreground whitespace-pre-line">
                                  {restaurant.description}
                                </p>
                              </CardContent>
                            )}
                            {restaurant.url && restaurant.url.trim() !== "" && (
                              <CardFooter className="bg-muted/30 border-t">
                                <a
                                  href={restaurant.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-primary hover:underline text-sm flex items-center"
                                >
                                  Visit Website{" "}
                                  <Globe className="h-4 w-4 ml-1.5" />
                                </a>
                              </CardFooter>
                            )}
                          </Card>
                        ))}
                      </div>
                    </section>
                  )}
              </div>
            ) : (
              <div className="text-center py-10 border rounded-lg">
                <Info
                  size={48}
                  className="text-muted-foreground mx-auto mb-4"
                />
                <h2 className="text-xl font-semibold mb-2">
                  Dining Information Not Available
                </h2>
                <p className="text-muted-foreground">
                  Restaurant recommendations are not available for this trip.
                </p>
              </div>
            )}
          </TabsContent>

          {/* Budget Tab Content */}
          <TabsContent value="budget" className="space-y-8">
            {trip.budget_agent_response ? (
              <Card className="overflow-hidden">
                <CardHeader className="bg-muted/30">
                  <CardTitle className="flex items-center">
                    <Receipt className="h-5 w-5 mr-2 text-primary" /> Budget
                    Analysis
                  </CardTitle>
                  <CardDescription>
                    Budget recommendations and optimization strategies
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-6">
                  <div className="prose prose-sm max-w-none dark:prose-invert prose-headings:font-bold prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg">
                    <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>
                      {trip.budget_agent_response}
                    </ReactMarkdown>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="text-center py-10 border rounded-lg">
                <Info
                  size={48}
                  className="text-muted-foreground mx-auto mb-4"
                />
                <h2 className="text-xl font-semibold mb-2">
                  Budget Information Not Available
                </h2>
                <p className="text-muted-foreground">
                  Budget analysis information is not available for this trip.
                </p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
