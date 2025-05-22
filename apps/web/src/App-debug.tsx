import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ToastProvider } from './components/ui/use-toast';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Agents from './pages/Agents';
import PlanSubmission from './pages/PlanSubmission';
import MessagesPage from './pages/arch/Messages';

// Test 9: Add ARCH Messages page
export const App: React.FC = () => {
  return (
    <ToastProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="agents" element={<Agents />} />
            <Route path="plans/submit" element={<PlanSubmission />} />
            <Route path="arch/messages" element={<MessagesPage />} />
          </Route>
        </Routes>
      </Router>
    </ToastProvider>
  );
};

export default App;