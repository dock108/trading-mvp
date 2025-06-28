/**
 * API-specific types and interfaces
 */

export interface ApiResponse<T> {
  data: T;
  status: number;
  statusText: string;
  headers: Record<string, string>;
  config: Record<string, any>;
}

export interface ApiError {
  response?: {
    data: { detail: string };
    status: number;
    statusText: string;
    headers: Record<string, string>;
    config: Record<string, any>;
  };
  message: string;
  isAxiosError: boolean;
}

export interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export interface UseApiReturn<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  execute: (...args: any[]) => Promise<{ success: boolean; data?: T; error?: string }>;
  reset: () => void;
}

// Request/Response types
export interface RunStrategiesRequest {
  strategies: string[];
  config_overrides?: Record<string, any>;
  backtest?: boolean;
}

export interface BacktestRequest {
  start_date: string;
  end_date: string;
  initial_capital: number;
  strategies?: string[];
  risk_tolerance?: string;
}

export interface ConfigUpdateRequest {
  config: Partial<any>;
}

export interface ConfigUpdateResponse {
  config: any;
  message: string;
}