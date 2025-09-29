// frontend/src/components/chat/EmptyState.tsx
import React from 'react';
import { cn } from '../../lib/utils';
import { 
  ChatBubbleLeftRightIcon,
  CalendarDaysIcon,
  SparklesIcon 
} from '@heroicons/react/24/outline';

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[400px] px-4">
      <div className="relative mb-6">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
          <ChatBubbleLeftRightIcon className="w-8 h-8 text-white" />
        </div>
        <div className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-yellow-400 flex items-center justify-center">
          <SparklesIcon className="w-4 h-4 text-yellow-900" />
        </div>
      </div>

      <h2 className="text-2xl font-semibold text-foreground mb-2 text-center">
        I can answer questions about your meetings
      </h2>
      
      <p className="text-muted-foreground text-center max-w-md mb-8">
        What do you want to know?
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-3xl">
        <FeatureCard
          icon={<CalendarDaysIcon className="w-5 h-5" />}
          title="Find meetings"
          description="Search by attendees, dates, or topics"
        />
        <FeatureCard
          icon={<ChatBubbleLeftRightIcon className="w-5 h-5" />}
          title="Get summaries"
          description="Quickly recap past conversations"
        />
        <FeatureCard
          icon={<SparklesIcon className="w-5 h-5" />}
          title="Take actions"
          description="Schedule follow-ups and more"
        />
      </div>
    </div>
  );
}

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
}

function FeatureCard({ icon, title, description }: FeatureCardProps) {
  return (
    <div className={cn(
      'flex flex-col items-center text-center p-4',
      'rounded-xl border border-border bg-card',
      'hover:shadow-md transition-all duration-200'
    )}>
      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-3">
        {icon}
      </div>
      <h3 className="font-medium text-foreground mb-1">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
}