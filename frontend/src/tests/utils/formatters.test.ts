import {
  formatCurrency,
  formatPercentage,
  formatNumber,
  formatDuration,
  formatDate,
  formatDateTime,
  getAssetTypeStyle,
  getRiskLevelStyle,
  getSeverityStyle,
  getPnLColor,
  truncateText
} from '../../utils/formatters';

describe('formatters', () => {
  describe('formatCurrency', () => {
    it('should format positive numbers as currency', () => {
      expect(formatCurrency(1234.56)).toBe('$1,234.56');
      expect(formatCurrency(1000000)).toBe('$1,000,000.00');
    });

    it('should format negative numbers as currency', () => {
      expect(formatCurrency(-1234.56)).toBe('-$1,234.56');
    });

    it('should handle zero', () => {
      expect(formatCurrency(0)).toBe('$0.00');
    });
  });

  describe('formatPercentage', () => {
    it('should format positive percentages with + sign by default', () => {
      expect(formatPercentage(5.67)).toBe('+5.67%');
    });

    it('should format negative percentages without extra sign', () => {
      expect(formatPercentage(-3.45)).toBe('-3.45%');
    });

    it('should respect includeSign option', () => {
      expect(formatPercentage(5.67, { includeSign: false })).toBe('5.67%');
    });

    it('should respect decimals option', () => {
      expect(formatPercentage(5.6789, { decimals: 1 })).toBe('+5.7%');
    });
  });

  describe('formatNumber', () => {
    it('should format numbers with locale', () => {
      expect(formatNumber(1234567.89)).toBe('1,234,567.89');
    });

    it('should respect maxFractionDigits', () => {
      expect(formatNumber(1234.56789, { maximumFractionDigits: 2 })).toBe('1,234.57');
    });
  });

  describe('formatDuration', () => {
    it('should format seconds', () => {
      expect(formatDuration(30)).toBe('30.0s');
    });

    it('should format minutes', () => {
      expect(formatDuration(90)).toBe('1.5m');
    });

    it('should format hours', () => {
      expect(formatDuration(3900)).toBe('1.1h');
    });
  });

  describe('formatDate', () => {
    it('should format date string', () => {
      const result = formatDate('2023-12-25');
      expect(result).toMatch(/Dec 25, 2023/);
    });

    it('should format Date object', () => {
      const date = new Date('2023-12-25');
      const result = formatDate(date);
      expect(result).toMatch(/Dec 25, 2023/);
    });
  });

  describe('formatDateTime', () => {
    it('should format date and time', () => {
      const result = formatDateTime('2023-12-25T10:30:00');
      expect(result).toMatch(/Dec 25, 2023.*10:30/);
    });
  });

  describe('getAssetTypeStyle', () => {
    it('should return correct styles for known asset types', () => {
      expect(getAssetTypeStyle('stock')).toBe('bg-blue-100 text-blue-800');
      expect(getAssetTypeStyle('etf')).toBe('bg-green-100 text-green-800');
      expect(getAssetTypeStyle('crypto')).toBe('bg-purple-100 text-purple-800');
    });

    it('should return default style for unknown asset type', () => {
      expect(getAssetTypeStyle('unknown')).toBe('bg-gray-100 text-gray-800');
    });
  });

  describe('getRiskLevelStyle', () => {
    it('should return correct styles for risk levels', () => {
      expect(getRiskLevelStyle('low')).toBe('bg-green-100 text-green-800 border-green-200');
      expect(getRiskLevelStyle('LOW')).toBe('bg-green-100 text-green-800 border-green-200');
      expect(getRiskLevelStyle('medium')).toBe('bg-yellow-100 text-yellow-800 border-yellow-200');
      expect(getRiskLevelStyle('high')).toBe('bg-red-100 text-red-800 border-red-200');
    });
  });

  describe('getSeverityStyle', () => {
    it('should return correct styles for severity levels', () => {
      expect(getSeverityStyle('high')).toBe('text-red-600 bg-red-50 border-red-200');
      expect(getSeverityStyle('medium')).toBe('text-yellow-600 bg-yellow-50 border-yellow-200');
      expect(getSeverityStyle('low')).toBe('text-blue-600 bg-blue-50 border-blue-200');
    });
  });

  describe('getPnLColor', () => {
    it('should return green for positive values', () => {
      expect(getPnLColor(100)).toBe('text-green-600');
      expect(getPnLColor(0)).toBe('text-green-600');
    });

    it('should return red for negative values', () => {
      expect(getPnLColor(-100)).toBe('text-red-600');
    });
  });

  describe('truncateText', () => {
    it('should not truncate text shorter than max length', () => {
      expect(truncateText('hello', 10)).toBe('hello');
    });

    it('should truncate text longer than max length', () => {
      expect(truncateText('hello world', 8)).toBe('hello...');
    });

    it('should handle exact length', () => {
      expect(truncateText('hello', 5)).toBe('hello');
    });
  });
});