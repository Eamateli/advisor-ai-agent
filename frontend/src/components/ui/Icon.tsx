// frontend/src/components/ui/Icon.tsx
import React from 'react';
import * as HeroIcons from '@heroicons/react/24/outline';
import { cn } from '../../lib/utils';

type IconName = keyof typeof HeroIcons;

interface IconProps {
  name: IconName;
  className?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
}

const sizeClasses = {
  xs: 'w-3 h-3',
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
  xl: 'w-8 h-8',
};

export function Icon({ name, className, size = 'md' }: IconProps) {
  const IconComponent = HeroIcons[name] as React.ComponentType<{ className?: string }>;
  
  if (!IconComponent) {
    console.warn(`Icon "${name}" not found`);
    return null;
  }

  return <IconComponent className={cn(sizeClasses[size], className)} />;
}