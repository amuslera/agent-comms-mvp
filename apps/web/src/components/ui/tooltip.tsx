import React from 'react';

interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactElement;
  className?: string;
}

export const Tooltip: React.FC<TooltipProps> = ({ content, children, className = '' }) => {
  const [isVisible, setIsVisible] = React.useState(false);
  
  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
      >
        {children}
      </div>
      {isVisible && (
        <div 
          className={`
            absolute z-10 p-2 text-xs text-white bg-gray-800 rounded 
            shadow-lg whitespace-nowrap ${className}
          `}
          style={{ 
            bottom: '100%',
            left: '50%',
            transform: 'translateX(-50%)',
            marginBottom: '0.5rem',
          }}
        >
          {content}
        </div>
      )}
    </div>
  );
};

export default Tooltip;
