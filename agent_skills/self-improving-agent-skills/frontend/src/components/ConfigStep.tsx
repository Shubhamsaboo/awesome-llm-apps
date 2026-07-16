"use client";

import { useState } from "react";
import { CheckSquare, Square, Plus, X, RefreshCw, ArrowRight } from "lucide-react";

interface ConfigStepProps {
  sessionId: string;
  apiKey: string;
  scenarios: any[];
  evals: any[];
  onScenariosChange: (scenarios: any[]) => void;
  onEvalsChange: (evals: any[]) => void;
  onComplete: () => void;
}

export default function ConfigStep({
  sessionId,
  apiKey,
  scenarios: initialScenarios,
  evals: initialEvals,
  onScenariosChange,
  onEvalsChange,
  onComplete,
}: ConfigStepProps) {
  const [scenarios, setScenarios] = useState(
    initialScenarios.map((s) => ({ ...s, selected: true, editing: false }))
  );
  const [evals, setEvals] = useState(
    initialEvals.map((e) => ({ ...e, selected: true, editing: false }))
  );
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [showAddScenario, setShowAddScenario] = useState(false);
  const [showAddEval, setShowAddEval] = useState(false);

  const handleScenarioToggle = (id: number) => {
    setScenarios((prev) =>
      prev.map((s) => (s.id === id ? { ...s, selected: !s.selected } : s))
    );
  };

  const handleEvalToggle = (id: number) => {
    setEvals((prev) =>
      prev.map((e) => (e.id === id ? { ...e, selected: !e.selected } : e))
    );
  };

  const handleScenarioEdit = (id: number, field: string, value: string) => {
    setScenarios((prev) =>
      prev.map((s) => (s.id === id ? { ...s, [field]: value } : s))
    );
  };

  const handleEvalEdit = (id: number, field: string, value: string) => {
    setEvals((prev) =>
      prev.map((e) => (e.id === id ? { ...e, [field]: value } : e))
    );
  };

  const handleDeleteScenario = (id: number) => {
    setScenarios((prev) => prev.filter((s) => s.id !== id));
  };

  const handleDeleteEval = (id: number) => {
    setEvals((prev) => prev.filter((e) => e.id !== id));
  };

  const handleAddScenario = () => {
    const newId = Math.max(...scenarios.map((s) => s.id), 0) + 1;
    setScenarios((prev) => [
      ...prev,
      {
        id: newId,
        description: "New scenario",
        input: "",
        selected: true,
        editing: true,
      },
    ]);
    setShowAddScenario(false);
  };

  const handleAddEval = () => {
    const newId = Math.max(...evals.map((e) => e.id), 0) + 1;
    setEvals((prev) => [
      ...prev,
      {
        id: newId,
        name: "New criterion",
        question: "",
        pass_condition: "",
        fail_condition: "",
        selected: true,
        editing: true,
      },
    ]);
    setShowAddEval(false);
  };

  const handleRegenerate = async () => {
    setIsRegenerating(true);

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8891";
      const response = await fetch(`${API_BASE}/api/regenerate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, gemini_api_key: apiKey }),
      });

      if (!response.ok) {
        throw new Error("Regeneration failed");
      }

      const data = await response.json();
      setScenarios(data.scenarios.map((s: any) => ({ ...s, selected: true })));
      setEvals(data.evals.map((e: any) => ({ ...e, selected: true })));
    } catch (error) {
      alert("Failed to regenerate. Please try again.");
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleContinue = async () => {
    const selectedScenarios = scenarios.filter((s) => s.selected);
    const selectedEvals = evals.filter((e) => e.selected);

    if (selectedScenarios.length === 0 || selectedEvals.length === 0) {
      alert("Please select at least one scenario and one evaluation criterion");
      return;
    }

    try {
      const API_BASE2 = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8891";
      const response = await fetch(`${API_BASE2}/api/update-config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          scenarios: selectedScenarios,
          evals: selectedEvals,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to save configuration");
      }

      onScenariosChange(selectedScenarios);
      onEvalsChange(selectedEvals);
      onComplete();
    } catch (error) {
      alert("Failed to save configuration. Please try again.");
    }
  };

  const selectedScenarioCount = scenarios.filter((s) => s.selected).length;
  const selectedEvalCount = evals.filter((e) => e.selected).length;

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="glass rounded-2xl p-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold">Test Scenarios</h2>
            <span className="px-3 py-1 bg-violet-500/20 text-violet-400 rounded-full text-sm font-medium">
              {selectedScenarioCount} selected
            </span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowAddScenario(true)}
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add
            </button>
            <button
              onClick={handleRegenerate}
              disabled={isRegenerating}
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${isRegenerating ? "animate-spin" : ""}`} />
              Regenerate
            </button>
          </div>
        </div>

        <div className="space-y-4">
          {showAddScenario && (
            <div className="p-4 bg-zinc-900 border border-zinc-800 rounded-lg">
              <button
                onClick={handleAddScenario}
                className="w-full py-3 border-2 border-dashed border-zinc-700 rounded-lg hover:border-violet-500 transition-colors text-zinc-400 hover:text-white"
              >
                Click to add scenario
              </button>
            </div>
          )}

          {scenarios.map((scenario) => (
            <div
              key={scenario.id}
              className="p-4 bg-zinc-900 border border-zinc-800 rounded-lg hover:border-zinc-700 transition-colors"
            >
              <div className="flex items-start gap-3">
                <button
                  onClick={() => handleScenarioToggle(scenario.id)}
                  className="mt-1 text-violet-500 hover:text-violet-400"
                >
                  {scenario.selected ? (
                    <CheckSquare className="w-5 h-5" />
                  ) : (
                    <Square className="w-5 h-5" />
                  )}
                </button>

                <div className="flex-1 space-y-2">
                  <input
                    type="text"
                    value={scenario.description}
                    onChange={(e) =>
                      handleScenarioEdit(scenario.id, "description", e.target.value)
                    }
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg focus:outline-none focus:border-violet-500"
                  />
                  <textarea
                    value={scenario.input}
                    onChange={(e) =>
                      handleScenarioEdit(scenario.id, "input", e.target.value)
                    }
                    rows={3}
                    placeholder="Test input..."
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg focus:outline-none focus:border-violet-500 resize-none"
                  />
                </div>

                <button
                  onClick={() => handleDeleteScenario(scenario.id)}
                  className="mt-1 text-zinc-500 hover:text-red-400 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="glass rounded-2xl p-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold">Evaluation Criteria</h2>
            <span className="px-3 py-1 bg-violet-500/20 text-violet-400 rounded-full text-sm font-medium">
              {selectedEvalCount} selected
            </span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowAddEval(true)}
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add
            </button>
          </div>
        </div>

        <div className="space-y-4">
          {showAddEval && (
            <div className="p-4 bg-zinc-900 border border-zinc-800 rounded-lg">
              <button
                onClick={handleAddEval}
                className="w-full py-3 border-2 border-dashed border-zinc-700 rounded-lg hover:border-violet-500 transition-colors text-zinc-400 hover:text-white"
              >
                Click to add criterion
              </button>
            </div>
          )}

          {evals.map((evalItem) => (
            <div
              key={evalItem.id}
              className="p-4 bg-zinc-900 border border-zinc-800 rounded-lg hover:border-zinc-700 transition-colors"
            >
              <div className="flex items-start gap-3">
                <button
                  onClick={() => handleEvalToggle(evalItem.id)}
                  className="mt-1 text-violet-500 hover:text-violet-400"
                >
                  {evalItem.selected ? (
                    <CheckSquare className="w-5 h-5" />
                  ) : (
                    <Square className="w-5 h-5" />
                  )}
                </button>

                <div className="flex-1 space-y-2">
                  <input
                    type="text"
                    value={evalItem.name}
                    onChange={(e) =>
                      handleEvalEdit(evalItem.id, "name", e.target.value)
                    }
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg focus:outline-none focus:border-violet-500 font-semibold"
                  />
                  <input
                    type="text"
                    value={evalItem.question}
                    onChange={(e) =>
                      handleEvalEdit(evalItem.id, "question", e.target.value)
                    }
                    placeholder="Yes/no question..."
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg focus:outline-none focus:border-violet-500"
                  />
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="text"
                      value={evalItem.pass_condition}
                      onChange={(e) =>
                        handleEvalEdit(evalItem.id, "pass_condition", e.target.value)
                      }
                      placeholder="Pass condition..."
                      className="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg focus:outline-none focus:border-green-500 text-sm"
                    />
                    <input
                      type="text"
                      value={evalItem.fail_condition}
                      onChange={(e) =>
                        handleEvalEdit(evalItem.id, "fail_condition", e.target.value)
                      }
                      placeholder="Fail condition..."
                      className="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg focus:outline-none focus:border-red-500 text-sm"
                    />
                  </div>
                </div>

                <button
                  onClick={() => handleDeleteEval(evalItem.id)}
                  className="mt-1 text-zinc-500 hover:text-red-400 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <button
        onClick={handleContinue}
        disabled={selectedScenarioCount === 0 || selectedEvalCount === 0}
        className={`
          w-full py-4 rounded-xl font-semibold transition-all flex items-center justify-center gap-2
          ${
            selectedScenarioCount > 0 && selectedEvalCount > 0
              ? "gradient-bg hover:scale-105"
              : "bg-zinc-800 text-zinc-500 cursor-not-allowed"
          }
        `}
      >
        Start Optimization
        <ArrowRight className="w-5 h-5" />
      </button>
    </div>
  );
}
