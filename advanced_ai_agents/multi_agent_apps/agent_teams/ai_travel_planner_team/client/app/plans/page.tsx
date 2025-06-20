"use client";

import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  MapPin,
  Calendar as CalendarIcon,
  Users,
  DollarSign,
  Heart,
  Home,
  Clock,
  Globe,
  Plane,
  Luggage,
  Plus,
  RefreshCw,
  AlertCircle,
  Trash2,
  Eye,
} from "lucide-react";
import { format } from "date-fns";
import Link from "next/link";
import { toast } from "sonner";

interface TripPlan {
  id: string;
  name: string;
  destination: string;
  startingLocation: string;
  travelDatesStart: string;
  travelDatesEnd?: string;
  dateInputType: string;
  duration?: number;
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
  createdAt: string;
  updatedAt: string;
  userId?: string;
}

const formatCurrency = (amount: number, currency: string) => {
  const symbols: Record<string, string> = {
    USD: "$",
    EUR: "€",
    GBP: "£",
    INR: "₹",
    JPY: "¥",
  };
  return `${symbols[currency] || "$"}${amount.toLocaleString()}`;
};

const formatDate = (dateString: string, inputType: string) => {
  if (inputType === "text" || !dateString) {
    return dateString || "Flexible dates";
  }
  try {
    return format(new Date(dateString), "MMM dd, yyyy");
  } catch {
    return dateString;
  }
};

