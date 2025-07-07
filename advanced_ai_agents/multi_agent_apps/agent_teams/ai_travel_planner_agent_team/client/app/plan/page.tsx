"use client";

import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { useRouter } from "next/navigation";
import { format } from "date-fns";
import { authClient } from "@/lib/auth-client";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Badge } from "@/components/ui/badge";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
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
  Camera,
  Utensils,
  Mountain,
  Waves,
  Building,
  TreePine,
  Star,
  ChevronRight,
  ChevronLeft,
  Luggage,
  Sparkles,
  Edit3,
  Lightbulb,
  AlertCircle,
  Plus,
  Minus,
} from "lucide-react";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

const travelVibes = [
  { id: "relaxing", label: "Relaxing", icon: Waves },
  { id: "adventure", label: "Adventure", icon: Mountain },
  { id: "romantic", label: "Romantic", icon: Heart },
  { id: "cultural", label: "Cultural", icon: Building },
  { id: "food-focused", label: "Food-focused", icon: Utensils },
  { id: "nature", label: "Nature", icon: TreePine },
  { id: "photography", label: "Photography", icon: Camera },
];

const travelStyles = [
  {
    value: "backpacker",
    label: "Backpacker",
    description: "Budget-conscious, authentic experiences",
  },
  {
    value: "comfort",
    label: "Comfort",
    description: "Balance of comfort and value",
  },
  {
    value: "luxury",
    label: "Luxury",
    description: "Premium experiences and stays",
  },
  {
    value: "eco-conscious",
    label: "Eco-conscious",
    description: "Sustainable and responsible travel",
  },
];

const travelingWithOptions = [
  "Solo",
  "Partner",
  "Friends",
  "Family with kids",
  "Extended family",
  "Colleagues",
];

const ageGroupOptions = ["Under 18", "18-25", "26-35", "36-50", "51-65", "65+"];

// Custom NumberInput component with +/- buttons
const NumberInput = ({
  value,
  onChange,
  min = 0,
  max = 99,
  className = "",
}: {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  className?: string;
}) => {
  const increment = () => {
    if (value < max) {
      onChange(value + 1);
    }
  };

  const decrement = () => {
    if (value > min) {
      onChange(value - 1);
    }
  };

  return (
    <div className={`flex items-center border rounded-md ${className}`}>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="h-12 px-3 rounded-r-none border-r"
        onClick={decrement}
        disabled={value <= min}
      >
        <Minus className="w-4 h-4" />
      </Button>
      <div className="flex-1 h-12 flex items-center justify-center bg-background text-center font-medium text-base min-w-[60px]">
        {value}
      </div>
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="h-12 px-3 rounded-l-none border-l"
        onClick={increment}
        disabled={value >= max}
      >
        <Plus className="w-4 h-4" />
      </Button>
    </div>
  );
};

// Helper function to get default budget for currency
const getDefaultBudgetForCurrency = (currency: string) => {
  switch (currency) {
    case "USD":
      return 1000;
    case "EUR":
      return 900;
    case "GBP":
      return 800;
    case "INR":
      return 75000;
    case "JPY":
      return 120000;
    default:
      return 1000;
  }
};

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

