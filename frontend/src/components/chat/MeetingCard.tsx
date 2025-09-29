// frontend/src/components/chat/MeetingCard.tsx
import React from 'react';
import { cn } from '../../lib/utils';
import { CalendarIcon, ClockIcon } from '@heroicons/react/24/outline';
import { Avatar } from '../ui/Avatar';

interface Meeting {
  id: string;
  title: string;
  start: string;
  end: string;
  attendees?: Array<{
    name: string;
    email: string;
    avatar?: string;
  }>;
  location?: string;
  description?: string;
}

interface MeetingCardProps {
  meeting: Meeting;
  className?: string;
}

export function MeetingCard({ meeting, className }: MeetingCardProps) {
  const startDate = new Date(meeting.start);
  const endDate = new Date(meeting.end);
  
  const dayNumber = startDate.getDate();
  const dayName = startDate.toLocaleDateString('en-US', { weekday: 'long' });
  
  const formatTime = (date: Date) => {
    const hours = date.getHours();
    const minutes = date.getMinutes();
    const ampm = hours >= 12 ? 'pm' : 'am';
    const displayHours = hours % 12 || 12;
    const displayMinutes = minutes < 10 ? `0${minutes}` : minutes;
    return minutes === 0 ? `${displayHours}${ampm}` : `${displayHours}:${displayMinutes}${ampm}`;
  };
  
  const timeRange = `${formatTime(startDate)} – ${formatTime(endDate)}`;

  return (
    <div className={cn(
      'meeting-card group cursor-pointer',
      'bg-card border border-border rounded-xl p-4',
      'hover:shadow-lg hover:border-primary/20 transition-all duration-200',
      className
    )}>
      <div className="flex items-baseline gap-2 mb-3 text-sm">
        <span className="font-semibold text-foreground">{dayNumber}</span>
        <span className="font-medium text-foreground">{dayName}</span>
      </div>

      <div className="flex items-center gap-2 mb-2 text-sm text-muted-foreground">
        <ClockIcon className="w-4 h-4" />
        <span>{timeRange}</span>
      </div>

      <h3 className="font-semibold text-base text-foreground mb-3 group-hover:text-primary transition-colors">
        {meeting.title}
      </h3>

      {meeting.attendees && meeting.attendees.length > 0 && (
        <div className="flex items-center gap-1">
          {meeting.attendees.slice(0, 5).map((attendee, index) => (
            <Avatar
              key={attendee.email}
              name={attendee.name}
              src={attendee.avatar}
              size="sm"
              className={cn(
                'ring-2 ring-background',
                index > 0 && '-ml-2'
              )}
            />
          ))}
          {meeting.attendees.length > 5 && (
            <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-xs font-medium text-muted-foreground -ml-2 ring-2 ring-background">
              +{meeting.attendees.length - 5}
            </div>
          )}
        </div>
      )}

      {meeting.location && (
        <div className="mt-2 text-xs text-muted-foreground">
          📍 {meeting.location}
        </div>
      )}
    </div>
  );
}