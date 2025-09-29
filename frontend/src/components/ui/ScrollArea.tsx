// frontend/src/components/ui/ScrollArea.tsx
import React from 'react';
import { cn } from '../../lib/utils';

interface ScrollAreaProps {
  children: React.ReactNode;
  className?: string;
  orientation?: 'vertical' | 'horizontal' | 'both';
}

export function ScrollArea({ 
  children, 
  className,
  orientation = 'vertical'
}: ScrollAreaProps) {
  const scrollClasses = {
    vertical: 'overflow-y-auto overflow-x-hidden',
    horizontal: 'overflow-x-auto overflow-y-hidden',
    both: 'overflow-auto',
  };

  return (
    <div
      className={cn(
        'relative',
        scrollClasses[orientation],
        className
      )}
    >
      {children}
    </div>
  );
}