import React from 'react';

export const Tabs = ({ children, className }: any) => <div className={className}>{children}</div>;
export const TabsList = ({ children, className }: any) => <div className={className}>{children}</div>;
export const TabsTrigger = ({ children, className, ...props }: any) => <button className={className} {...props}>{children}</button>;
export const TabsContent = ({ children, className }: any) => <div className={className}>{children}</div>;

// For default import compatibility
const Stub = () => null;
export default Stub; 