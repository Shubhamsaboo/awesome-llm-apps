"use client";

import { Check } from "lucide-react";

interface StepIndicatorProps {
  currentStep: number;
}

const steps = [
  { number: 1, name: "Upload" },
  { number: 2, name: "Configure" },
  { number: 3, name: "Optimize" },
  { number: 4, name: "Results" },
];

export default function StepIndicator({ currentStep }: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-center gap-4">
      {steps.map((step, index) => (
        <div key={step.number} className="flex items-center">
          <div className="flex items-center gap-3">
            <div
              className={`
                w-12 h-12 rounded-full flex items-center justify-center font-semibold
                transition-all duration-300
                ${
                  currentStep > step.number
                    ? "gradient-bg text-white"
                    : currentStep === step.number
                    ? "gradient-bg text-white scale-110"
                    : "bg-zinc-800 text-zinc-500"
                }
              `}
            >
              {currentStep > step.number ? (
                <Check className="w-6 h-6" />
              ) : (
                step.number
              )}
            </div>
            <span
              className={`
                text-sm font-medium transition-colors
                ${
                  currentStep >= step.number
                    ? "text-white"
                    : "text-zinc-500"
                }
              `}
            >
              {step.name}
            </span>
          </div>

          {index < steps.length - 1 && (
            <div
              className={`
                w-16 h-0.5 mx-4 transition-colors
                ${
                  currentStep > step.number
                    ? "bg-gradient-to-r from-violet-500 to-purple-500"
                    : "bg-zinc-800"
                }
              `}
            />
          )}
        </div>
      ))}
    </div>
  );
}
