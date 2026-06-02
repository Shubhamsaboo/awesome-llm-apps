/**
 * Stock and Portfolio data layer for the Investment Simulator demo.
 * Contains mock stock data, portfolio management, and trading logic.
 */

// Type definitions
export type Sector =
  | "technology"
  | "healthcare"
  | "finance"
  | "energy"
  | "consumer"
  | "industrial";
export type RiskTolerance = "conservative" | "moderate" | "aggressive";
export type PortfolioFocus =
  | "tech"
  | "healthcare"
  | "diversified"
  | "growth"
  | "dividend";

/**
 * Represents a stock in the market.
 */
export interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number; // % change today
  sector: Sector;
  volatility: number; // 0-1, higher = more volatile
  dividendYield: number; // annual %
}

/**
 * Represents a holding in a portfolio.
 */
export interface Holding {
  symbol: string;
  name: string;
  shares: number;
  avgCost: number;
  currentPrice: number;
  change: number;
  value: number;
  profitLoss: number;
}

/**
 * Historical data point for performance chart.
 */
export interface PerformancePoint {
  date: string;
  value: number;
}

/**
 * Represents a user's investment portfolio.
 */
export interface Portfolio {
  id: string;
  cash: number;
  holdings: Holding[];
  totalValue: number;
  totalProfitLoss: number;
  allocation: {
    stocks: number; // percentage
    cash: number;
  };
  performance: PerformancePoint[];
}

/**
 * Trade action type.
 */
export type TradeAction = "buy" | "sell";

/**
 * Result of a trade execution.
 */
export interface TradeResult {
  success: boolean;
  message: string;
  portfolio?: Portfolio;
  trade?: {
    action: TradeAction;
    symbol: string;
    shares: number;
    price: number;
    total: number;
  };
}

/**
 * Mock stock database with 18 stocks across sectors.
 */
const STOCKS: Stock[] = [
  // Technology
  {
    symbol: "AAPL",
    name: "Apple Inc.",
    price: 178.5,
    change: 1.2,
    sector: "technology",
    volatility: 0.3,
    dividendYield: 0.5,
  },
  {
    symbol: "MSFT",
    name: "Microsoft Corp.",
    price: 378.25,
    change: 0.8,
    sector: "technology",
    volatility: 0.25,
    dividendYield: 0.8,
  },
  {
    symbol: "GOOGL",
    name: "Alphabet Inc.",
    price: 141.8,
    change: -0.5,
    sector: "technology",
    volatility: 0.35,
    dividendYield: 0,
  },
  {
    symbol: "NVDA",
    name: "NVIDIA Corp.",
    price: 495.2,
    change: 2.5,
    sector: "technology",
    volatility: 0.5,
    dividendYield: 0.04,
  },
  {
    symbol: "META",
    name: "Meta Platforms",
    price: 505.3,
    change: 1.8,
    sector: "technology",
    volatility: 0.45,
    dividendYield: 0.4,
  },

  // Healthcare
  {
    symbol: "JNJ",
    name: "Johnson & Johnson",
    price: 156.4,
    change: 0.3,
    sector: "healthcare",
    volatility: 0.15,
    dividendYield: 3.0,
  },
  {
    symbol: "UNH",
    name: "UnitedHealth Group",
    price: 528.9,
    change: -0.2,
    sector: "healthcare",
    volatility: 0.2,
    dividendYield: 1.4,
  },
  {
    symbol: "PFE",
    name: "Pfizer Inc.",
    price: 27.15,
    change: -1.5,
    sector: "healthcare",
    volatility: 0.3,
    dividendYield: 5.8,
  },

  // Finance
  {
    symbol: "JPM",
    name: "JPMorgan Chase",
    price: 195.6,
    change: 0.9,
    sector: "finance",
    volatility: 0.25,
    dividendYield: 2.4,
  },
  {
    symbol: "BAC",
    name: "Bank of America",
    price: 33.8,
    change: 1.1,
    sector: "finance",
    volatility: 0.3,
    dividendYield: 2.8,
  },
  {
    symbol: "V",
    name: "Visa Inc.",
    price: 279.45,
    change: 0.6,
    sector: "finance",
    volatility: 0.2,
    dividendYield: 0.8,
  },

  // Energy
  {
    symbol: "XOM",
    name: "Exxon Mobil",
    price: 104.25,
    change: -0.8,
    sector: "energy",
    volatility: 0.35,
    dividendYield: 3.5,
  },
  {
    symbol: "CVX",
    name: "Chevron Corp.",
    price: 151.7,
    change: -0.4,
    sector: "energy",
    volatility: 0.3,
    dividendYield: 4.0,
  },

  // Consumer
  {
    symbol: "AMZN",
    name: "Amazon.com",
    price: 178.9,
    change: 1.5,
    sector: "consumer",
    volatility: 0.35,
    dividendYield: 0,
  },
  {
    symbol: "WMT",
    name: "Walmart Inc.",
    price: 163.2,
    change: 0.4,
    sector: "consumer",
    volatility: 0.15,
    dividendYield: 1.4,
  },
  {
    symbol: "KO",
    name: "Coca-Cola Co.",
    price: 60.85,
    change: 0.2,
    sector: "consumer",
    volatility: 0.1,
    dividendYield: 3.1,
  },

  // Industrial
  {
    symbol: "CAT",
    name: "Caterpillar Inc.",
    price: 345.6,
    change: 0.7,
    sector: "industrial",
    volatility: 0.25,
    dividendYield: 1.6,
  },
  {
    symbol: "BA",
    name: "Boeing Co.",
    price: 198.3,
    change: -1.2,
    sector: "industrial",
    volatility: 0.4,
    dividendYield: 0,
  },
];

