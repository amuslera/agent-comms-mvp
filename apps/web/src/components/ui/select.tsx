import React from 'react';

interface SelectProps {
  value: string;
  onValueChange: (value: string) => void;
  children: React.ReactNode;
  className?: string;
}

export const Select: React.FC<SelectProps> = ({ 
  value, 
  onValueChange, 
  children,
  className = ''
}) => {
  return (
    <select
      value={value}
      onChange={(e) => onValueChange(e.target.value)}
      className={`block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${className}`}
    >
      {children}
    </select>
  );
};

interface SelectTriggerProps {
  children: React.ReactNode;
  className?: string;
}

export const SelectTrigger: React.FC<SelectTriggerProps> = ({ 
  children, 
  className = '' 
}) => {
  return (
    <div className={`relative ${className}`}>
      {children}
    </div>
  );
};

interface SelectContentProps {
  children: React.ReactNode;
  className?: string;
  position?: 'popper' | 'item-aligned';
  side?: 'top' | 'bottom';
  align?: 'start' | 'center' | 'end';
}

export const SelectContent: React.FC<SelectContentProps> = ({ 
  children, 
  className = '',
  position = 'popper',
  // side and align are kept in the interface for future use
  side = 'bottom',
  align = 'start',
}) => {
  return (
    <div 
      className={`
        absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg 
        ${position === 'popper' ? 'min-w-[var(--radix-select-trigger-width)]' : ''}
        ${className}
      `}
    >
      {children}
    </div>
  );
};

interface SelectItemProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

export const SelectItem: React.FC<SelectItemProps> = ({ 
  value, 
  children,
  className = '',
}) => {
  return (
    <option 
      value={value} 
      className={`px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer ${className}`}
    >
      {children}
    </option>
  );
};

export default {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
};
