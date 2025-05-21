import React from 'react';

export const ScrollArea = ({ children, className }: any) => <div className={className} style={{ overflow: 'auto', maxHeight: 400 }}>{children}</div>;

// For default import compatibility
const Stub = () => null;
export default Stub; 