"use client";

import { useState, useEffect } from "react";
import { useCoAgent, useCopilotAction } from "@copilotkit/react-core";
import { motion, AnimatePresence } from "framer-motion";
import {
  Swords,
  DollarSign,
  TrendingDown,
  TrendingUp,
  Handshake,
  XCircle,
  Trophy,
  Play,
  RotateCcw,
  Sparkles,
  Zap
} from "lucide-react";

// Types for agent state
type NegotiationRound = {
  round: number;
  type: "buyer_offer" | "seller_response";
  offer_amount?: number;
  action?: string;
  counter_amount?: number;
  message: string;
  buyer_name?: string;
  buyer_emoji?: string;
  seller_name?: string;
  seller_emoji?: string;
};

type Scenario = {
  id: string;
  title: string;
  emoji: string;
  item: string;
  asking_price: number;
  description: string;
};

type Personality = {
  id: string;
  name: string;
  emoji: string;
  description: string;
};

type AgentState = {
  status: "setup" | "ready" | "negotiating" | "deal" | "no_deal";
  scenario?: {
    title: string;
    item: string;
    asking_price: number;
  };
  buyer?: {
    name: string;
    emoji: string;
    budget: number;
  };
  seller?: {
    name: string;
    emoji: string;
    minimum: number;
  };
  rounds: NegotiationRound[];
  current_round: number;
  final_price?: number;
};