export default function Plan() {
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedVibes, setSelectedVibes] = useState<string[]>([]);
  const [selectedPriorities, setSelectedPriorities] = useState<string[]>([]);
  const [dateInputType, setDateInputType] = useState<"picker" | "text">(
    "picker"
  );
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitMessage, setSubmitMessage] = useState<string | null>(null);
  const router = useRouter();

  // Better Auth session hook
  const {
    data: session,
    isPending: sessionLoading,
    error: sessionError,
  } = authClient.useSession();

  const form = useForm<TripFormData>({
    defaultValues: {
      name: "",
      adults: 1,
      children: 0,
      rooms: 1,
      pace: [3],
      budgetFlexible: false,
      budget: getDefaultBudgetForCurrency("USD"),
      travelingWith: "",
      ageGroups: [],
      vibes: [],
      priorities: [],
      budgetCurrency: "USD",
      dateInputType: "picker",
      travelDates: {
        start: "",
        end: "",
      },
    },
  });

  // Prefill user name when session data is available
  useEffect(() => {
    if (session?.user?.name && !form.getValues("name")) {
      form.setValue("name", session.user.name);
    }
  }, [session, form]);

  // Handle session loading and error states
  if (sessionLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 mx-auto mb-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-muted-foreground">Loading your session...</p>
        </div>
      </div>
    );
  }

  if (sessionError) {
    console.error("Session error:", sessionError);
    // Continue without session data - allow anonymous users
  }

  const onSubmit = async (data: TripFormData) => {
    setIsSubmitting(true);
    setSubmitMessage(null);

    // Debug: Log the data being submitted
    console.log("Form data being submitted:", data);
    console.log("Personal touch data:", {
      beenThereBefore: data.beenThereBefore,
      lovedPlaces: data.lovedPlaces,
      additionalInfo: data.additionalInfo,
    });

    try {
      // Include user ID from session if available
      const submitData = {
        ...data,
        userId: session?.user?.id || null, // Include user ID from Better Auth session
      };

      const response = await fetch("/api/plan/submit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(submitData),
      });

      const result = await response.json();

      if (result.success) {
        setSubmitMessage("🎉 Your trip plan has been submitted successfully!");
        console.log("Trip submitted with ID:", result.tripPlanId);

        // Show success message briefly, then redirect to the plan details page
        setTimeout(() => {
          router.push(`/plan/${result.tripPlanId}`);
        }, 1500);
      } else {
        setSubmitMessage("❌ Failed to submit trip plan. Please try again.");
      }
    } catch (error) {
      console.error("Submission error:", error);
      setSubmitMessage("❌ Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const steps = [
    {
      id: "basics",
      title: "Trip Basics",
      icon: Plane,
      description: "Where and when are you going?",
    },
    {
      id: "group",
      title: "Group Details",
      icon: Users,
      description: "Who's joining the adventure?",
    },
    {
      id: "budget",
      title: "Budget & Style",
      icon: DollarSign,
      description: "What's your travel style?",
    },
    {
      id: "vibe",
      title: "Trip Vibe",
      icon: Heart,
      description: "What experience are you after?",
    },
    {
      id: "accommodation",
      title: "Stay Preferences",
      icon: Home,
      description: "Where will you rest?",
    },
    {
      id: "pace",
      title: "Pace & Style",
      icon: Clock,
      description: "How do you like to travel?",
    },
    {
      id: "personal",
      title: "Personal Touch",
      icon: Globe,
      description: "Tell us more about you",
    },
  ];

  const handleVibeToggle = (vibeId: string) => {
    const newVibes = selectedVibes.includes(vibeId)
      ? selectedVibes.filter((v) => v !== vibeId)
      : [...selectedVibes, vibeId];
    setSelectedVibes(newVibes);
    form.setValue("vibes", newVibes);
    setValidationError(null);
  };

  const handlePriorityToggle = (priority: string) => {
    const newPriorities = selectedPriorities.includes(priority)
      ? selectedPriorities.filter((p) => p !== priority)
      : [...selectedPriorities, priority];
    setSelectedPriorities(newPriorities);
    form.setValue("priorities", newPriorities);
  };

  const nextStep = async (e?: React.MouseEvent) => {
    e?.preventDefault(); // Prevent any form submission
    const isValid = await validateCurrentStep();
    if (isValid && currentStep < steps.length - 1) {
      setValidationError(null);
      setCurrentStep(currentStep + 1);
    }
  };

  const validateCurrentStep = async () => {
    const currentValues = form.getValues();

    try {
      switch (currentStep) {
        case 0: // Trip Basics
          if (
            !currentValues.name ||
            !currentValues.destination ||
            !currentValues.startingLocation ||
            !currentValues.travelDates?.start ||
            !currentValues.duration
          ) {
            setValidationError(
              "Please fill in all required fields to continue"
            );
            form.trigger([
              "name",
              "destination",
              "startingLocation",
              "travelDates.start",
              "duration",
            ]);
            return false;
          }
          break;
        case 1: // Group Details
          if (
            !currentValues.travelingWith ||
            !currentValues.adults ||
            !currentValues.ageGroups?.length
          ) {
            setValidationError(
              "Please select who you're traveling with, number of adults, and age groups"
            );
            form.trigger(["travelingWith", "adults", "ageGroups"]);
            return false;
          }
          break;
        case 2: // Budget & Style
          if (!currentValues.budget || !currentValues.travelStyle) {
            setValidationError(
              "Please enter your budget and select a travel style"
            );
            form.trigger(["budget", "travelStyle"]);
            return false;
          }
          break;
        case 3: // Trip Vibe
          if (!currentValues.vibes?.length) {
            setValidationError("Please select at least one trip vibe");
            return false;
          }
          break;
        case 4: // Accommodation
          if (!currentValues.rooms) {
            setValidationError("Please specify the number of rooms needed");
            form.trigger(["rooms"]);
            return false;
          }
          break;
        case 5: // Pace & Style
          if (!currentValues.pace?.length) {
            setValidationError("Please set your preferred activity pace");
            form.trigger(["pace"]);
            return false;
          }
          break;
        case 6: // Personal Touch - all fields are optional
          // No validation needed as all fields are optional
          return true;
        default:
          return true;
      }
      return true;
    } catch {
      return false;
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  return (
    <div className="min-h-screen bg-background py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-4 flex items-center justify-center gap-3">
            <Luggage className="w-8 h-8 text-primary" />
            Plan Your Perfect Trip
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Tell us about your dream destination and we&apos;ll craft the
            perfect itinerary just for you
          </p>
        </div>

        {/* Progress Indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            {steps.map((step, index) => {
              const StepIcon = step.icon;
              return (
                <div key={step.id} className="flex flex-col items-center">
                  <div
                    className={`w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${
                      index <= currentStep
                        ? "bg-primary border-primary text-primary-foreground"
                        : "bg-background border-border text-muted-foreground"
                    }`}
                  >
                    <StepIcon className="w-5 h-5" />
                  </div>
                  <span
                    className={`text-xs mt-2 font-medium ${
                      index <= currentStep
                        ? "text-primary"
                        : "text-muted-foreground"
                    }`}
                  >
                    {step.title}
                  </span>
                </div>
              );
            })}
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full transition-all duration-500"
              style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Validation Error */}
        {validationError && (
          <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-destructive" />
            <span className="text-destructive font-medium">
              {validationError}
            </span>
          </div>
        )}

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <Card className="shadow-lg border">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-3 text-2xl">
                  {React.createElement(steps[currentStep].icon, {
                    className: "w-6 h-6 text-primary",
                  })}
                  {steps[currentStep].title}
                </CardTitle>
                <CardDescription className="text-base">
                  {steps[currentStep].description}
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-6">
                {/* Step 0: Trip Basics */}
                {currentStep === 0 && (
                  <div className="space-y-6">
                    <FormField
                      control={form.control}
                      name="name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-base font-semibold flex items-center gap-2">
                            <Sparkles className="w-4 h-4 text-primary" />
                            What&apos;s your name?
                            {session?.user?.name && (
                              <Badge variant="secondary" className="text-xs">
                                Prefilled from account
                              </Badge>
                            )}
                          </FormLabel>
                          <FormControl>
                            <Input
                              placeholder="Your name"
                              {...field}
                              className="h-12 text-base"
                            />
                          </FormControl>
                          <FormDescription>
                            {session?.user?.name ? (
                              <span className="text-green-600 flex items-center gap-1">
                                <Sparkles className="w-3 h-3" />
                                Welcome back, {session.user.name}! Your name has
                                been prefilled.
                              </span>
                            ) : (
                              "Enter your name to personalize your trip plan"
                            )}
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <div className="grid md:grid-cols-2 gap-6">
                      <FormField
                        control={form.control}
                        name="destination"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel className="text-base font-semibold flex items-center gap-2">
                              <MapPin className="w-4 h-4" />
                              Where are you going?
                            </FormLabel>
                            <FormControl>
                              <Input
                                placeholder="e.g., Paris, Bali, Tokyo"
                                {...field}
                                className="h-12 text-base"
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="startingLocation"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel className="text-base font-semibold flex items-center gap-2">
                              <Plane className="w-4 h-4" />
                              Where are you starting from?
                            </FormLabel>
                            <FormControl>
                              <Input
                                placeholder="e.g., New York City, Delhi"
                                {...field}
                                className="h-12 text-base"
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>

                    {/* Travel Dates Section */}
                    <div className="space-y-4">
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                        <FormLabel className="text-base font-semibold flex items-center gap-2">
                          <CalendarIcon className="w-4 h-4 text-primary" />
                          When are you traveling?
                        </FormLabel>
                        <div className="inline-flex items-center bg-muted rounded-lg p-1 w-fit">
                          <button
                            type="button"
                            className={`inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-all whitespace-nowrap ${
                              dateInputType === "picker"
                                ? "bg-background text-primary shadow-sm border border-border"
                                : "text-muted-foreground hover:text-foreground"
                            }`}
                            onClick={() => {
                              setDateInputType("picker");
                              form.setValue("dateInputType", "picker");
                              if (dateInputType === "text") {
                                form.setValue("travelDates.start", "");
                                form.setValue("travelDates.end", "");
                              }
                            }}
                          >
                            <CalendarIcon className="w-3 h-3 mr-1.5" />
                            Date Picker
                          </button>
                          <button
                            type="button"
                            className={`inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-all whitespace-nowrap ${
                              dateInputType === "text"
                                ? "bg-background text-primary shadow-sm border border-border"
                                : "text-muted-foreground hover:text-foreground"
                            }`}
                            onClick={() => {
                              setDateInputType("text");
                              form.setValue("dateInputType", "text");
                              if (dateInputType === "picker") {
                                form.setValue("travelDates.start", "");
                                form.setValue("travelDates.end", "");
                              }
                            }}
                          >
                            <Edit3 className="w-3 h-3 mr-1.5" />
                            Flexible
                          </button>
                        </div>
                      </div>

                      {dateInputType === "picker" ? (
                        <div className="grid md:grid-cols-2 gap-4">
                          <FormField
                            control={form.control}
                            name="travelDates.start"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel className="text-sm font-medium">
                                  Start Date
                                </FormLabel>
                                <FormControl>
                                  <Popover>
                                    <PopoverTrigger asChild>
                                      <Button
                                        variant={"outline"}
                                        className={cn(
                                          "w-full justify-start text-left font-normal h-12",
                                          !field.value &&
                                            "text-muted-foreground"
                                        )}
                                      >
                                        <CalendarIcon className="mr-2 h-4 w-4" />
                                        {field.value ? (
                                          format(new Date(field.value), "PPP")
                                        ) : (
                                          <span>Pick start date</span>
                                        )}
                                      </Button>
                                    </PopoverTrigger>
                                    <PopoverContent
                                      className="w-auto p-0"
                                      align="start"
                                    >
                                      <Calendar
                                        mode="single"
                                        selected={
                                          field.value
                                            ? new Date(field.value)
                                            : undefined
                                        }
                                        onSelect={(date) => {
                                          if (date) {
                                            field.onChange(date.toISOString());
                                          } else {
                                            field.onChange("");
                                          }
                                        }}
                                        initialFocus
                                      />
                                    </PopoverContent>
                                  </Popover>
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          <FormField
                            control={form.control}
                            name="travelDates.end"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel className="text-sm font-medium">
                                  End Date
                                </FormLabel>
                                <FormControl>
                                  <Popover>
                                    <PopoverTrigger asChild>
                                      <Button
                                        variant={"outline"}
                                        className={cn(
                                          "w-full justify-start text-left font-normal h-12",
                                          !field.value &&
                                            "text-muted-foreground"
                                        )}
                                      >
                                        <CalendarIcon className="mr-2 h-4 w-4" />
                                        {field.value ? (
                                          format(new Date(field.value), "PPP")
                                        ) : (
                                          <span>Pick end date</span>
                                        )}
                                      </Button>
                                    </PopoverTrigger>
                                    <PopoverContent
                                      className="w-auto p-0"
                                      align="start"
                                    >
                                      <Calendar
                                        mode="single"
                                        selected={
                                          field.value
                                            ? new Date(field.value)
                                            : undefined
                                        }
                                        onSelect={(date) => {
                                          if (date) {
                                            field.onChange(date.toISOString());
                                          } else {
                                            field.onChange("");
                                          }
                                        }}
                                        disabled={(date) => {
                                          const startDate =
                                            form.getValues("travelDates.start");
                                          return startDate
                                            ? date < new Date(startDate)
                                            : false;
                                        }}
                                        initialFocus
                                      />
                                    </PopoverContent>
                                  </Popover>
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </div>
                      ) : (
                        <div className="space-y-4">
                          <FormField
                            control={form.control}
                            name="travelDates.start"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel className="text-sm font-medium">
                                  Travel Dates
                                </FormLabel>
                                <FormControl>
                                  <Input
                                    placeholder="e.g., July 10 – July 17, August 2025 (flexible), Summer 2025"
                                    {...field}
                                    className="h-12 text-base"
                                  />
                                </FormControl>
                                <FormDescription className="text-xs text-muted-foreground">
                                  <Sparkles className="w-3 h-3 inline mr-1" />
                                  You can enter flexible dates like &quot;August
                                  2025&quot;, &quot;Summer 2025
                                  (flexible)&quot;, or &quot;Early
                                  December&quot;
                                </FormDescription>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          <FormField
                            control={form.control}
                            name="travelDates.end"
                            render={({ field }) => (
                              <FormItem className="hidden">
                                <FormControl>
                                  <Input
                                    {...field}
                                    value={field.value || ""}
                                    className="hidden"
                                  />
                                </FormControl>
                              </FormItem>
                            )}
                          />
                        </div>
                      )}
                    </div>

                    <FormField
                      control={form.control}
                      name="duration"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-base font-semibold">
                            How many days?
                          </FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              placeholder="5"
                              {...field}
                              onChange={(e) =>
                                field.onChange(Number(e.target.value))
                              }
                              className="h-12 text-base"
                            />
                          </FormControl>
                          <FormDescription className="text-sm text-muted-foreground">
                            <Lightbulb className="w-3 h-3 inline mr-1" />
                            Approximate number of days (leave empty if flexible)
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                )}

                {/* Step 1: Group Details */}
                {currentStep === 1 && (
                  <div className="space-y-6">
                    <FormField
                      control={form.control}
                      name="travelingWith"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-base font-semibold">
                            Who are you traveling with?
                          </FormLabel>
                          <RadioGroup
                            onValueChange={field.onChange}
                            defaultValue={field.value}
                            className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-2"
                          >
                            {travelingWithOptions.map((option) => (
                              <div
                                key={option}
                                className="flex items-center space-x-2"
                              >
                                <RadioGroupItem value={option} id={option} />
                                <Label
                                  htmlFor={option}
                                  className="text-sm font-medium cursor-pointer"
                                >
                                  {option}
                                </Label>
                              </div>
                            ))}
                          </RadioGroup>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <div className="grid md:grid-cols-2 gap-6">
                      <FormField
                        control={form.control}
                        name="adults"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel className="text-base font-semibold">
                              Number of adults
                            </FormLabel>
                            <FormControl>
                              <NumberInput
                                value={field.value}
                                onChange={field.onChange}
                                min={1}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="children"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel className="text-base font-semibold">
                              Number of children
                            </FormLabel>
                            <FormControl>
                              <NumberInput
                                value={field.value}
                                onChange={field.onChange}
                                min={1}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>

                    <FormField
                      control={form.control}
                      name="ageGroups"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-base font-semibold">
                            Age groups of travelers
                          </FormLabel>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {ageGroupOptions.map((ageGroup) => (
                              <Badge
                                key={ageGroup}
                                variant={
                                  field.value?.includes(ageGroup)
                                    ? "default"
                                    : "outline"
                                }
                                className="cursor-pointer px-4 py-2 hover:bg-primary/10"
                                onClick={() => {
                                  const value = field.value || [];
                                  if (value.includes(ageGroup)) {
                                    field.onChange(
                                      value.filter(
                                        (v: string) => v !== ageGroup
                                      )
                                    );
                                  } else {
                                    field.onChange([...value, ageGroup]);
                                  }
                                }}
                              >
                                {ageGroup}
                              </Badge>
                            ))}
                          </div>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                )}

                {/* Step 2: Budget & Style */}
                {currentStep === 2 && (
                  <div className="space-y-6">
                    <div className="grid md:grid-cols-3 gap-4">
                      <div className="md:col-span-2">
                        <FormField
                          control={form.control}
                          name="budget"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel className="text-base font-semibold">
                                Budget per person
                              </FormLabel>
                              <FormControl>
                                <div className="px-4 py-6">
                                  <div className="mb-4 text-center">
                                    <span className="text-2xl font-bold text-primary">
                                      {form.watch("budgetCurrency") === "USD" &&
                                        "$"}
                                      {form.watch("budgetCurrency") === "EUR" &&
                                        "€"}
                                      {form.watch("budgetCurrency") === "GBP" &&
                                        "£"}
                                      {form.watch("budgetCurrency") === "INR" &&
                                        "₹"}
                                      {form.watch("budgetCurrency") === "JPY" &&
                                        "¥"}
                                      {field.value.toLocaleString()}
                                    </span>
                                  </div>
                                  <Slider
                                    min={
                                      form.watch("budgetCurrency") === "USD"
                                        ? 100
                                        : form.watch("budgetCurrency") === "EUR"
                                        ? 100
                                        : form.watch("budgetCurrency") === "GBP"
                                        ? 100
                                        : form.watch("budgetCurrency") === "INR"
                                        ? 5000
                                        : form.watch("budgetCurrency") === "JPY"
                                        ? 10000
                                        : 100
                                    }
                                    max={
                                      form.watch("budgetCurrency") === "USD"
                                        ? 10000
                                        : form.watch("budgetCurrency") === "EUR"
                                        ? 9000
                                        : form.watch("budgetCurrency") === "GBP"
                                        ? 8000
                                        : form.watch("budgetCurrency") === "INR"
                                        ? 500000
                                        : form.watch("budgetCurrency") === "JPY"
                                        ? 1000000
                                        : 10000
                                    }
                                    step={
                                      form.watch("budgetCurrency") === "USD"
                                        ? 100
                                        : form.watch("budgetCurrency") === "EUR"
                                        ? 100
                                        : form.watch("budgetCurrency") === "GBP"
                                        ? 100
                                        : form.watch("budgetCurrency") === "INR"
                                        ? 5000
                                        : form.watch("budgetCurrency") === "JPY"
                                        ? 10000
                                        : 100
                                    }
                                    value={[field.value]}
                                    onValueChange={(values) =>
                                      field.onChange(values[0])
                                    }
                                    className="w-full"
                                  />
                                  <div className="flex justify-between text-sm text-muted-foreground mt-2">
                                    {form.watch("budgetCurrency") === "USD" && (
                                      <>
                                        <span>$100</span>
                                        <span>$5,000</span>
                                        <span>$10,000+</span>
                                      </>
                                    )}
                                    {form.watch("budgetCurrency") === "EUR" && (
                                      <>
                                        <span>€100</span>
                                        <span>€4,500</span>
                                        <span>€9,000+</span>
                                      </>
                                    )}
                                    {form.watch("budgetCurrency") === "GBP" && (
                                      <>
                                        <span>£100</span>
                                        <span>£4,000</span>
                                        <span>£8,000+</span>
                                      </>
                                    )}
                                    {form.watch("budgetCurrency") === "INR" && (
                                      <>
                                        <span>₹5,000</span>
                                        <span>₹250,000</span>
                                        <span>₹500,000+</span>
                                      </>
                                    )}
                                    {form.watch("budgetCurrency") === "JPY" && (
                                      <>
                                        <span>¥10,000</span>
                                        <span>¥500,000</span>
                                        <span>¥1,000,000+</span>
                                      </>
                                    )}
                                  </div>
                                </div>
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </div>
                      <FormField
                        control={form.control}
                        name="budgetCurrency"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel className="text-base font-semibold">
                              Currency
                            </FormLabel>
                            <Select
                              onValueChange={(value) => {
                                field.onChange(value);
                                // Update budget to appropriate default for new currency
                                form.setValue(
                                  "budget",
                                  getDefaultBudgetForCurrency(value)
                                );
                              }}
                              defaultValue={field.value}
                            >
                              <FormControl>
                                <SelectTrigger className="h-12">
                                  <SelectValue placeholder="USD" />
                                </SelectTrigger>
                              </FormControl>
                              <SelectContent>
                                <SelectItem value="USD">USD ($)</SelectItem>
                                <SelectItem value="EUR">EUR (€)</SelectItem>
                                <SelectItem value="GBP">GBP (£)</SelectItem>
                                <SelectItem value="INR">INR (₹)</SelectItem>
                                <SelectItem value="JPY">JPY (¥)</SelectItem>
                              </SelectContent>
                            </Select>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>

                    <FormField
                      control={form.control}
                      name="travelStyle"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-base font-semibold">
                            Preferred travel style
                          </FormLabel>
                          <RadioGroup
                            onValueChange={field.onChange}
                            defaultValue={field.value}
                            className="grid md:grid-cols-2 gap-4 mt-2"
                          >
                            {travelStyles.map((style) => (
                              <div
                                key={style.value}
                                className="flex items-center space-x-2"
                              >
                                <RadioGroupItem
                                  value={style.value}
                                  id={style.value}
                                />
                                <div className="grid gap-1">
                                  <Label
                                    htmlFor={style.value}
                                    className="font-medium"
                                  >
                                    {style.label}
                                  </Label>
                                  <p className="text-sm text-muted-foreground">
                                    {style.description}
                                  </p>
                                </div>
                              </div>
                            ))}
                          </RadioGroup>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="budgetFlexible"
                      render={({ field }) => (
                        <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                          <div className="space-y-0.5">
                            <FormLabel className="text-base font-semibold">
                              Budget flexibility
                            </FormLabel>
                            <FormDescription>
                              Can you go a bit over budget for amazing
                              experiences?
                            </FormDescription>
                          </div>
                          <FormControl>
                            <Checkbox
                              checked={field.value}
                              onCheckedChange={field.onChange}
                            />
                          </FormControl>
                        </FormItem>
                      )}
                    />
                  </div>
                )}

                {/* Step 3: Trip Vibe */}
                {currentStep === 3 && (
                  <div className="space-y-6">
                    <FormField
                      control={form.control}
                      name="vibes"
                      render={() => (
                        <FormItem>
                          <FormLabel className="text-base font-semibold">
                            What kind of vibe are you looking for?
                          </FormLabel>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">
                            {travelVibes.map((vibe) => {
                              const VibeIcon = vibe.icon;
                              const isSelected = selectedVibes.includes(
                                vibe.id
                              );
                              return (
                                <div
                                  key={vibe.id}
                                  onClick={() => handleVibeToggle(vibe.id)}
                                  className={`p-4 rounded-xl border-2 cursor-pointer transition-all hover:shadow-lg ${
                                    isSelected
                                      ? "border-primary bg-primary/5 shadow-md"
                                      : "border-border hover:border-primary/50"
                                  }`}
                                >
                                  <div className="text-center">
                                    <VibeIcon
                                      className={`w-8 h-8 mx-auto mb-2 ${
                                        isSelected
                                          ? "text-primary"
                                          : "text-muted-foreground"
                                      }`}
                                    />
                                    <span
                                      className={`font-medium ${
                                        isSelected
                                          ? "text-primary"
                                          : "text-foreground"
                                      }`}
                                    >
                                      {vibe.label}
                                    </span>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="priorities"
                      render={() => (
                        <FormItem>
                          <FormLabel className="text-base font-semibold">
                            Trip priorities (optional)
                          </FormLabel>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {[
                              "Comfort",
                              "Budget-friendly",
                              "Unique stays",
                              "Local experiences",
                              "Instagram-worthy spots",
                              "Safety",
                            ].map((priority) => (
                              <Badge
                                key={priority}
                                variant={
                                  selectedPriorities.includes(priority)
                                    ? "default"
                                    : "outline"
                                }
                                className="cursor-pointer px-4 py-2 hover:bg-primary/10"
                                onClick={() => handlePriorityToggle(priority)}
                              >
                                {priority}
                              </Badge>
                            ))}
                          </div>
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="interests"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-base font-semibold">
                            Any specific interests or things to avoid?
                          </FormLabel>
                          <FormControl>
                            <Textarea
                              placeholder="e.g., Love street food, avoid crowded places, interested in local art..."
                              {...field}
                              className="min-h-[100px] text-base"
                            />
                          </FormControl>
                          <FormDescription>
                            Help us personalize your trip
                          </FormDescription>
                        </FormItem>
                      )}
                    />
                  </div>
                )}

                {/* Step 4: Accommodation */}
                {currentStep === 4 && (
                  <div className="space-y-6">
                    <FormField
                      control={form.control}
                      name="rooms"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-base font-semibold">
                            How many rooms do you need?
                          </FormLabel>
                          <FormControl>
                            <NumberInput
                              value={field.value}
                              onChange={field.onChange}
                              min={1}
                            />
                          </FormControl>
                          <FormDescription>
                            This helps us suggest the right accommodations
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                )}

                {/* Step 5: Pace & Style */}
                {currentStep === 5 && (
                  <div className="space-y-6">
                    <FormField
                      control={form.control}
                      name="pace"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-base font-semibold">
                            How packed should your days be?
                          </FormLabel>
                          <FormControl>
                            <div className="px-4 py-6">
                              <Slider
                                min={1}
                                max={5}
                                step={1}
                                value={field.value}
                                onValueChange={field.onChange}
                                className="w-full"
                              />
                              <div className="flex justify-between text-sm text-muted-foreground mt-2">
                                <span>Very relaxed</span>
                                <span>Balanced</span>
                                <span>Action-packed</span>
                              </div>
                            </div>
                          </FormControl>
                          <FormDescription>
                            Current setting:{" "}
                            {field.value?.[0] === 1
                              ? "Very relaxed"
                              : field.value?.[0] === 2
                              ? "Mostly relaxed"
                              : field.value?.[0] === 3
                              ? "Balanced"
                              : field.value?.[0] === 4
                              ? "Quite busy"
                              : "Action-packed"}
                          </FormDescription>
                        </FormItem>
                      )}
                    />
                  </div>
                )}

                {/* Step 6: Personal Touch */}
                {currentStep === 6 && (
                  <div className="space-y-6">
                    <FormField
                      control={form.control}
                      name="beenThereBefore"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-base font-semibold">
                            Have you been to this destination before?
                          </FormLabel>
                          <RadioGroup
                            onValueChange={field.onChange}
                            defaultValue={field.value}
                            className="flex gap-6 mt-2"
                          >
                            <div className="flex items-center space-x-2">
                              <RadioGroupItem value="no" id="no" />
                              <Label htmlFor="no">No, first time!</Label>
                            </div>
                            <div className="flex items-center space-x-2">
                              <RadioGroupItem value="yes" id="yes" />
                              <Label htmlFor="yes">Yes, been before</Label>
                            </div>
                          </RadioGroup>
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="lovedPlaces"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-base font-semibold">
                            Any places you&apos;ve loved in the past?
                          </FormLabel>
                          <FormControl>
                            <Textarea
                              placeholder="e.g., Loved the temples in Kyoto, enjoyed the beaches in Goa..."
                              {...field}
                              className="min-h-[80px] text-base"
                            />
                          </FormControl>
                          <FormDescription>
                            This helps us understand your travel style
                          </FormDescription>
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="additionalInfo"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-base font-semibold">
                            Anything else you&apos;d like us to know?
                          </FormLabel>
                          <FormControl>
                            <Textarea
                              placeholder="e.g., This is our honeymoon, we're vegetarian, love hidden gems..."
                              {...field}
                              className="min-h-[100px] text-base"
                            />
                          </FormControl>
                          <FormDescription>
                            Share any special requirements, dietary
                            restrictions, or preferences
                          </FormDescription>
                        </FormItem>
                      )}
                    />
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Submission Message */}
            {submitMessage && (
              <div
                className={`p-4 rounded-lg border text-center font-medium ${
                  submitMessage.includes("🎉")
                    ? "bg-green-50 border-green-200 text-green-800"
                    : "bg-red-50 border-red-200 text-red-800"
                }`}
              >
                {submitMessage}
              </div>
            )}

            {/* Navigation */}
            <div className="flex justify-between items-center">
              <Button
                type="button"
                variant="outline"
                onClick={prevStep}
                disabled={currentStep === 0 || isSubmitting}
                className="h-12 px-6"
              >
                <ChevronLeft className="w-4 h-4 mr-2" />
                Previous
              </Button>

              <span className="text-sm text-muted-foreground">
                Step {currentStep + 1} of {steps.length}
              </span>

              {currentStep === steps.length - 1 ? (
                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="h-12 px-8"
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-4 h-4 mr-2 animate-spin rounded-full border-2 border-background border-t-transparent" />
                      Creating Trip...
                    </>
                  ) : (
                    <>
                      <Star className="w-4 h-4 mr-2" />
                      Create My Trip
                    </>
                  )}
                </Button>
              ) : (
                <Button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    nextStep(e);
                  }}
                  disabled={isSubmitting}
                  className="h-12 px-6"
                >
                  Next
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              )}
            </div>
          </form>
        </Form>
      </div>
    </div>
  );
}