// In-memory portfolio storage (in production, use proper storage)
const portfolios: Map<string, Portfolio> = new Map();

/**
 * Get all available stocks.
 */
export function getStocks(): Stock[] {
  return STOCKS.map((s) => ({ ...s }));
}

/**
 * Get stock by symbol.
 */
export function getStockBySymbol(symbol: string): Stock | undefined {
  return STOCKS.find((s) => s.symbol === symbol);
}

/**
 * Generate a unique portfolio ID.
 */
function generatePortfolioId(): string {
  return `pf-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
}

/**
 * Generate historical performance data (fake 7-day history).
 */
function generatePerformanceHistory(currentValue: number): PerformancePoint[] {
  const points: PerformancePoint[] = [];
  const today = new Date();

  // Generate 7 days of history with some variance
  for (let i = 6; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);

    // Random variance between -3% and +3% for historical values
    const variance = i === 0 ? 0 : (Math.random() - 0.5) * 0.06;
    const value = Math.round(currentValue * (1 - variance) * 100) / 100;

    points.push({
      date: date.toISOString().split("T")[0],
      value,
    });
  }

  return points;
}

/**
 * Create a new portfolio based on user preferences.
 */
export function createPortfolio(options: {
  initialBalance: number;
  riskTolerance: RiskTolerance;
  focus: PortfolioFocus;
}): { portfolio: Portfolio; availableStocks: Stock[] } {
  const { initialBalance, riskTolerance, focus } = options;
  const id = generatePortfolioId();

  // Determine allocation percentages based on risk tolerance
  const stockAllocation =
    riskTolerance === "conservative"
      ? 0.4
      : riskTolerance === "moderate"
        ? 0.6
        : 0.8;

  const investmentAmount = initialBalance * stockAllocation;
  const cashAmount = initialBalance - investmentAmount;

  // Select stocks based on focus
  let selectedStocks: Stock[];
  switch (focus) {
    case "tech":
      selectedStocks = STOCKS.filter((s) => s.sector === "technology").slice(
        0,
        4,
      );
      break;
    case "healthcare":
      selectedStocks = STOCKS.filter((s) => s.sector === "healthcare");
      break;
    case "dividend":
      selectedStocks = STOCKS.filter((s) => s.dividendYield >= 2.0).slice(0, 5);
      break;
    case "growth":
      selectedStocks = STOCKS.filter(
        (s) => s.volatility >= 0.3 && s.dividendYield < 1,
      ).slice(0, 4);
      break;
    default: // diversified
      // One from each sector
      const sectors: Sector[] = [
        "technology",
        "healthcare",
        "finance",
        "energy",
        "consumer",
      ];
      selectedStocks = sectors.map(
        (sector) => STOCKS.find((s) => s.sector === sector)!,
      );
  }

  // Calculate equal investment per stock
  const perStockInvestment = investmentAmount / selectedStocks.length;

  // Create holdings with slight cost variance (simulating past purchases)
  const holdings: Holding[] = selectedStocks.map((stock) => {
    const shares = Math.floor(perStockInvestment / stock.price);
    // Average cost is slightly different from current (simulating earlier purchase)
    const costVariance = (Math.random() - 0.5) * 0.1; // +/- 5%
    const avgCost = Math.round(stock.price * (1 + costVariance) * 100) / 100;
    const value = shares * stock.price;
    const profitLoss = value - shares * avgCost;

    return {
      symbol: stock.symbol,
      name: stock.name,
      shares,
      avgCost,
      currentPrice: stock.price,
      change: stock.change,
      value: Math.round(value * 100) / 100,
      profitLoss: Math.round(profitLoss * 100) / 100,
    };
  });

  // Calculate totals
  const totalStockValue = holdings.reduce((sum, h) => sum + h.value, 0);
  const totalValue = totalStockValue + cashAmount;
  const totalProfitLoss = holdings.reduce((sum, h) => sum + h.profitLoss, 0);

  const portfolio: Portfolio = {
    id,
    cash: Math.round(cashAmount * 100) / 100,
    holdings,
    totalValue: Math.round(totalValue * 100) / 100,
    totalProfitLoss: Math.round(totalProfitLoss * 100) / 100,
    allocation: {
      stocks: Math.round((totalStockValue / totalValue) * 100),
      cash: Math.round((cashAmount / totalValue) * 100),
    },
    performance: generatePerformanceHistory(totalValue),
  };

  // Store portfolio
  portfolios.set(id, portfolio);

  // Return available stocks for trading (stocks not in portfolio)
  const holdingSymbols = new Set(holdings.map((h) => h.symbol));
  const availableStocks = STOCKS.filter((s) => !holdingSymbols.has(s.symbol));

  return { portfolio, availableStocks };
}

/**
 * Get portfolio by ID.
 */
export function getPortfolio(portfolioId: string): Portfolio | undefined {
  return portfolios.get(portfolioId);
}

/**
 * Execute a trade (buy or sell).
 */
export function executeTrade(
  portfolioId: string,
  symbol: string,
  action: TradeAction,
  quantity: number,
): TradeResult {
  const portfolio = portfolios.get(portfolioId);
  if (!portfolio) {
    return { success: false, message: "Portfolio not found" };
  }

  const stock = getStockBySymbol(symbol);
  if (!stock) {
    return { success: false, message: `Stock ${symbol} not found` };
  }

  const totalCost = stock.price * quantity;

  if (action === "buy") {
    // Check if user has enough cash
    if (totalCost > portfolio.cash) {
      return {
        success: false,
        message: `Insufficient funds. Need $${totalCost.toFixed(2)}, have $${portfolio.cash.toFixed(2)}`,
      };
    }

    // Find existing holding or create new
    let holding = portfolio.holdings.find((h) => h.symbol === symbol);
    if (holding) {
      // Update existing holding with new average cost
      const totalShares = holding.shares + quantity;
      const totalCostBasis = holding.shares * holding.avgCost + totalCost;
      holding.avgCost = Math.round((totalCostBasis / totalShares) * 100) / 100;
      holding.shares = totalShares;
      holding.currentPrice = stock.price;
      holding.change = stock.change;
      holding.value = Math.round(totalShares * stock.price * 100) / 100;
      holding.profitLoss =
        Math.round((holding.value - totalShares * holding.avgCost) * 100) / 100;
    } else {
      // Create new holding
      portfolio.holdings.push({
        symbol: stock.symbol,
        name: stock.name,
        shares: quantity,
        avgCost: stock.price,
        currentPrice: stock.price,
        change: stock.change,
        value: Math.round(totalCost * 100) / 100,
        profitLoss: 0,
      });
    }

    portfolio.cash = Math.round((portfolio.cash - totalCost) * 100) / 100;
  } else {
    // Sell
    const holding = portfolio.holdings.find((h) => h.symbol === symbol);
    if (!holding) {
      return { success: false, message: `You don't own any ${symbol}` };
    }

    if (quantity > holding.shares) {
      return {
        success: false,
        message: `Can't sell ${quantity} shares. You only own ${holding.shares}`,
      };
    }

    // Update holding
    holding.shares -= quantity;
    if (holding.shares === 0) {
      // Remove holding entirely
      portfolio.holdings = portfolio.holdings.filter(
        (h) => h.symbol !== symbol,
      );
    } else {
      holding.value = Math.round(holding.shares * stock.price * 100) / 100;
      holding.profitLoss =
        Math.round((holding.value - holding.shares * holding.avgCost) * 100) /
        100;
    }

    portfolio.cash = Math.round((portfolio.cash + totalCost) * 100) / 100;
  }

  // Recalculate portfolio totals
  const totalStockValue = portfolio.holdings.reduce(
    (sum, h) => sum + h.value,
    0,
  );
  portfolio.totalValue =
    Math.round((totalStockValue + portfolio.cash) * 100) / 100;
  portfolio.totalProfitLoss =
    Math.round(
      portfolio.holdings.reduce((sum, h) => sum + h.profitLoss, 0) * 100,
    ) / 100;
  portfolio.allocation = {
    stocks:
      portfolio.totalValue > 0
        ? Math.round((totalStockValue / portfolio.totalValue) * 100)
        : 0,
    cash:
      portfolio.totalValue > 0
        ? Math.round((portfolio.cash / portfolio.totalValue) * 100)
        : 0,
  };

  // Update performance (add today's value)
  portfolio.performance[portfolio.performance.length - 1].value =
    portfolio.totalValue;

  return {
    success: true,
    message: `${action === "buy" ? "Bought" : "Sold"} ${quantity} shares of ${symbol} at $${stock.price.toFixed(2)}`,
    portfolio,
    trade: {
      action,
      symbol,
      shares: quantity,
      price: stock.price,
      total: Math.round(totalCost * 100) / 100,
    },
  };
}

