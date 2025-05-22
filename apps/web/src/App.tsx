import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ToastProvider } from './components/ui/use-toast';
import { ErrorBoundary } from './components/ErrorBoundary';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Agents from './pages/Agents';
import PlanSubmission from './pages/PlanSubmission';
import MessagesPage from './pages/arch/Messages';
import PlanPage from './app/plan/page';
import HistoryPage from './app/history/page';

// Temporary simple PlanView without ReactFlow to avoid the error
const SimplePlanView: React.FC = () => {
  return (
    <div style={{ padding: '20px' }}>
      <h1>Plan View</h1>
      <p>Plan visualization will be available once ReactFlow issues are resolved.</p>
      <p>For now, you can use the other pages:</p>
      <ul>
        <li>Dashboard - System overview</li>
        <li>Agents - Agent management</li>
        <li>Submit Plan - Create new plans</li>
        <li>ARCH Messages - View communications</li>
      </ul>
    </div>
  );
};

// Define a fallback component for errors
interface ErrorFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
}

const ErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetErrorBoundary }) => (
  <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
    <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-md text-center">
      <h2 className="text-2xl font-bold text-red-600 mb-4">Application Error</h2>
      <p className="text-gray-700 mb-2">Something went wrong in the application.</p>
      <pre className="text-sm text-red-500 bg-red-50 p-3 rounded mb-4 overflow-auto max-h-40">
        {error.message}
      </pre>
      <div className="space-y-2">
        <button
          onClick={resetErrorBoundary}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
        >
          Try Again
        </button>
        <button
          onClick={() => window.location.reload()}
          className="w-full bg-gray-200 text-gray-800 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors"
        >
          Reload Application
        </button>
      </div>
    </div>
  </div>
);

export const App: React.FC = () => {
  return (
    <ErrorBoundary
      fallback={
        <ErrorFallback 
          error={new Error('An unexpected error occurred')} 
          resetErrorBoundary={() => window.location.reload()} 
        />
      }
    >
      <ToastProvider>
        <Router>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="agents" element={<Agents />} />
              <Route path="plans/submit" element={<PlanSubmission />} />
              <Route path="history" element={<HistoryPage />} />
              <Route path="arch/messages" element={<MessagesPage />} />
            </Route>
            <Route path="/plans/view/:planId" element={<SimplePlanView />} />
            <Route path="/plan" element={<PlanPage />} />
          </Routes>
        </Router>
      </ToastProvider>
    </ErrorBoundary>
  );
};

export default App;