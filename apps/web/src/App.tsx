import React from 'react';
import { BrowserRouter as Router, Routes, Route, Outlet } from 'react-router-dom';
import { ToastProvider } from './components/ui/use-toast';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Agents from './pages/Agents';
import PlanSubmission from './pages/PlanSubmission';
import { PlanView } from './pages/PlanView';

// Wrapper component that provides the Layout with Outlet for nested routes
const LayoutWrapper = () => (
  <Layout>
    <Outlet />
  </Layout>
);

export const App: React.FC = () => {
  return (
    <ToastProvider>
      <Router>
        <Routes>
          <Route path="/" element={<LayoutWrapper />}>
            <Route index element={<Dashboard />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="agents" element={<Agents />} />
            <Route path="plans/submit" element={<PlanSubmission />} />
          </Route>
          <Route path="/plans/view/:planId" element={<PlanView />} />
        </Routes>
      </Router>
    </ToastProvider>
  );
};

export default App;