/**
 * Refresh stock prices with random small changes.
 */
export function refreshPrices(
  portfolioId: string,
): { portfolio: Portfolio; availableStocks: Stock[] } | undefined {
  const portfolio = portfolios.get(portfolioId);
  if (!portfolio) {
    return undefined;
  }

  // Update all stock prices with small random changes
  STOCKS.forEach((stock) => {
    // Random change between -2% and +2%, weighted by volatility
    const changePercent = (Math.random() - 0.5) * 0.04 * stock.volatility * 2;
    stock.price = Math.round(stock.price * (1 + changePercent) * 100) / 100;
    stock.change = Math.round(changePercent * 100 * 100) / 100;
  });

  // Update holdings with new prices
  portfolio.holdings.forEach((holding) => {
    const stock = getStockBySymbol(holding.symbol);
    if (stock) {
      holding.currentPrice = stock.price;
      holding.change = stock.change;
      holding.value = Math.round(holding.shares * stock.price * 100) / 100;
      holding.profitLoss =
        Math.round((holding.value - holding.shares * holding.avgCost) * 100) /
        100;
    }
  });

  // Recalculate totals
  const totalStockValue = portfolio.holdings.reduce(
    (sum, h) => sum + h.value,
    0,
  );
  portfolio.totalValue =
    Math.round((totalStockValue + portfolio.cash) * 100) / 100;
  portfolio.totalProfitLoss =
    Math.round(
      portfolio.holdings.reduce((sum, h) => sum + h.profitLoss, 0) * 100,
    ) / 100;
  portfolio.allocation = {
    stocks:
      portfolio.totalValue > 0
        ? Math.round((totalStockValue / portfolio.totalValue) * 100)
        : 0,
    cash:
      portfolio.totalValue > 0
        ? Math.round((portfolio.cash / portfolio.totalValue) * 100)
        : 0,
  };

  // Get available stocks
  const holdingSymbols = new Set(portfolio.holdings.map((h) => h.symbol));
  const availableStocks = STOCKS.filter((s) => !holdingSymbols.has(s.symbol));

  return { portfolio, availableStocks };
}
