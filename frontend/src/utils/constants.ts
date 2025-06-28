/**
 * Application constants and configuration
 */

// API Configuration
export const API_CONFIG = {
  BASE_URL: 'http://127.0.0.1:8001',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000
} as const;

// Tab Configuration
export const TABS = {
  HELP: 'help',
  PORTFOLIO: 'portfolio',
  RECOMMENDATIONS: 'recommendations',
  BACKTEST: 'backtest',
  STRATEGY: 'strategy'
} as const;

export type TabType = typeof TABS[keyof typeof TABS];

// Asset Types
export const ASSET_TYPES = {
  STOCK: 'stock',
  ETF: 'etf',
  CRYPTO: 'crypto'
} as const;

export type AssetType = typeof ASSET_TYPES[keyof typeof ASSET_TYPES];

// Risk Tolerance Levels
export const RISK_TOLERANCE = {
  LOW: 'LOW',
  MEDIUM: 'MEDIUM',
  HIGH: 'HIGH'
} as const;

export type RiskTolerance = typeof RISK_TOLERANCE[keyof typeof RISK_TOLERANCE];

// Data Modes
export const DATA_MODES = {
  LIVE: 'live',
  MOCK: 'mock'
} as const;

export type DataMode = typeof DATA_MODES[keyof typeof DATA_MODES];

// Rebalance Frequencies
export const REBALANCE_FREQUENCIES = {
  WEEKLY: 'weekly',
  MONTHLY: 'monthly',
  QUARTERLY: 'quarterly'
} as const;

export type RebalanceFrequency = typeof REBALANCE_FREQUENCIES[keyof typeof REBALANCE_FREQUENCIES];

// Trading Actions
export const TRADING_ACTIONS = {
  BUY: 'BUY',
  SELL: 'SELL',
  HOLD: 'HOLD',
  REDUCE: 'REDUCE',
  BUY_CRYPTO: 'BUY_CRYPTO',
  SELL_CRYPTO: 'SELL_CRYPTO',
  SELL_PUT: 'SELL_PUT',
  BUY_SHARES: 'BUY_SHARES',
  SELL_CALL: 'SELL_CALL'
} as const;

export type TradingAction = typeof TRADING_ACTIONS[keyof typeof TRADING_ACTIONS];

// Default Values
export const DEFAULTS = {
  INITIAL_CAPITAL: 100000,
  CASH_BALANCE: 50000,
  SIMULATION_WEEKS: 8,
  RISK_TOLERANCE: RISK_TOLERANCE.MEDIUM,
  DATA_MODE: DATA_MODES.LIVE,
  REBALANCE_FREQUENCY: REBALANCE_FREQUENCIES.WEEKLY,
  
  // Default symbols
  WHEEL_SYMBOLS: ['SPY', 'QQQ', 'IWM'],
  ROTATOR_SYMBOLS: ['BTC', 'ETH', 'SOL'],
  
  // Default allocations
  WHEEL_ALLOCATION: 0.5,
  ROTATOR_ALLOCATION: 0.5
} as const;

// Validation Rules
export const VALIDATION = {
  MIN_CAPITAL: 1000,
  MAX_CAPITAL: 10000000,
  MIN_QUANTITY: 0.0001,
  MAX_QUANTITY: 1000000,
  MIN_PRICE: 0.01,
  MAX_PRICE: 1000000,
  SYMBOL_MAX_LENGTH: 10,
  NOTES_MAX_LENGTH: 500
} as const;

// UI Configuration
export const UI_CONFIG = {
  ITEMS_PER_PAGE: 50,
  DEBOUNCE_DELAY: 300,
  LOADING_TIMEOUT: 30000,
  AUTO_REFRESH_INTERVAL: 300000, // 5 minutes
  
  // Breakpoints (matching Tailwind)
  BREAKPOINTS: {
    SM: 640,
    MD: 768,
    LG: 1024,
    XL: 1280,
    '2XL': 1536
  }
} as const;

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK: 'Network error. Please check your connection.',
  TIMEOUT: 'Request timed out. Please try again.',
  UNAUTHORIZED: 'Authentication required. Please log in.',
  FORBIDDEN: 'Access denied. Insufficient permissions.',
  NOT_FOUND: 'Requested resource not found.',
  SERVER_ERROR: 'Server error. Please try again later.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  UNKNOWN: 'An unknown error occurred.',
  
  // Specific validation messages
  REQUIRED_FIELD: 'This field is required.',
  INVALID_SYMBOL: 'Please enter a valid symbol.',
  INVALID_QUANTITY: 'Quantity must be greater than 0.',
  INVALID_PRICE: 'Price must be greater than 0.',
  INVALID_DATE: 'Please enter a valid date.',
  INVALID_EMAIL: 'Please enter a valid email address.'
} as const;

// Success Messages
export const SUCCESS_MESSAGES = {
  SAVE_SUCCESS: 'Successfully saved!',
  UPDATE_SUCCESS: 'Successfully updated!',
  DELETE_SUCCESS: 'Successfully deleted!',
  PORTFOLIO_SAVED: 'Portfolio saved successfully!',
  CONFIG_UPDATED: 'Configuration updated successfully!',
  ANALYSIS_COMPLETE: 'Analysis completed successfully!'
} as const;