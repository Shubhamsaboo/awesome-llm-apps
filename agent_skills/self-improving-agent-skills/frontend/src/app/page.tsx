"use client";

import { useState } from "react";
import StepIndicator from "@/components/StepIndicator";
import UploadStep from "@/components/UploadStep";
import ConfigStep from "@/components/ConfigStep";
import RunningStep from "@/components/RunningStep";
import ResultsStep from "@/components/ResultsStep";

export default function Home() {
  const [currentStep, setCurrentStep] = useState(1);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [metadata, setMetadata] = useState<any>(null);
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [evals, setEvals] = useState<any[]>([]);
  const [finalResult, setFinalResult] = useState<any>(null);

  const handleUploadComplete = (
    sid: string,
    key: string,
    meta: any,
    initialScenarios: any[],
    initialEvals: any[]
  ) => {
    setSessionId(sid);
    setApiKey(key);
    setMetadata(meta);
    setScenarios(initialScenarios);
    setEvals(initialEvals);
    setCurrentStep(2);
  };

  const handleConfigComplete = () => {
    setCurrentStep(3);
  };

  const handleOptimizationComplete = (result: any) => {
    setFinalResult(result);
    setCurrentStep(4);
  };

  const handleStartOver = () => {
    setCurrentStep(1);
    setSessionId(null);
    setApiKey("");
    setMetadata(null);
    setScenarios([]);
    setEvals([]);
    setFinalResult(null);
  };

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4">
            <span className="gradient-text">Self-Improving</span> Agent Skills
          </h1>
          <p className="text-zinc-400 dark:text-zinc-400 text-zinc-600 text-lg">
            Powered by Google ADK multi-agent system and Gemini
          </p>
          <div className="flex items-center justify-center gap-2 mt-3">
            <span className="px-3 py-1 bg-blue-500/10 text-blue-400 dark:text-blue-400 text-blue-600 rounded-full text-xs font-medium border border-blue-500/20">Google ADK</span>
            <span className="px-3 py-1 bg-violet-500/10 text-violet-400 dark:text-violet-400 text-violet-600 rounded-full text-xs font-medium border border-violet-500/20">Gemini</span>
            <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 dark:text-emerald-400 text-emerald-600 rounded-full text-xs font-medium border border-emerald-500/20">Multi-Agent</span>
          </div>
        </div>

        <StepIndicator currentStep={currentStep} />

        <div className="mt-12">
          {currentStep === 1 && (
            <UploadStep onComplete={handleUploadComplete} />
          )}

          {currentStep === 2 && sessionId && (
            <ConfigStep
              sessionId={sessionId}
              apiKey={apiKey}
              scenarios={scenarios}
              evals={evals}
              onScenariosChange={setScenarios}
              onEvalsChange={setEvals}
              onComplete={handleConfigComplete}
            />
          )}

          {currentStep === 3 && sessionId && (
            <RunningStep
              sessionId={sessionId}
              apiKey={apiKey}
              scenarios={scenarios}
              evals={evals}
              onComplete={handleOptimizationComplete}
            />
          )}

          {currentStep === 4 && finalResult && (
            <ResultsStep
              result={finalResult}
              sessionId={sessionId!}
              onStartOver={handleStartOver}
            />
          )}
        </div>
      </div>
    </main>
  );
}
