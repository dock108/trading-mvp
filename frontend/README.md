# Trading MVP Frontend

A React TypeScript application for managing trading strategies, portfolio analysis, and investment recommendations.

## 🏗️ Architecture

This frontend application follows modern React patterns and best practices:

### 📁 Project Structure

```
src/
├── components/           # React components
│   ├── common/          # Reusable UI components
│   │   ├── ErrorMessage.tsx
│   │   ├── FormField.tsx
│   │   ├── LoadingSpinner.tsx
│   │   └── index.ts
│   ├── BacktestPanel.tsx
│   ├── ControlsPanel.tsx
│   ├── ExplainerPanel.tsx
│   ├── Header.tsx
│   ├── PerformanceChart.tsx
│   ├── PortfolioPanel.tsx
│   ├── RecommendationsPanel.tsx
│   ├── ResultsPanel.tsx
│   ├── SummaryMetrics.tsx
│   └── TradesTable.tsx
├── hooks/               # Custom React hooks
│   └── useApi.ts       # API state management hook
├── services/           # API and external services
│   └── apiService.ts   # Centralized API client
├── types/              # TypeScript type definitions
│   ├── api.ts         # API-related types
│   ├── ui.ts          # UI component types
│   └── index.ts       # Main type exports
├── utils/              # Utility functions
│   ├── constants.ts   # Application constants
│   └── formatters.ts  # Data formatting utilities
├── tests/              # Test files (currently excluded from build)
├── App.tsx             # Main application component
├── main.tsx           # Application entry point
└── types.ts           # Legacy types (to be migrated)
```

## 🎯 Key Features

### 1. **Multi-Tab Interface**
- **How It Works**: User education and documentation
- **Portfolio Manager**: Comprehensive portfolio management
- **Investment Recommendations**: AI-powered trading suggestions
- **Historical Analysis**: Backtesting and performance metrics
- **Strategy Testing**: Live strategy simulation

### 2. **State Management**
- Custom `useApi` hook for consistent API state management
- Centralized error handling and loading states
- Type-safe API responses with proper TypeScript interfaces

### 3. **Component Architecture**
- **Single Responsibility Principle**: Each component has a focused purpose
- **Reusable Components**: Common UI elements in `components/common/`
- **Custom Hooks**: Shared logic extracted into reusable hooks
- **Type Safety**: Comprehensive TypeScript interfaces and types

### 4. **API Integration**
- Unified API service with axios interceptors
- Automatic error handling and retry logic
- Request/response logging for debugging
- Type-safe API calls with proper error handling

## 🛠️ Technical Implementation

### Custom Hooks

#### `useApi<T>`
Provides consistent API state management across components:
```typescript
const { data, loading, error, execute } = useApi(apiService.getConfig);

// Usage
const result = await execute();
if (result.success) {
  // Handle success
}
```

### Utility Functions

#### Formatters (`utils/formatters.ts`)
- `formatCurrency()` - Currency formatting with locale support
- `formatPercentage()` - Percentage formatting with sign options
- `formatNumber()` - Number formatting with locale
- `formatDate()` / `formatDateTime()` - Date formatting utilities
- Styling utilities for risk levels, asset types, P&L colors

#### Constants (`utils/constants.ts`)
- API configuration
- Tab definitions
- Asset types and risk tolerance levels
- Default values and validation rules
- Error and success messages

### Type Safety

Comprehensive TypeScript types organized by domain:
- **API Types** (`types/api.ts`): Request/response interfaces
- **UI Types** (`types/ui.ts`): Component prop interfaces
- **Main Types** (`types.ts`): Core business logic types

## 🎨 UI/UX Design

### Styling
- **Tailwind CSS** for utility-first styling
- **Responsive design** with mobile-first approach
- **Consistent design system** with reusable components
- **Loading states** and **error handling** throughout

### User Experience
- **Progressive loading** with skeleton screens
- **Clear error messages** with actionable feedback
- **Form validation** with real-time feedback
- **Accessible** interface with proper ARIA labels

## 🔧 Development

### Prerequisites
```bash
npm install
```

### Available Scripts
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
```

### Code Quality
- **ESLint** configuration for code consistency
- **TypeScript** strict mode for type safety
- **Component decomposition** following SRP
- **Error boundaries** for graceful error handling

## 🚀 Performance Optimizations

### Bundle Optimization
- **Tree shaking** for minimal bundle size
- **Dynamic imports** for code splitting
- **Asset optimization** with Vite

### Runtime Performance
- **React.memo** for component memoization where appropriate
- **Custom hooks** for logic reuse and optimization
- **Efficient re-renders** with proper state management

## 🧪 Testing Strategy

Testing infrastructure is set up but currently excluded from build:
- **Jest** and **React Testing Library** configuration
- **Test utilities** for consistent test setup
- **Mock factories** for test data generation
- **Component testing** patterns established

## 🔄 API Integration

### Endpoints Used
- `GET /api/config` - Load application configuration
- `PUT /api/config` - Update configuration
- `POST /api/run` - Execute trading strategies
- `POST /api/recommendations/analyze` - Run backtesting analysis
- `GET /api/recommendations/current-positions` - Get portfolio data
- `GET /api/recommendations/market-alerts` - Get market alerts

### Error Handling
- **Automatic retry** with exponential backoff
- **User-friendly error messages** based on HTTP status
- **Network error detection** and fallback handling
- **Loading states** during API calls

## 📈 Future Enhancements

### Planned Features
1. **Real-time data streaming** with WebSocket integration
2. **Advanced charting** with interactive visualizations
3. **User authentication** and personalized settings
4. **Push notifications** for important alerts
5. **Offline support** with service workers

### Technical Improvements
1. **Complete test coverage** with unit and integration tests
2. **Storybook** for component documentation
3. **Performance monitoring** with analytics
4. **Progressive Web App** capabilities
5. **Internationalization** support

## 🔗 Related Documentation

- [Backend API Documentation](../backend/README.md)
- [Main Project Documentation](../CLAUDE.md)
- [Trading Strategies Guide](../strategies/README.md)

---

This frontend provides a comprehensive, type-safe, and user-friendly interface for the Trading MVP platform, following modern React development practices and providing excellent developer experience.