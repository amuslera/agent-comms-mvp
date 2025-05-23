import React from 'react';

export const App: React.FC = () => {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Test App Component</h1>
      <p>If you can see this, React is working!</p>
      <ul>
        <li>Dashboard: <a href="/">Home</a></li>
        <li>Agents: <a href="/agents">Agents</a></li>
        <li>History: <a href="/history">History</a></li>
      </ul>
    </div>
  );
};

export default App;