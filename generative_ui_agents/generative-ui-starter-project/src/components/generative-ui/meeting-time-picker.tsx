import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Check, X, Clock, ChevronRight } from "lucide-react";

export interface TimeSlot {
  date: string;
  time: string;
  duration?: string;
}

export interface MeetingTimePickerProps {
  status: "inProgress" | "executing" | "complete";
  respond?: (response: string) => void;
  reasonForScheduling?: string;
  meetingDuration?: number;
  title?: string;
  timeSlots?: TimeSlot[];
}

export function MeetingTimePicker({
  status,
  respond,
  reasonForScheduling,
  meetingDuration,
  title = "Schedule a Meeting",
  timeSlots = [
    { date: "Tomorrow", time: "2:00 PM", duration: "30 min" },
    { date: "Friday", time: "10:00 AM", duration: "30 min" },
    { date: "Next Monday", time: "3:00 PM", duration: "30 min" },
  ],
}: MeetingTimePickerProps) {
  const displayTitle = reasonForScheduling || title;
  const slots = meetingDuration
    ? timeSlots.map((slot) => ({ ...slot, duration: `${meetingDuration} min` }))
    : timeSlots;
  const [selectedSlot, setSelectedSlot] = useState<TimeSlot | null>(null);
  const [declined, setDeclined] = useState(false);

  const handleSelectSlot = (slot: TimeSlot) => {
    setSelectedSlot(slot);
    respond?.(
      `Meeting scheduled for ${slot.date} at ${slot.time}${slot.duration ? ` (${slot.duration})` : ""}.`,
    );
  };

  const handleDecline = () => {
    setDeclined(true);
    respond?.(
      "The user declined all proposed meeting times. Please suggest alternative times or ask for their availability.",
    );
  };

  // Confirmed state
  if (selectedSlot) {
    return (
      <Card className="max-w-md w-full mx-auto mb-4 overflow-hidden">
        <CardContent className="p-6">
          <div className="flex flex-col items-center text-center gap-3">
            <div className="flex items-center justify-center h-10 w-10 rounded-full bg-[#189370]">
              <Check className="h-5 w-5 text-white" strokeWidth={3} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-[var(--foreground)]">
                Meeting Scheduled
              </h3>
              <p className="text-sm text-[var(--muted-foreground)] mt-1">
                {selectedSlot.date} at {selectedSlot.time}
              </p>
            </div>
            {selectedSlot.duration && (
              <Badge variant="secondary">
                <Clock className="h-3 w-3 mr-1" />
                {selectedSlot.duration}
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Declined state
  if (declined) {
    return (
      <Card className="max-w-md w-full mx-auto mb-4 overflow-hidden">
        <CardContent className="p-6">
          <div className="flex flex-col items-center text-center gap-3">
            <div className="flex items-center justify-center h-12 w-12 rounded-full bg-[var(--secondary)]">
              <X className="h-6 w-6 text-[var(--muted-foreground)]" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-[var(--foreground)]">
                No Time Selected
              </h3>
              <p className="text-sm text-[var(--muted-foreground)] mt-1">
                Looking for a better time that works for you
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Selection state
  return (
    <Card className="max-w-md w-full mx-auto mb-4 overflow-hidden">
      <CardContent className="p-6">
        <div className="flex flex-col items-center text-center mb-5">
          <div className="flex items-center justify-center h-12 w-12 rounded-full bg-[var(--accent)] mb-3">
            <Clock className="h-6 w-6 text-[#BEC2FF]" />
          </div>
          <h3 className="text-lg font-bold text-[var(--foreground)]">
            {displayTitle}
          </h3>
          <p className="text-sm text-[var(--muted-foreground)] mt-1">
            {status === "inProgress"
              ? "Finding available times..."
              : "Pick a time that works for you"}
          </p>
        </div>

        {status === "inProgress" && (
          <div className="flex justify-center py-6">
            <Spinner size="lg" />
          </div>
        )}

        {status === "executing" && (
          <div className="space-y-3">
            {slots.map((slot, index) => (
              <button
                key={index}
                onClick={() => handleSelectSlot(slot)}
                className="group w-full px-6 py-5 rounded-[var(--radius)]
                  border border-[var(--border)]
                  hover:border-[var(--ring)] hover:bg-[var(--accent)]
                  transition-all duration-150 cursor-pointer
                  flex items-center gap-4"
              >
                <div className="flex-1 text-left">
                  <div className="font-semibold text-base text-[var(--foreground)]">
                    {slot.date}
                  </div>
                  <div className="text-sm text-[var(--muted-foreground)] mt-0.5">
                    {slot.time}
                  </div>
                </div>
                {slot.duration && (
                  <Badge
                    variant="secondary"
                    className="shrink-0 text-sm px-3 py-1"
                  >
                    {slot.duration}
                  </Badge>
                )}
                <ChevronRight className="h-4 w-4 text-[var(--muted-foreground)] opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
              </button>
            ))}

            <Button
              variant="ghost"
              size="sm"
              className="w-full mt-1 text-xs text-[var(--muted-foreground)]"
              onClick={handleDecline}
            >
              None of these work
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
