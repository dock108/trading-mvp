import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { ConfigData, StrategyResults } from '../../types';

// Mock data factories
export const createMockConfig = (overrides: Partial<ConfigData> = {}): ConfigData => ({
  initial_capital: 100000,
  strategies: {
    wheel: true,
    rotator: true
  },
  allocation: {
    wheel: 0.5,
    rotator: 0.5
  },
  data_mode: 'live',
  wheel_symbols: ['SPY', 'QQQ', 'IWM'],
  rotator_symbols: ['BTC', 'ETH', 'SOL'],
  simulation: {
    weeks_to_simulate: 8,
    enable_deterministic_mode: true
  },
  ...overrides
});

export const createMockStrategyResults = (overrides: Partial<StrategyResults> = {}): StrategyResults => ({
  results: {
    wheel: {
      trades: [
        {
          week: 'Week0',
          strategy: 'Wheel',
          symbol: 'IWM',
          action: 'SELL_PUT',
          quantity: 1,
          price: 3.96,
          strike: 198.12,
          cash_flow: 3.96,
          notes: 'Sold put with strike $198.12',
          timestamp: '2025-06-28T13:09:31.211424'
        }
      ],
      summary: {
        total_trades: 4,
        initial_capital: 50000,
        final_capital: 50016.11,
        total_return: 0.03,
        execution_time: 1.5
      },
      strategy_name: 'wheel',
      execution_time: 1.5
    },
    rotator: {
      trades: [
        {
          week: 'Week0',
          strategy: 'Rotator',
          symbol: 'BTC',
          action: 'BUY_CRYPTO',
          quantity: 0.482,
          price: 103732.58,
          cash_flow: -50000,
          notes: 'Bought 0.4820 BTC @ $103732.58',
          timestamp: '2025-06-28T13:09:31.213139'
        }
      ],
      summary: {
        total_trades: 11,
        initial_capital: 50000,
        final_capital: 49623.83,
        total_return: -0.75,
        execution_time: 2.1
      },
      strategy_name: 'rotator',
      execution_time: 2.1
    }
  },
  status: 'success',
  ran_at: '2025-06-28T13:09:31.211424',
  total_trades: 15,
  combined_summary: {
    total_execution_time: 3.6,
    total_strategies_run: 2,
    combined_cash_flow: -46376.17,
    strategies_requested: ['wheel', 'rotator'],
    data_mode: 'live'
  },
  ...overrides
});

export const createMockPosition = (overrides = {}) => ({
  id: 'test-position-1',
  symbol: 'AAPL',
  asset_type: 'stock',
  quantity: 100,
  avg_cost: 150,
  current_price: 155,
  market_value: 15500,
  unrealized_pnl: 500,
  notes: 'Test position',
  ...overrides
});

export const createMockRecommendation = (overrides = {}) => ({
  action: 'BUY',
  symbol: 'AAPL',
  confidence: 0.75,
  reasoning: 'Strong fundamentals and momentum',
  risk_level: 'LOW',
  allocation_percentage: 25,
  expected_return: 8.5,
  quantity: 100,
  current_price: 155,
  ...overrides
});

// Custom render function that includes common providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  // Add any context providers here if needed
}

const customRender = (
  ui: ReactElement,
  options?: CustomRenderOptions
) => {
  // Add any global providers here (e.g., theme, context providers)
  const Wrapper = ({ children }: { children: React.ReactNode }) => {
    return <>{children}</>;
  };

  return render(ui, { wrapper: Wrapper, ...options });
};

// Re-export everything
export * from '@testing-library/react';
export { customRender as render };

// Utility functions for common test scenarios
export const waitForLoadingToFinish = async () => {
  const { waitFor } = await import('@testing-library/react');
  await waitFor(() => {
    expect(document.querySelector('[data-testid="loading-spinner"]')).not.toBeInTheDocument();
  });
};

export const expectElementToHaveText = (element: HTMLElement, expectedText: string) => {
  expect(element).toHaveTextContent(expectedText);
};

export const expectElementToBeVisible = (testId: string) => {
  const element = document.querySelector(`[data-testid="${testId}"]`);
  expect(element).toBeVisible();
};

// Mock API responses
export const mockApiSuccess = (data: any) => ({
  data,
  status: 200,
  statusText: 'OK',
  headers: {},
  config: {}
});

export const mockApiError = (message = 'API Error', status = 500) => ({
  response: {
    data: { detail: message },
    status,
    statusText: status === 500 ? 'Internal Server Error' : 'Error',
    headers: {},
    config: {}
  },
  message,
  isAxiosError: true
});