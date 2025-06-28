import { useState, useEffect } from 'react';
import Header from './components/Header';
import ControlsPanel from './components/ControlsPanel';
import ResultsPanel from './components/ResultsPanel';
import BacktestPanel from './components/BacktestPanel';
import RecommendationsPanel from './components/RecommendationsPanel';
import ExplainerPanel from './components/ExplainerPanel';
import PortfolioPanel from './components/PortfolioPanel';
import { LoadingSpinner } from './components/common';
import { Play, BarChart, Target, HelpCircle, Briefcase } from 'lucide-react';
import { useApi } from './hooks/useApi';
import { apiService } from './services/apiService';
import { TABS, type TabType } from './utils/constants';
import type { ConfigData, StrategyResults } from './types';

function App() {
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [results, setResults] = useState<StrategyResults | null>(null);
  const [status, setStatus] = useState<string>('Ready');
  const [activeTab, setActiveTab] = useState<TabType>(TABS.HELP);

  // API hooks
  const configApi = useApi(apiService.getConfig);
  const updateConfigApi = useApi(apiService.updateConfig);
  const runStrategiesApi = useApi(apiService.runStrategies);
  const backtestApi = useApi(apiService.runBacktest);

  // Load initial configuration
  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    const result = await configApi.execute();
    if (result.success && result.data) {
      setConfig(result.data);
    }
  };

  const updateConfig = async (newConfig: Partial<ConfigData>) => {
    const result = await updateConfigApi.execute(newConfig);
    if (result.success && result.data) {
      setConfig((result.data as any).config);
      return true;
    }
    return false;
  };

  const runStrategies = async (strategies: string[], configOverrides?: any) => {
    setStatus('Running strategies...');
    setResults(null);

    const result = await runStrategiesApi.execute({
      strategies,
      config_overrides: configOverrides,
      backtest: true
    });

    if (result.success && result.data) {
      setResults(result.data as StrategyResults);
      setStatus(`Completed at ${new Date().toLocaleTimeString()}`);
    } else {
      setStatus('Failed');
    }
  };

  const runBacktest = async (params: any) => {
    return await backtestApi.execute(params);
  };

  if (configApi.loading || !config) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="lg" className="mx-auto mb-4" />
          <p className="text-gray-600">Loading configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="container mx-auto px-4 py-6">
        {/* Tab Navigation */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {[
                { id: TABS.HELP, icon: HelpCircle, label: 'How It Works' },
                { id: TABS.PORTFOLIO, icon: Briefcase, label: 'Portfolio Manager' },
                { id: TABS.RECOMMENDATIONS, icon: Target, label: 'Investment Recommendations' },
                { id: TABS.BACKTEST, icon: BarChart, label: 'Historical Analysis' },
                { id: TABS.STRATEGY, icon: Play, label: 'Strategy Testing' }
              ].map(({ id, icon: Icon, label }) => (
                <button
                  key={id}
                  onClick={() => setActiveTab(id)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <Icon className="h-4 w-4" />
                    <span>{label}</span>
                  </div>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === TABS.HELP && (
          <div className="max-w-6xl mx-auto">
            <ExplainerPanel />
          </div>
        )}
        
        {activeTab === TABS.PORTFOLIO && (
          <div className="max-w-7xl mx-auto">
            <PortfolioPanel />
          </div>
        )}
        
        {activeTab === TABS.RECOMMENDATIONS && (
          <div className="max-w-6xl mx-auto">
            <RecommendationsPanel />
          </div>
        )}
        
        {activeTab === TABS.BACKTEST && (
          <div className="max-w-4xl mx-auto">
            <BacktestPanel
              onRunBacktest={runBacktest}
              isLoading={backtestApi.loading}
              error={backtestApi.error}
              results={backtestApi.data}
            />
          </div>
        )}
        
        {activeTab === TABS.STRATEGY && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Controls Panel */}
            <div className="lg:col-span-1">
              <ControlsPanel
                config={config}
                onConfigUpdate={updateConfig}
                onRunStrategies={runStrategies}
                isLoading={runStrategiesApi.loading}
                status={status}
                error={runStrategiesApi.error}
              />
            </div>

            {/* Results Panel */}
            <div className="lg:col-span-2">
              <ResultsPanel
                results={results}
                isLoading={runStrategiesApi.loading}
                config={config}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
