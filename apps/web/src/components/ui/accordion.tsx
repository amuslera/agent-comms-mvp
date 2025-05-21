import React from 'react';

export const Accordion = ({ children, className }: any) => <div className={className}>{children}</div>;
export const AccordionItem = ({ children, className }: any) => <div className={className}>{children}</div>;
export const AccordionTrigger = ({ children, className }: any) => <button className={className}>{children}</button>;
export const AccordionContent = ({ children, className }: any) => <div className={className}>{children}</div>;

// For default import compatibility
const Stub = () => null;
export default Stub; 