const getPaceDescription = (pace: number[]) => {
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

export default function Plans() {
  const [tripPlans, setTripPlans] = useState<TripPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingPlanId, setDeletingPlanId] = useState<string | null>(null);

  const fetchTripPlans = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch("/api/plans");
      const data = await response.json();

      if (data.success) {
        setTripPlans(data.tripPlans);
      } else {
        setError(data.message || "Failed to fetch trip plans");
      }
    } catch (err) {
      console.error("Error fetching trip plans:", err);
      setError("Failed to fetch trip plans");
    } finally {
      setLoading(false);
    }
  };

  const deleteTripPlan = async (planId: string) => {
    try {
      setDeletingPlanId(planId);
      const response = await fetch(`/api/plans/${planId}`, {
        method: "DELETE",
      });
      const data = await response.json();

      if (data.success) {
        // Remove the plan from the local state
        setTripPlans(tripPlans.filter((plan) => plan.id !== planId));
        toast.success("Trip plan deleted successfully");
      } else {
        toast.error(data.message || "Failed to delete trip plan");
      }
    } catch (err) {
      console.error("Error deleting trip plan:", err);
      toast.error("Failed to delete trip plan");
    } finally {
      setDeletingPlanId(null);
    }
  };

  const handleDeletePlan = (planId: string) => {
    if (
      window.confirm(
        "Are you sure you want to delete this trip plan? This action cannot be undone."
      )
    ) {
      deleteTripPlan(planId);
    }
  };

  useEffect(() => {
    fetchTripPlans();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-background py-8 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 animate-spin text-primary mx-auto mb-4" />
            <p className="text-muted-foreground">Loading your trip plans...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background py-8 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center">
            <AlertCircle className="w-8 h-8 text-destructive mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Error Loading Plans</h2>
            <p className="text-muted-foreground mb-4">{error}</p>
            <Button onClick={fetchTripPlans} variant="outline">
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-4 flex items-center justify-center gap-3">
            <Luggage className="w-8 h-8 text-primary" />
            Your Trip Plans
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Manage and review all your planned adventures
          </p>
        </div>

        {/* Action Bar */}
        <div className="flex justify-between items-center mb-8">
          <div className="text-sm text-muted-foreground">
            {tripPlans.length} {tripPlans.length === 1 ? "plan" : "plans"} found
          </div>
          <div className="flex gap-3">
            <Button onClick={fetchTripPlans} variant="outline" size="sm">
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
            <Link href="/plan">
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                New Trip Plan
              </Button>
            </Link>
          </div>
        </div>

        {/* Trip Plans Grid */}
        {tripPlans.length === 0 ? (
          <div className="text-center py-16">
            <Globe className="w-16 h-16 text-muted-foreground/50 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">No trip plans yet</h3>
            <p className="text-muted-foreground mb-6">
              Start planning your next adventure!
            </p>
            <Link href="/plan">
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Trip Plan
              </Button>
            </Link>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {tripPlans.map((plan) => (
              <Card
                key={plan.id}
                className="shadow-lg border hover:shadow-xl transition-shadow"
              >
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-xl">
                    <MapPin className="w-5 h-5 text-primary" />
                    {plan.destination}
                  </CardTitle>
                  <CardDescription className="text-base font-medium">
                    {plan.name}
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Travel Details */}
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm">
                      <Plane className="w-4 h-4 text-muted-foreground" />
                      <span>From {plan.startingLocation}</span>
                    </div>

                    <div className="flex items-center gap-2 text-sm">
                      <CalendarIcon className="w-4 h-4 text-muted-foreground" />
                      <span>
                        {formatDate(plan.travelDatesStart, plan.dateInputType)}
                        {plan.travelDatesEnd &&
                          plan.dateInputType === "picker" && (
                            <>
                              {" - "}
                              {formatDate(
                                plan.travelDatesEnd,
                                plan.dateInputType
                              )}
                            </>
                          )}
                      </span>
                    </div>

                    {plan.duration && (
                      <div className="flex items-center gap-2 text-sm">
                        <Clock className="w-4 h-4 text-muted-foreground" />
                        <span>{plan.duration} days</span>
                      </div>
                    )}

                    <div className="flex items-center gap-2 text-sm">
                      <Users className="w-4 h-4 text-muted-foreground" />
                      <span>
                        {plan.adults} adult{plan.adults > 1 ? "s" : ""}
                        {plan.children > 0 &&
                          `, ${plan.children} child${
                            plan.children > 1 ? "ren" : ""
                          }`}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-sm">
                      <DollarSign className="w-4 h-4 text-muted-foreground" />
                      <span>
                        {formatCurrency(plan.budget, plan.budgetCurrency)} per
                        person
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-sm">
                      <Home className="w-4 h-4 text-muted-foreground" />
                      <span>
                        {plan.rooms} room{plan.rooms > 1 ? "s" : ""},{" "}
                        {plan.travelStyle}
                      </span>
                    </div>
                  </div>

                  {/* Vibes */}
                  {plan.vibes.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                        <Heart className="w-4 h-4" />
                        Trip Vibes
                      </h4>
                      <div className="flex flex-wrap gap-1">
                        {plan.vibes.slice(0, 3).map((vibe) => (
                          <Badge
                            key={vibe}
                            variant="secondary"
                            className="text-xs"
                          >
                            {vibe}
                          </Badge>
                        ))}
                        {plan.vibes.length > 3 && (
                          <Badge variant="outline" className="text-xs">
                            +{plan.vibes.length - 3} more
                          </Badge>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Pace */}
                  <div className="text-sm text-muted-foreground">
                    <span className="font-medium">Pace:</span>{" "}
                    {getPaceDescription(plan.pace)}
                  </div>

                  {/* Created Date */}
                  <div className="text-xs text-muted-foreground pt-2 border-t">
                    Created{" "}
                    {format(
                      new Date(plan.createdAt),
                      "MMM dd, yyyy 'at' h:mm a"
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 pt-2">
                    <Link href={`/plan/${plan.id}`} className="flex-1">
                      <Button variant="outline" size="sm" className="w-full">
                        <Eye className="w-4 h-4 mr-2" />
                        View Details
                      </Button>
                    </Link>
                    <Button
                      variant="destructive"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleDeletePlan(plan.id)}
                      disabled={deletingPlanId === plan.id}
                    >
                      {deletingPlanId === plan.id ? (
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <Trash2 className="w-4 h-4 mr-2" />
                      )}
                      Delete
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
