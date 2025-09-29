// frontend/src/components/chat/ContextHeader.tsx
import React from 'react';
import { cn } from '../../lib/utils';
import { CalendarIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import { Button } from '../ui/Button';

interface ContextHeaderProps {
  contextLabel?: string;
  startDate?: string;
  endDate?: string;
}

export function ContextHeader({ 
  contextLabel = 'all meetings',
  startDate,
  endDate 
}: ContextHeaderProps) {
  
  const formatDateRange = () => {
    if (!startDate || !endDate) return '';
    
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    const formatDate = (date: Date) => {
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric'
      });
    };
    
    return `${formatDate(start)} – ${formatDate(end)}`;
  };

  const dateRange = formatDateRange();

  return (
    <div className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="max-w-4xl mx-auto px-4 py-3">
        <Button
          variant="ghost"
          size="sm"
          className={cn(
            'h-auto py-2 px-3 flex flex-col items-start gap-0.5',
            'hover:bg-muted/50 transition-colors'
          )}
        >
          <div className="flex items-center gap-2 w-full">
            <CalendarIcon className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">
              Context set to {contextLabel}
            </span>
            <ChevronDownIcon className="w-4 h-4 text-muted-foreground ml-auto" />
          </div>
          {dateRange && (
            <span className="text-xs text-muted-foreground/70 ml-6">
              {dateRange}
            </span>
          )}
        </Button>
      </div>
    </div>
  );
}