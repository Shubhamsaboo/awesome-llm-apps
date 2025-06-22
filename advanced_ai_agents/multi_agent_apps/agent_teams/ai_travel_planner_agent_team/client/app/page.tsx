import {
  MapPin,
  Zap,
  Heart,
  Star,
  Plane,
  Calendar,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <h1 className="text-4xl font-bold sm:text-6xl">
            <span className="text-accent">TripCraft AI</span>
          </h1>
          <h2 className="text-2xl font-semibold sm:text-3xl mt-4 text-muted-foreground">
            Your Journey, Perfectly Crafted with Intelligence
          </h2>
          <p className="mt-6 text-lg leading-8 text-secondary-foreground max-w-3xl mx-auto">
            Stop juggling dozens of tabs and conflicting travel info. Our
            AI-powered platform turns your travel dreams into reality—complete
            with flights, hotels, activities, and budget—all from a simple
            conversation about your perfect trip.
          </p>
          <div className="mt-10 flex items-center justify-center gap-x-6">
            <Link href="/plan">
              <Button size="lg" className="bg-primary hover:bg-primary/90">
                <Plane className="w-4 h-4 mr-2" />
                Plan My Trip
              </Button>
            </Link>
            <Button variant="ghost" size="lg">
              See How It Works <span aria-hidden="true">→</span>
            </Button>
          </div>
        </div>

        {/* How It Works Section */}
        <div className="mt-20">
          <h3 className="text-3xl font-bold text-center mb-12">How It Works</h3>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            <div className="text-center">
              <div className="flex items-center justify-center w-16 h-16 bg-primary/10 rounded-full mb-6 mx-auto border-2 border-primary/20">
                <span className="text-2xl font-bold text-primary">1</span>
              </div>
              <h4 className="text-xl font-semibold mb-4">
                Fill Once, Dream Big
              </h4>
              <p className="text-muted-foreground">
                Tell us about your ideal trip—destination, dates, style, budget,
                and preferences. Our thoughtful form captures everything in
                minutes.
              </p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center w-16 h-16 bg-secondary/20 rounded-full mb-6 mx-auto border-2 border-secondary/40">
                <span className="text-2xl font-bold text-foreground">2</span>
              </div>
              <h4 className="text-xl font-semibold mb-4">
                AI Agents Take Over
              </h4>
              <p className="text-muted-foreground">
                Specialized AI agents work together on flights, lodging,
                activities, and budgeting—all happening seamlessly in the
                background.
              </p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center w-16 h-16 bg-accent/10 rounded-full mb-6 mx-auto border-2 border-accent/20">
                <span className="text-2xl font-bold text-accent">3</span>
              </div>
              <h4 className="text-xl font-semibold mb-4">
                Complete Itinerary Ready
              </h4>
              <p className="text-muted-foreground">
                Get a full day-by-day plan with flights, accommodations,
                activities, costs, and booking links—all beautifully organized.
              </p>
            </div>
          </div>
        </div>

        {/* Feature Cards */}
        <div className="mt-20">
          <h3 className="text-3xl font-bold text-center mb-12">
            Why Choose TripCraft AI
          </h3>
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <Card className="hover:shadow-lg transition-shadow border-primary/20 hover:border-primary/40">
              <CardHeader>
                <div className="flex items-center justify-center w-12 h-12 bg-primary/10 rounded-lg mb-4">
                  <Sparkles className="w-6 h-6 text-primary" />
                </div>
                <CardTitle className="text-lg">
                  AI-Powered Intelligence
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Multi-agent AI system that understands your travel style and
                  crafts personalized itineraries that feel like they were made
                  just for you.
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow border-accent/20 hover:border-accent/40">
              <CardHeader>
                <div className="flex items-center justify-center w-12 h-12 bg-accent/10 rounded-lg mb-4">
                  <MapPin className="w-6 h-6 text-accent" />
                </div>
                <CardTitle className="text-lg">Hidden Gems Discovery</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Go beyond tourist traps. We find unique experiences, local
                  events, and offbeat attractions that match your interests
                  perfectly.
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow border-secondary/30 hover:border-secondary/50">
              <CardHeader>
                <div className="flex items-center justify-center w-12 h-12 bg-secondary/20 rounded-lg mb-4">
                  <Zap className="w-6 h-6 text-foreground" />
                </div>
                <CardTitle className="text-lg">Instant Planning</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  No more hours of research and comparison. Get a complete
                  travel plan in moments, with everything balanced perfectly for
                  your needs.
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow border-primary/20 hover:border-primary/40">
              <CardHeader>
                <div className="flex items-center justify-center w-12 h-12 bg-primary/10 rounded-lg mb-4">
                  <Star className="w-6 h-6 text-primary" />
                </div>
                <CardTitle className="text-lg">Smart Memory</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Learns from your preferences over time. Each trip becomes more
                  tailored as our AI remembers what you love.
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow border-accent/20 hover:border-accent/40">
              <CardHeader>
                <div className="flex items-center justify-center w-12 h-12 bg-accent/10 rounded-lg mb-4">
                  <Calendar className="w-6 h-6 text-accent" />
                </div>
                <CardTitle className="text-lg">Complete Coordination</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Flights, hotels, activities, and budget—all coordinated
                  seamlessly. No conflicts, no stress, just a perfect plan ready
                  to execute.
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow border-secondary/30 hover:border-secondary/50">
              <CardHeader>
                <div className="flex items-center justify-center w-12 h-12 bg-secondary/20 rounded-lg mb-4">
                  <Heart className="w-6 h-6 text-foreground" />
                </div>
                <CardTitle className="text-lg">Crafted with Care</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Every detail is thoughtfully considered to create not just a
                  trip, but an experience that feels truly magical and personal.
                </CardDescription>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-20 text-center bg-primary/5 rounded-2xl py-16 px-8 border border-primary/10">
          <h3 className="text-3xl font-bold mb-6">
            Ready to Make Travel Planning Magical?
          </h3>
          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            Stop spending hours planning and start experiencing. Let our AI
            create your perfect journey.
          </p>
          <Button size="lg" className="bg-primary hover:bg-primary/90">
            <Plane className="w-4 h-4 mr-2" />
            Start Planning Now
          </Button>
        </div>
      </main>
    </div>
  );
}