// Offer Card Component - Editorial Style
function OfferCard({ round, isLatest }: { round: NegotiationRound; isLatest: boolean }) {
  const isBuyer = round.type === "buyer_offer";

  return (
    <motion.div
      initial={{ opacity: 0, x: isBuyer ? -20 : 20, y: 10 }}
      animate={{ opacity: 1, x: 0, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className={`
        relative p-6 rounded-lg mb-6 max-w-lg
        ${isBuyer
          ? "bg-white border border-border-light ml-auto shadow-sm"
          : "bg-bg-subtle border border-border-light mr-auto shadow-sm"
        }
        ${isLatest ? "ring-1 ring-text-tertiary" : ""}
      `}
    >
      {/* Round Indicator */}
      <div className={`
        absolute -top-3 ${isBuyer ? "-right-3" : "-left-3"}
        bg-text-primary text-bg-app px-2 py-1 rounded text-[10px] font-bold tracking-widest uppercase shadow-md
      `}>
        Round {round.round}
      </div>

      {/* Header */}
      <div className={`flex items-center gap-3 mb-4 ${isBuyer ? "flex-row-reverse" : ""}`}>
        <span className="text-xl filter grayscale opacity-80">
          {isBuyer ? round.buyer_emoji : round.seller_emoji}
        </span>
        <span className="font-serif font-bold text-sm text-text-primary tracking-wide">
          {isBuyer ? round.buyer_name : round.seller_name}
        </span>
      </div>

      {/* Offer Content */}
      <div className={`${isBuyer ? "text-right" : "text-left"}`}>
        {isBuyer && round.offer_amount && (
          <div className="mb-3">
            <span className="block text-xs font-bold text-text-tertiary uppercase tracking-widest mb-1">Offer</span>
            <span className="font-serif text-3xl font-medium text-text-primary block">
              ${round.offer_amount.toLocaleString()}
            </span>
          </div>
        )}

        {!isBuyer && round.action && (
          <div className={`mb-3 ${isBuyer ? "text-right" : "text-left"}`}>
            <span className="block text-xs font-bold text-text-tertiary uppercase tracking-widest mb-1">Response</span>
            {round.action === "accept" && (
              <span className="text-lg font-serif font-medium text-emerald-700 flex items-center gap-2">
                <Handshake className="w-4 h-4" /> Deal Accepted
              </span>
            )}
            {round.action === "counter" && (
              <span className="font-serif text-3xl font-medium text-text-primary block">
                ${round.counter_amount?.toLocaleString()}
              </span>
            )}
            {round.action === "reject" && (
              <span className="text-lg font-serif font-medium text-red-700 flex items-center gap-2">
                <XCircle className="w-4 h-4" /> Offer Rejected
              </span>
            )}
            {round.action === "walk" && (
              <span className="text-lg font-serif font-medium text-text-tertiary flex items-center gap-2">
                <XCircle className="w-4 h-4" /> Ended Negotiation
              </span>
            )}
          </div>
        )}

        {/* Message Body */}
        <p className="text-text-secondary text-sm leading-relaxed font-sans border-t border-border-light pt-3 mt-2">
          {round.message}
        </p>
      </div>
    </motion.div>
  );
}

// Deal Banner Component - Editorial Style
function DealBanner({ finalPrice, askingPrice }: { finalPrice: number; askingPrice: number }) {
  const savings = askingPrice - finalPrice;
  const percentOff = ((savings / askingPrice) * 100).toFixed(1);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-bg-card rounded-2xl p-12 text-center shadow-lg border border-border-medium max-w-xl mx-auto"
    >
      <div className="mb-6 flex justify-center">
        <Trophy className="w-12 h-12 text-text-primary" strokeWidth={1} />
      </div>
      <h2 className="text-sm font-bold tracking-widest text-text-tertiary uppercase mb-4">Agreement Reached</h2>
      <p className="text-6xl font-serif text-text-primary mb-8 font-medium">
        ${finalPrice.toLocaleString()}
      </p>
      <div className="flex justify-center gap-12 border-t border-border-light pt-8">
        <div>
          <p className="text-text-tertiary text-xs uppercase tracking-wider mb-1">Savings</p>
          <p className="font-serif text-xl text-text-secondary">${savings.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-text-tertiary text-xs uppercase tracking-wider mb-1">Discount</p>
          <p className="font-serif text-xl text-text-secondary">{percentOff}%</p>
        </div>
      </div>
    </motion.div>
  );
}

// ==================== CHAT UI COMPONENTS ====================

// Chat Bubble Component
const ChatBubble = ({ round, type }: { round: NegotiationRound; type: "buyer" | "seller" }) => {
  const name = type === "buyer" ? round.buyer_name : round.seller_name;
  const emoji = type === "buyer" ? round.buyer_emoji : round.seller_emoji;

  return (
    <motion.div
      initial={{ opacity: 0, x: type === "buyer" ? -50 : 50 }}
      animate={{ opacity: 1, x: 0 }}
      className={`chat-bubble ${type}`}
    >
      <div className="avatar">{emoji}</div>
      <div className="bubble-content">
        <div className="name">{name}</div>
        <div className="message">{round.message}</div>
        {round.offer_amount && (
          <div className="offer-badge">${round.offer_amount.toLocaleString()}</div>
        )}
      </div>
    </motion.div>
  );
};

// Typing Indicator Component
const TypingIndicator = ({ emoji, name }: { emoji: string; name: string }) => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    className="typing-indicator"
  >
    <span className="avatar" style={{ fontSize: '20px' }}>{emoji}</span>
    <div className="dots">
      <span></span>
      <span></span>
      <span></span>
    </div>
    <span className="typing-text">{name} is thinking...</span>
  </motion.div>
);

// Price Tracker Component
const PriceTracker = ({
  currentOffer,
  askingPrice,
  minimum,
  budget
}: {
  currentOffer: number;
  askingPrice: number;
  minimum: number;
  budget: number;
}) => {
  const range = budget - minimum;
  const position = ((currentOffer - minimum) / range) * 100;

  return (
    <div className="price-tracker">
      <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: 'var(--text-dark)' }}>
        💰 Price Convergence
      </h4>
      <div className="track">
        <div className="sweet-spot" style={{ left: `${Math.max(10, Math.min(90, position))}%` }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <div className="range-marker seller">Min: ${minimum.toLocaleString()}</div>
        <div className="range-marker buyer">Max: ${budget.toLocaleString()}</div>
      </div>
    </div>
  );
};

