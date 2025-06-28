import axios from 'axios';
import { API_CONFIG, ERROR_MESSAGES } from '../utils/constants';
import type { 
  ConfigData, 
  StrategyResults, 
  RunStrategiesRequest,
  BacktestRequest,
  ConfigUpdateResponse
} from '../types';

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor for logging and authentication
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('Response error:', error);
    return Promise.reject(error);
  }
);

// Error handler utility
export const handleApiError = (error: any): string => {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    
    switch (status) {
      case 400:
        return error.response?.data?.detail || ERROR_MESSAGES.VALIDATION_ERROR;
      case 401:
        return ERROR_MESSAGES.UNAUTHORIZED;
      case 403:
        return ERROR_MESSAGES.FORBIDDEN;
      case 404:
        return ERROR_MESSAGES.NOT_FOUND;
      case 500:
        return ERROR_MESSAGES.SERVER_ERROR;
      case undefined:
        return ERROR_MESSAGES.NETWORK;
      default:
        return error.response?.data?.detail || ERROR_MESSAGES.UNKNOWN;
    }
  }
  return error instanceof Error ? error.message : ERROR_MESSAGES.UNKNOWN;
};

// Configuration API
const getConfig = async (): Promise<ConfigData> => {
  const response = await apiClient.get<ConfigData>('/api/config');
  return response.data;
};

const updateConfig = async (newConfig: Partial<ConfigData>): Promise<ConfigUpdateResponse> => {
  const response = await apiClient.put<ConfigUpdateResponse>('/api/config', newConfig);
  return response.data;
};

// Strategy API
const runStrategies = async (params: RunStrategiesRequest): Promise<StrategyResults> => {
  const response = await apiClient.post<StrategyResults>('/api/run', params);
  return response.data;
};

const getTrades = async (): Promise<{ trades: any[]; count: number; source: string }> => {
  const response = await apiClient.get('/api/trades');
  return response.data;
};

const getSummary = async (): Promise<{ message: string; last_run: any }> => {
  const response = await apiClient.get('/api/summary');
  return response.data;
};

// Recommendations API
const runBacktest = async (params: BacktestRequest): Promise<any> => {
  const response = await apiClient.post('/api/recommendations/analyze', params);
  return response.data;
};

const getCurrentPositions = async (): Promise<any> => {
  const response = await apiClient.get('/api/recommendations/current-positions');
  return response.data;
};

const getMarketAlerts = async (): Promise<any> => {
  const response = await apiClient.get('/api/recommendations/market-alerts');
  return response.data;
};

const runCustomBacktest = async (params: {
  start_date: string;
  end_date: string;
  strategies: string[];
  initial_capital: number;
}): Promise<any> => {
  const response = await apiClient.post('/api/recommendations/backtest-custom', null, { params });
  return response.data;
};

// Health check
const healthCheck = async (): Promise<{ status: string; message: string }> => {
  const response = await apiClient.get('/api/health');
  return response.data;
};

// Unified API service
export const apiService = {
  // Configuration
  getConfig,
  updateConfig,
  
  // Strategies
  runStrategies,
  getTrades,
  getSummary,
  
  // Recommendations & Backtesting
  runBacktest,
  getCurrentPositions,
  getMarketAlerts,
  runCustomBacktest,
  
  // Health
  healthCheck
};

export default apiService;