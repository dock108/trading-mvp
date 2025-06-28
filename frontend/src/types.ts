// Type definitions for the Trading Dashboard

export interface ConfigData {
  initial_capital: number;
  strategies: {
    wheel: boolean;
    rotator: boolean;
  };
  allocation: {
    wheel: number;
    rotator: number;
  };
  data_mode: string;
  wheel_symbols: string[];
  rotator_symbols: string[];
  simulation?: {
    weeks_to_simulate: number;
    enable_deterministic_mode: boolean;
  };
  [key: string]: any; // Allow for additional config properties
}

export interface TradeRecord {
  week: string;
  strategy: string;
  symbol: string;
  action: string;
  quantity: number;
  price: number;
  strike?: number;
  cash_flow: number;
  notes: string;
  timestamp: string;
}

export interface StrategySummary {
  total_trades: number;
  initial_capital: number;
  final_capital: number;
  total_return: number;
  execution_time: number;
  [key: string]: any;
}

export interface StrategyResult {
  trades: TradeRecord[];
  summary: StrategySummary;
  strategy_name: string;
  execution_time: number;
  error?: string;
}

export interface StrategyResults {
  results: {
    wheel?: StrategyResult;
    rotator?: StrategyResult;
  };
  status: string;
  ran_at: string;
  total_trades: number;
  combined_summary: {
    total_execution_time: number;
    total_strategies_run: number;
    combined_cash_flow: number;
    strategies_requested: string[];
    data_mode: string;
  };
}

export interface ChartDataPoint {
  date: string;
  value: number;
  [key: string]: any;
}

export interface PriceDataPoint {
  time: string;
  price: number;
  symbol?: string;
}