// frontend/src/components/ui/Avatar.tsx
import React from 'react';
import { cn, getAvatarColor } from '../../lib/utils';

interface AvatarProps {
  src?: string;
  alt?: string;
  name?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  fallbackClassName?: string;
}

export function Avatar({ 
  src, 
  alt, 
  name = '',
  size = 'md',
  className,
  fallbackClassName 
}: AvatarProps) {
  const sizes = {
    sm: 'w-6 h-6 text-xs',
    md: 'w-8 h-8 text-sm',
    lg: 'w-12 h-12 text-base'
  };

  const getInitials = (name: string) => {
    if (!name) return '?';
    
    return name
      .trim()
      .split(' ')
      .slice(0, 2)
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase();
  };

  const initials = getInitials(name);
  const avatarColor = getAvatarColor(name || 'default');

  // If image source provided, try to load it
  if (src) {
    return (
      <img
        src={src}
        alt={alt || name || 'User avatar'}
        className={cn(
          'rounded-full object-cover',
          sizes[size],
          className
        )}
        onError={(e) => {
          // If image fails to load, hide it and show fallback
          e.currentTarget.style.display = 'none';
        }}
      />
    );
  }

  // Fallback to initials
  return (
    <div
      className={cn(
        'rounded-full flex items-center justify-center font-medium',
        sizes[size],
        avatarColor,
        'text-white',
        fallbackClassName,
        className
      )}
      role="img"
      aria-label={name || 'User avatar'}
    >
      {initials}
    </div>
  );
}