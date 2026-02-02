"use client";

import { useState } from "react";
import { 
  CopilotSidebar, 
  CopilotKitCSSProperties 
} from "@copilotkit/react-ui";
import { useCoAgent, useCopilotAction } from "@copilotkit/react-core";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Swords, 
  DollarSign, 
  TrendingDown, 
  TrendingUp,
  Handshake,
  XCircle,
  Trophy
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

// Offer Card Component
function OfferCard({ round, isLatest }: { round: NegotiationRound; isLatest: boolean }) {
  const isBuyer = round.type === "buyer_offer";
  
  return (
    <motion.div
      initial={{ opacity: 0, x: isBuyer ? -50 : 50, scale: 0.9 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      transition={{ duration: 0.4 }}
      className={`
        relative p-4 rounded-xl mb-4
        ${isBuyer 
          ? "bg-gradient-to-r from-blue-900/80 to-blue-800/60 border-l-4 border-blue-400 mr-8" 
          : "bg-gradient-to-l from-red-900/80 to-red-800/60 border-r-4 border-red-400 ml-8"
        }
        ${isLatest ? "offer-pulse" : ""}
      `}
    >
      {/* Round Badge */}
      <div className={`
        absolute -top-2 ${isBuyer ? "-left-2" : "-right-2"}
        bg-gray-800 px-2 py-0.5 rounded-full text-xs font-bold
      `}>
        R{round.round}
      </div>

      {/* Agent Info */}
      <div className={`flex items-center gap-2 mb-2 ${!isBuyer && "flex-row-reverse"}`}>
        <span className="text-2xl">
          {isBuyer ? round.buyer_emoji : round.seller_emoji}
        </span>
        <span className="font-bold text-sm">
          {isBuyer ? round.buyer_name : round.seller_name}
        </span>
      </div>

      {/* Offer/Response */}
      <div className={`${!isBuyer && "text-right"}`}>
        {isBuyer && round.offer_amount && (
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="w-5 h-5 text-green-400" />
            <span className="text-2xl font-bold text-green-400">
              ${round.offer_amount.toLocaleString()}
            </span>
          </div>
        )}
        
        {!isBuyer && round.action && (
          <div className={`flex items-center gap-2 mb-2 ${!isBuyer && "justify-end"}`}>
            {round.action === "accept" && (
              <>
                <Handshake className="w-5 h-5 text-green-400" />
                <span className="text-xl font-bold text-green-400">ACCEPTED!</span>
              </>
            )}
            {round.action === "counter" && (
              <>
                <TrendingDown className="w-5 h-5 text-yellow-400" />
                <span className="text-xl font-bold text-yellow-400">
                  ${round.counter_amount?.toLocaleString()}
                </span>
              </>
            )}
            {round.action === "reject" && (
              <>
                <XCircle className="w-5 h-5 text-red-400" />
                <span className="text-xl font-bold text-red-400">REJECTED</span>
              </>
            )}
            {round.action === "walk" && (
              <>
                <XCircle className="w-5 h-5 text-red-500" />
                <span className="text-xl font-bold text-red-500">WALKED AWAY</span>
              </>
            )}
          </div>
        )}

        {/* Message */}
        <p className="text-gray-300 italic text-sm">"{round.message}"</p>
      </div>
    </motion.div>
  );
}

// Deal Banner Component
function DealBanner({ finalPrice, askingPrice }: { finalPrice: number; askingPrice: number }) {
  const savings = askingPrice - finalPrice;
  const percentOff = ((savings / askingPrice) * 100).toFixed(1);

  return (
    <motion.div
      initial={{ scale: 0, rotate: -10 }}
      animate={{ scale: 1, rotate: 0 }}
      transition={{ type: "spring", bounce: 0.5 }}
      className="deal-celebration bg-gradient-to-r from-green-600 to-emerald-500 rounded-2xl p-8 text-center shadow-2xl"
    >
      <Trophy className="w-16 h-16 mx-auto mb-4 text-yellow-300" />
      <h2 className="text-4xl font-black mb-2">🎉 DEAL CLOSED! 🎉</h2>
      <p className="text-5xl font-black text-yellow-300 mb-4">
        ${finalPrice.toLocaleString()}
      </p>
      <div className="flex justify-center gap-8 text-lg">
        <div>
          <p className="text-green-200">Savings</p>
          <p className="font-bold text-2xl">${savings.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-green-200">Off Asking</p>
          <p className="font-bold text-2xl">{percentOff}%</p>
        </div>
      </div>
    </motion.div>
  );
}

// Main Page Component
export default function NegotiationBattle() {
  const [themeColor] = useState("#6366f1");

  // Connect to agent state
  const { state } = useCoAgent<AgentState>({
    name: "negotiation_agent",
    initialState: {
      status: "setup",
      rounds: [],
      current_round: 0,
    },
  });

  // Register tool renderers for Generative UI
  useCopilotAction({
    name: "buyer_make_offer",
    description: "Buyer makes an offer",
    available: "disabled",
    parameters: [
      { name: "offer_amount", type: "number", required: true },
      { name: "message", type: "string", required: true },
    ],
    render: ({ args }) => (
      <div className="bg-blue-900/50 p-3 rounded-lg border border-blue-500">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-blue-400" />
          <span className="font-bold">Buyer Offers:</span>
          <span className="text-green-400 font-bold">
            ${(args.offer_amount as number)?.toLocaleString()}
          </span>
        </div>
      </div>
    ),
  });

  useCopilotAction({
    name: "seller_respond",
    description: "Seller responds to offer",
    available: "disabled",
    parameters: [
      { name: "action", type: "string", required: true },
      { name: "counter_amount", type: "number", required: false },
      { name: "message", type: "string", required: true },
    ],
    render: ({ args }) => (
      <div className="bg-red-900/50 p-3 rounded-lg border border-red-500">
        <div className="flex items-center gap-2">
          <TrendingDown className="w-4 h-4 text-red-400" />
          <span className="font-bold">Seller {args.action}s:</span>
          {args.counter_amount && (
            <span className="text-yellow-400 font-bold">
              ${(args.counter_amount as number)?.toLocaleString()}
            </span>
          )}
        </div>
      </div>
    ),
  });

  return (
    <main 
      className="min-h-screen"
      style={{ "--copilot-kit-primary-color": themeColor } as CopilotKitCSSProperties}
    >
      {/* Header */}
      <header className="bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 border-b border-gray-700">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-center gap-4">
            <Swords className="w-10 h-10 text-yellow-400" />
            <h1 className="text-4xl font-black bg-gradient-to-r from-yellow-400 via-red-500 to-blue-500 bg-clip-text text-transparent">
              AI NEGOTIATION BATTLE
            </h1>
            <Swords className="w-10 h-10 text-yellow-400 transform scale-x-[-1]" />
          </div>
          <p className="text-center text-gray-400 mt-2">
            Watch AI agents battle it out in epic negotiations!
          </p>
        </div>
      </header>

      {/* Battle Arena */}
      <div className="container mx-auto px-4 py-8 battle-arena">
        {/* Scenario Header */}
        {state.scenario && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-8"
          >
            <h2 className="text-2xl font-bold text-yellow-400">
              {state.scenario.title}
            </h2>
            <p className="text-xl text-gray-300">{state.scenario.item}</p>
            <p className="text-lg">
              Asking Price: <span className="text-green-400 font-bold">
                ${state.scenario.asking_price?.toLocaleString()}
              </span>
            </p>
          </motion.div>
        )}

        {/* VS Display */}
        {state.buyer && state.seller && (
          <div className="flex items-center justify-center gap-8 mb-8">
            {/* Buyer */}
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              className="buyer-glow bg-gradient-to-br from-blue-900 to-blue-800 rounded-2xl p-6 text-center min-w-[200px]"
            >
              <div className="text-5xl mb-2">{state.buyer.emoji}</div>
              <h3 className="text-xl font-bold text-blue-300">{state.buyer.name}</h3>
              <p className="text-sm text-gray-400">BUYER</p>
              <p className="text-green-400 font-bold mt-2">
                Budget: ${state.buyer.budget?.toLocaleString()}
              </p>
            </motion.div>

            {/* VS Badge */}
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.3, type: "spring" }}
              className="vs-badge rounded-full w-20 h-20 flex items-center justify-center text-3xl font-black text-gray-900"
            >
              VS
            </motion.div>

            {/* Seller */}
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              className="seller-glow bg-gradient-to-bl from-red-900 to-red-800 rounded-2xl p-6 text-center min-w-[200px]"
            >
              <div className="text-5xl mb-2">{state.seller.emoji}</div>
              <h3 className="text-xl font-bold text-red-300">{state.seller.name}</h3>
              <p className="text-sm text-gray-400">SELLER</p>
              <p className="text-yellow-400 font-bold mt-2">
                Minimum: ${state.seller.minimum?.toLocaleString()}
              </p>
            </motion.div>
          </div>
        )}

        {/* Negotiation Timeline */}
        {state.rounds && state.rounds.length > 0 && (
          <div className="max-w-2xl mx-auto">
            <h3 className="text-xl font-bold text-center mb-4 text-gray-300">
              ⏱️ NEGOTIATION TIMELINE
            </h3>
            <div className="relative">
              {/* Center line */}
              <div className="absolute left-1/2 top-0 bottom-0 w-1 timeline-connector transform -translate-x-1/2" />
              
              {/* Rounds */}
              <AnimatePresence>
                {state.rounds.map((round, index) => (
                  <OfferCard 
                    key={`${round.type}-${round.round}-${index}`} 
                    round={round} 
                    isLatest={index === state.rounds.length - 1}
                  />
                ))}
              </AnimatePresence>
            </div>
          </div>
        )}

        {/* Deal Banner */}
        {state.status === "deal" && state.final_price && state.scenario && (
          <div className="max-w-xl mx-auto mt-8">
            <DealBanner 
              finalPrice={state.final_price} 
              askingPrice={state.scenario.asking_price} 
            />
          </div>
        )}

        {/* No Deal Banner */}
        {state.status === "no_deal" && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="max-w-xl mx-auto mt-8 bg-gradient-to-r from-red-800 to-red-600 rounded-2xl p-8 text-center"
          >
            <XCircle className="w-16 h-16 mx-auto mb-4 text-red-300" />
            <h2 className="text-3xl font-black mb-2">NO DEAL 💔</h2>
            <p className="text-gray-200">The negotiation has ended without an agreement.</p>
          </motion.div>
        )}

        {/* Instructions when no negotiation */}
        {state.status === "setup" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-16"
          >
            <div className="text-6xl mb-4">🎮</div>
            <h2 className="text-2xl font-bold text-gray-300 mb-4">
              Ready to Start a Battle?
            </h2>
            <p className="text-gray-400 max-w-md mx-auto">
              Open the chat sidebar and tell the Battle Master to start a negotiation!
              Try: "Start a negotiation for a used car"
            </p>
          </motion.div>
        )}
      </div>

      {/* CopilotKit Sidebar */}
      <CopilotSidebar
        clickOutsideToClose={false}
        defaultOpen={true}
        labels={{
          title: "🎮 Battle Master",
          initial: `👋 Welcome to the AI Negotiation Battle Simulator!

I'm your Battle Master. I'll orchestrate an epic negotiation between AI agents.

**Try saying:**
- "Show me the available scenarios"
- "Start a negotiation for a used car"
- "Use Desperate Dan as the buyer and Shark Steve as the seller"

Ready to watch some AI agents battle it out? 🔥`
        }}
      />
    </main>
  );
}
