import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ToastProvider } from './components/ui/use-toast';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Agents from './pages/Agents';
import PlanSubmission from './pages/PlanSubmission';
import MessagesPage from './pages/arch/Messages';
import PlanPage from './app/plan/page';

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
          <Route path="/plans/view/:planId" element={<SimplePlanView />} />
          <Route path="/plan" element={<PlanPage />} />
        </Routes>
      </Router>
    </ToastProvider>
  );
};

export default App;