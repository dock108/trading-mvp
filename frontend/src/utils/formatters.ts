/**
 * Currency formatting utilities
 */
export const formatCurrency = (
  amount: number,
  options: Intl.NumberFormatOptions = {}
): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
    ...options
  }).format(amount);
};

/**
 * Percentage formatting utilities
 */
export const formatPercentage = (
  value: number,
  options: { 
    includeSign?: boolean;
    decimals?: number;
  } = {}
): string => {
  const { includeSign = true, decimals = 2 } = options;
  const sign = includeSign && value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)}%`;
};

/**
 * Number formatting with locale
 */
export const formatNumber = (
  value: number,
  options: Intl.NumberFormatOptions = {}
): string => {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 4,
    ...options
  }).format(value);
};

/**
 * Duration formatting
 */
export const formatDuration = (seconds: number): string => {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  } else if (seconds < 3600) {
    return `${(seconds / 60).toFixed(1)}m`;
  } else {
    return `${(seconds / 3600).toFixed(1)}h`;
  }
};

/**
 * Date formatting utilities
 */
export const formatDate = (
  date: string | Date,
  options: Intl.DateTimeFormatOptions = {}
): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...options
  }).format(dateObj);
};

export const formatDateTime = (
  date: string | Date,
  options: Intl.DateTimeFormatOptions = {}
): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    ...options
  }).format(dateObj);
};

/**
 * Asset type styling utilities
 */
export const getAssetTypeStyle = (type: string): string => {
  const styles = {
    stock: 'bg-blue-100 text-blue-800',
    etf: 'bg-green-100 text-green-800',
    crypto: 'bg-purple-100 text-purple-800',
    default: 'bg-gray-100 text-gray-800'
  };
  return styles[type as keyof typeof styles] || styles.default;
};

/**
 * Risk level styling utilities
 */
export const getRiskLevelStyle = (risk: string): string => {
  const styles = {
    low: 'bg-green-100 text-green-800 border-green-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    high: 'bg-red-100 text-red-800 border-red-200',
    default: 'bg-gray-100 text-gray-800 border-gray-200'
  };
  return styles[risk.toLowerCase() as keyof typeof styles] || styles.default;
};

/**
 * Severity level styling utilities
 */
export const getSeverityStyle = (severity: string): string => {
  const styles = {
    high: 'text-red-600 bg-red-50 border-red-200',
    medium: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    low: 'text-blue-600 bg-blue-50 border-blue-200',
    default: 'text-gray-600 bg-gray-50 border-gray-200'
  };
  return styles[severity.toLowerCase() as keyof typeof styles] || styles.default;
};

/**
 * P&L color utilities
 */
export const getPnLColor = (value: number): string => {
  return value >= 0 ? 'text-green-600' : 'text-red-600';
};

/**
 * Truncate text utility
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
};