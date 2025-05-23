import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';

// Simple test components
// const TestHome = () => <div style={{ padding: '20px' }}><h2>Home Page Working!</h2></div>;
const TestAgents = () => <div style={{ padding: '20px' }}><h2>Agents Page Working!</h2></div>;

export const App: React.FC = () => {
  console.log('AppDebug rendering - with Layout');
  
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="agents" element={<TestAgents />} />
        </Route>
      </Routes>
    </Router>
  );
};

export default App;