// Main Page Component
export default function NegotiationBattle() {
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [selectedBuyer, setSelectedBuyer] = useState<string | null>(null);
  const [selectedSeller, setSelectedSeller] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [buyers, setBuyers] = useState<Personality[]>([]);
  const [sellers, setSellers] = useState<Personality[]>([]);

  // Connect to agent state
  const { state, setState } = useCoAgent<AgentState>({
    name: "negotiation_agent",
    initialState: {
      status: "setup",
      rounds: [],
      current_round: 0,
    },
  });

  // Fetch available scenarios and personalities on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('[DEBUG] Fetching scenarios and personalities...');
        // Fetch scenarios
        const scenariosRes = await fetch('http://localhost:8000/get_available_scenarios');
        const scenariosData = await scenariosRes.json();
        console.log('[DEBUG] Scenarios fetched:', scenariosData);
        if (scenariosData.scenarios) {
          setScenarios(scenariosData.scenarios);
          console.log('[DEBUG] Scenarios state updated:', scenariosData.scenarios.length, 'scenarios');
        }

        // Fetch personalities
        const personalitiesRes = await fetch('http://localhost:8000/get_available_personalities');
        const personalitiesData = await personalitiesRes.json();
        console.log('[DEBUG] Personalities fetched:', personalitiesData);
        if (personalitiesData.buyers && personalitiesData.sellers) {
          setBuyers(personalitiesData.buyers);
          setSellers(personalitiesData.sellers);
          console.log('[DEBUG] Personalities state updated:', personalitiesData.buyers.length, 'buyers,', personalitiesData.sellers.length, 'sellers');
        }
      } catch (error) {
        console.error('[DEBUG] Error fetching data:', error);
      }
    };
    fetchData();
  }, []);

  // Debug logging for state changes
  useEffect(() => {
    console.log('[DEBUG] Current agent state:', state);
    console.log('[DEBUG] Scenarios count:', scenarios.length);
    console.log('[DEBUG] Buyers count:', buyers.length);
    console.log('[DEBUG] Sellers count:', sellers.length);
  }, [state, scenarios, buyers, sellers]);

  const handleStartBattle = async () => {
    if (!selectedScenario || !selectedBuyer || !selectedSeller) return;

    try {
      // Configure the negotiation
      const configRes = await fetch('http://localhost:8000/configure_negotiation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_id: selectedScenario,
          buyer_personality: selectedBuyer,
          seller_personality: selectedSeller,
        }),
      });
      const configData = await configRes.json();

      // Update state with configuration
      setState({
        ...state,
        status: "ready",
        scenario: configData.scenario,
        buyer: configData.buyer,
        seller: configData.seller,
      });

      // Start the negotiation
      const startRes = await fetch('http://localhost:8000/start_negotiation', {
        method: 'POST',
      });
      const startData = await startRes.json();

      if (startData.status === "started") {
        setState({
          ...state,
          status: "negotiating",
          scenario: configData.scenario,
          buyer: configData.buyer,
          seller: configData.seller,
        });

        // Start the automated negotiation
        runNegotiation();
      }
    } catch (error) {
      console.error('Error starting battle:', error);
    }
  };

  const runNegotiation = async () => {
    // This will be handled by the agent automatically
    // Just need to poll for state updates
    const pollInterval = setInterval(async () => {
      try {
        const stateRes = await fetch('http://localhost:8000/get_negotiation_state');
        const stateData = await stateRes.json();

        setState({
          status: stateData.status,
          scenario: {
            title: stateData.scenario,
            item: stateData.item,
            asking_price: stateData.asking_price,
          },
          buyer: stateData.buyer,
          seller: stateData.seller,
          rounds: stateData.rounds,
          current_round: stateData.current_round,
          final_price: stateData.final_price,
        });

        if (stateData.status === "deal" || stateData.status === "no_deal") {
          clearInterval(pollInterval);
        }
      } catch (error) {
        console.error('Error polling state:', error);
      }
    }, 1000);
  };

  const handleReset = () => {
    setSelectedScenario(null);
    setSelectedBuyer(null);
    setSelectedSeller(null);
    setState({
      status: "setup",
      rounds: [],
      current_round: 0,
    });
  };

  return (
    <main className="min-h-screen bg-bg-app">
      {/* Header - Editorial Style */}
      <header className="border-b border-border-light bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-8">
          <motion.div
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="flex flex-col items-center justify-center gap-2"
          >
            <h1 className="text-4xl md:text-5xl font-serif tracking-tight text-text-primary">
              The Negotiation
            </h1>
            <p
              className="text-center text-sm font-sans tracking-wide uppercase text-text-tertiary"
            >
              Autonomous Agent Simulation
            </p>
          </motion.div>
        </div>
      </header>

      <div className="relative container mx-auto px-4 py-12">
        {/* Setup Phase - Editorial Style */}
        {(state.status === "setup" || (!state.status && scenarios.length > 0)) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-5xl mx-auto space-y-16"
          >
            {/* Scenario Selection */}
            <section>
              <div className="text-center mb-10">
                <span className="text-xs font-bold tracking-widest text-text-tertiary uppercase mb-2 block">Step 1</span>
                <h2 className="text-3xl font-serif text-text-primary">
                  Select Context
                </h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {scenarios.map((scenario) => (
                  <motion.div
                    key={scenario.id}
                    whileHover={{ y: -4 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setSelectedScenario(scenario.id)}
                    className={`
                      cursor-pointer p-8 rounded-xl border transition-all duration-200
                      ${selectedScenario === scenario.id
                        ? 'bg-bg-card border-text-primary shadow-md ring-1 ring-text-primary'
                        : 'bg-bg-subtle border-transparent hover:border-border-medium hover:bg-bg-card'
                      }
                    `}
                  >
                    <div className="text-4xl mb-6 text-center filter grayscale opacity-90">{scenario.emoji}</div>
                    <h3 className="text-lg font-serif font-medium text-center mb-2 text-text-primary">{scenario.title}</h3>
                    <p className="text-text-secondary text-sm text-center mb-4 line-clamp-2">{scenario.item}</p>
                    <p className="text-center text-text-primary font-bold font-serif">
                      ${scenario.asking_price.toLocaleString()}
                    </p>
                  </motion.div>
                ))}
              </div>
            </section>

            {/* Character Selection */}
            {selectedScenario && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-16"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-16">
                  {/* Buyer Selection */}
                  <section>
                    <div className="text-center mb-8">
                      <span className="text-xs font-bold tracking-widest text-text-tertiary uppercase mb-2 block">Step 2</span>
                      <h2 className="text-2xl font-serif text-text-primary">
                        Choose Buyer
                      </h2>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      {buyers.map((buyer) => (
                        <motion.div
                          key={buyer.id}
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          onClick={() => setSelectedBuyer(buyer.id)}
                          className={`
                            cursor-pointer p-5 rounded-lg border transition-all
                            ${selectedBuyer === buyer.id
                              ? 'bg-bg-card border-text-primary shadow-sm'
                              : 'bg-bg-subtle border-transparent hover:border-border-medium'
                            }
                          `}
                        >
                          <div className="text-3xl mb-3 text-center filter grayscale opacity-90">{buyer.emoji}</div>
                          <h4 className="text-sm font-medium text-center text-text-primary">{buyer.name}</h4>
                        </motion.div>
                      ))}
                    </div>
                  </section>

                  {/* Seller Selection */}
                  <section>
                    <div className="text-center mb-8">
                      <span className="text-xs font-bold tracking-widest text-text-tertiary uppercase mb-2 block">Step 3</span>
                      <h2 className="text-2xl font-serif text-text-primary">
                        Choose Seller
                      </h2>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      {sellers.map((seller) => (
                        <motion.div
                          key={seller.id}
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          onClick={() => setSelectedSeller(seller.id)}
                          className={`
                            cursor-pointer p-5 rounded-lg border transition-all
                            ${selectedSeller === seller.id
                              ? 'bg-bg-card border-text-primary shadow-sm'
                              : 'bg-bg-subtle border-transparent hover:border-border-medium'
                            }
                          `}
                        >
                          <div className="text-3xl mb-3 text-center filter grayscale opacity-90">{seller.emoji}</div>
                          <h4 className="text-sm font-medium text-center text-text-primary">{seller.name}</h4>
                        </motion.div>
                      ))}
                    </div>
                  </section>
                </div>

                {/* Start Button */}
                {selectedBuyer && selectedSeller && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex justify-center pt-8"
                  >
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={handleStartBattle}
                      className="px-10 py-4 bg-text-primary text-bg-app rounded-full font-serif font-medium text-xl shadow-lg hover:shadow-xl transition-all flex items-center gap-3 tracking-wide"
                    >
                      <Play className="w-5 h-5 fill-current" />
                      Begin Negotiation
                    </motion.button>
                  </motion.div>
                )}
              </motion.div>
            )}
          </motion.div>
        )}

        {/* Battle Phase */}
        {(state.status === "ready" || state.status === "negotiating" || state.status === "deal" || state.status === "no_deal") && (
          <div className="max-w-5xl mx-auto">
            {/* Scenario Header - Editorial Style */}
            {state.scenario && (
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center mb-16 bg-bg-card border border-border-light rounded-2xl p-8 shadow-sm"
              >
                <div className="inline-block px-3 py-1 mb-4 border border-border-medium rounded-full text-xs font-semibold tracking-wider text-text-tertiary uppercase">
                  Negotiation Item
                </div>
                <h2 className="text-4xl font-serif text-text-primary mb-2">
                  {state.scenario.title}
                </h2>
                <p className="text-xl text-text-secondary mb-6 font-light">{state.scenario.item}</p>
                <div className="inline-flex items-center gap-2 text-lg border-t border-b border-border-light py-2 px-6">
                  <span className="text-text-tertiary uppercase text-xs font-bold tracking-widest">Asking Price</span>
                  <span className="text-text-primary font-serif font-bold text-xl">
                    ${state.scenario.asking_price?.toLocaleString()}
                  </span>
                </div>
              </motion.div>
            )}

            {/* Comparison Display - Editorial Two-Column */}
            {state.buyer && state.seller && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mb-16 items-start">

                {/* Buyer Column */}
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="text-right pr-6 border-r border-border-light"
                >
                  <span className="text-xs font-bold tracking-widest text-text-tertiary uppercase mb-4 block">Buyer</span>
                  <div className="text-5xl mb-6 grayscale hover:grayscale-0 transition-all duration-500 opacity-90 hover:opacity-100">{state.buyer.emoji}</div>
                  <h3 className="text-3xl font-serif text-text-primary mb-2">{state.buyer.name}</h3>
                  <p className="font-sans text-text-secondary mb-1">Budget: <span className="font-semibold text-text-primary">${state.buyer.budget?.toLocaleString()}</span></p>
                </motion.div>

                {/* Seller Column */}
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="text-left pl-6"
                >
                  <span className="text-xs font-bold tracking-widest text-text-tertiary uppercase mb-4 block">Seller</span>
                  <div className="text-5xl mb-6 grayscale hover:grayscale-0 transition-all duration-500 opacity-90 hover:opacity-100">{state.seller.emoji}</div>
                  <h3 className="text-3xl font-serif text-text-primary mb-2">{state.seller.name}</h3>
                  <p className="font-sans text-text-secondary mb-1">Minimum: <span className="font-semibold text-text-primary">${state.seller.minimum?.toLocaleString()}</span></p>
                </motion.div>

              </div>
            )}

            {/* Negotiation Chat */}
            {state.rounds && state.rounds.length > 0 && (
              <div className="max-w-3xl mx-auto mb-12">
                <div className="flex items-center justify-center gap-2 mb-8">
                  <span className="h-px w-8 bg-border-medium"></span>
                  <span className="text-xs font-bold tracking-widest text-text-tertiary uppercase">Live Transcript</span>
                  <span className="h-px w-8 bg-border-medium"></span>
                </div>

                {/* Price Tracker */}
                {state.buyer && state.seller && state.rounds.length > 0 && state.rounds[state.rounds.length - 1].offer_amount && (
                  <div className="mb-10 px-8">
                    <PriceTracker
                      currentOffer={state.rounds[state.rounds.length - 1].offer_amount || state.scenario?.asking_price || 0}
                      askingPrice={state.scenario?.asking_price || 0}
                      minimum={state.seller.minimum || 0}
                      budget={state.buyer.budget || 0}
                    />
                  </div>
                )}

                {/* Chat Bubbles */}
                <div className="space-y-6">
                  <AnimatePresence>
                    {state.rounds.map((round, index) => {
                      const isBuyer = round.type === "buyer_offer" || round.buyer_name;
                      return (
                        <OfferCard
                          key={`${round.type}-${round.round}-${index}`}
                          round={round}
                          isLatest={index === state.rounds.length - 1}
                        />
                      );
                    })}
                  </AnimatePresence>

                  {/* Typing Indicator */}
                  {(state.status === "negotiating" || state.status === "ready") && (
                    <div className="flex justify-center py-4">
                      <TypingIndicator
                        emoji={state.current_round % 2 === 0 ? state.buyer?.emoji || "🔵" : state.seller?.emoji || "🔴"}
                        name={state.current_round % 2 === 0 ? state.buyer?.name || "Buyer" : state.seller?.name || "Seller"}
                      />
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Deal Banner */}
            {state.status === "deal" && state.final_price && state.scenario && (
              <div className="max-w-2xl mx-auto mb-8">
                <DealBanner
                  finalPrice={state.final_price}
                  askingPrice={state.scenario.asking_price}
                />
              </div>
            )}

            {/* No Deal Banner */}
            {state.status === "no_deal" && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="max-w-xl mx-auto mb-12 bg-bg-card border border-border-medium rounded-xl p-10 text-center shadow-lg"
              >
                <div className="mb-6 flex justify-center">
                  <div className="h-16 w-16 bg-bg-subtle rounded-full flex items-center justify-center">
                    <XCircle className="w-8 h-8 text-text-tertiary" />
                  </div>
                </div>
                <h2 className="text-3xl font-serif text-text-primary mb-3">Negotiation Ended</h2>
                <p className="text-text-secondary font-sans leading-relaxed">No agreement could be reached between the parties.</p>
              </motion.div>
            )}

            {/* Reset Button */}
            {(state.status === "deal" || state.status === "no_deal") && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex justify-center mt-12 mb-12"
              >
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleReset}
                  className="px-8 py-3 bg-text-primary text-bg-app rounded-full font-serif font-medium text-lg shadow-lg hover:shadow-xl transition-all flex items-center gap-3 tracking-wide"
                >
                  <RotateCcw className="w-5 h-5" />
                  Start New Negotiation
                </motion.button>
              </motion.div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
