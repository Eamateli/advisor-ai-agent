// frontend/src/components/ui/Avatar.tsx
import React from 'react';
import { cn } from '../../lib/utils';

interface AvatarProps {
  src?: string;
  name: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  fallbackClassName?: string;
  showBorder?: boolean;
}

export function Avatar({
  src,
  name,
  size = 'md',
  className,
  fallbackClassName,
  showBorder = false,
}: AvatarProps) {
  const sizeClasses = {
    xs: 'w-6 h-6 text-xs',
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-12 h-12 text-base',
    xl: 'w-16 h-16 text-lg',
  };

  // Generate initials from name
  const getInitials = (name: string): string => {
    const parts = name.trim().split(' ');
    if (parts.length === 0) return '?';
    if (parts.length === 1) return parts[0][0].toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  };

  // Generate consistent color from name
  const getColorFromName = (name: string): string => {
    const colors = [
      'bg-red-500',
      'bg-orange-500',
      'bg-amber-500',
      'bg-yellow-500',
      'bg-lime-500',
      'bg-green-500',
      'bg-emerald-500',
      'bg-teal-500',
      'bg-cyan-500',
      'bg-sky-500',
      'bg-blue-500',
      'bg-indigo-500',
      'bg-violet-500',
      'bg-purple-500',
      'bg-fuchsia-500',
      'bg-pink-500',
      'bg-rose-500',
    ];

    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }

    return colors[Math.abs(hash) % colors.length];
  };

  const initials = getInitials(name);
  const bgColor = getColorFromName(name);

  return (
    <div
      className={cn(
        'relative inline-flex items-center justify-center rounded-full flex-shrink-0',
        sizeClasses[size],
        showBorder && 'ring-2 ring-background',
        className
      )}
      title={name}
    >
      {src ? (
        <img
          src={src}
          alt={name}
          className="w-full h-full rounded-full object-cover"
          onError={(e) => {
            // Hide image on error and show fallback
            e.currentTarget.style.display = 'none';
          }}
        />
      ) : (
        <div
          className={cn(
            'flex items-center justify-center w-full h-full rounded-full font-medium text-white',
            bgColor,
            fallbackClassName
          )}
        >
          {initials}
        </div>
      )}
    </div>
  );
}

// Avatar group component for displaying multiple avatars
interface AvatarGroupProps {
  avatars: Array<{
    name: string;
    src?: string;
  }>;
  max?: number;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  className?: string;
}

export function AvatarGroup({
  avatars,
  max = 5,
  size = 'sm',
  className,
}: AvatarGroupProps) {
  const displayAvatars = avatars.slice(0, max);
  const remainingCount = avatars.length - max;

  const sizeClasses = {
    xs: 'w-6 h-6 text-xs -ml-2',
    sm: 'w-8 h-8 text-xs -ml-2',
    md: 'w-10 h-10 text-sm -ml-3',
    lg: 'w-12 h-12 text-base -ml-3',
  };

  return (
    <div className={cn('flex items-center', className)}>
      {displayAvatars.map((avatar, index) => (
        <Avatar
          key={`${avatar.name}-${index}`}
          name={avatar.name}
          src={avatar.src}
          size={size}
          showBorder
          className={index > 0 ? sizeClasses[size] : ''}
        />
      ))}
      
      {remainingCount > 0 && (
        <div
          className={cn(
            'flex items-center justify-center rounded-full bg-muted text-muted-foreground font-medium ring-2 ring-background',
            sizeClasses[size]
          )}
        >
          +{remainingCount}
        </div>
      )}
    </div>
  );
}