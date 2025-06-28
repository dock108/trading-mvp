import '@testing-library/jest-dom';

// Mock axios for all tests
jest.mock('axios');

// Mock lucide-react icons for all tests
jest.mock('lucide-react', () => ({
  Play: () => 'Play Icon',
  BarChart: () => 'BarChart Icon',
  Target: () => 'Target Icon',
  HelpCircle: () => 'HelpCircle Icon',
  Briefcase: () => 'Briefcase Icon',
  TrendingUp: () => 'TrendingUp Icon',
  TrendingDown: () => 'TrendingDown Icon',
  DollarSign: () => 'DollarSign Icon',
  AlertTriangle: () => 'AlertTriangle Icon',
  CheckCircle: () => 'CheckCircle Icon',
  RefreshCw: () => 'RefreshCw Icon',
  Eye: () => 'Eye Icon',
  Plus: () => 'Plus Icon',
  Edit3: () => 'Edit3 Icon',
  Trash2: () => 'Trash2 Icon',
  Save: () => 'Save Icon',
  X: () => 'X Icon',
  Settings: () => 'Settings Icon',
  Calendar: () => 'Calendar Icon',
  Clock: () => 'Clock Icon'
}));

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    href: 'http://localhost:5173',
    origin: 'http://localhost:5173',
    protocol: 'http:',
    host: 'localhost:5173',
    hostname: 'localhost',
    port: '5173',
    pathname: '/',
    search: '',
    hash: ''
  },
  writable: true
});

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock
});

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  log: jest.fn(),
  warn: jest.fn(),
  error: jest.fn()
};