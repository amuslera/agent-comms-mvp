import React from 'react';

export default function SimpleHistory() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Simple History Test</h1>
      <div className="bg-white p-4 rounded shadow">
        <p>This is a simple test page to verify routing is working.</p>
        <p>If you can see this, the routing is fine and the issue is in the main history component.</p>
      </div>
    </div>
  );
}