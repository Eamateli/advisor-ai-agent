// frontend/src/lib/theme.tsx - FINAL FIX
import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from 'react';
import { SunIcon, MoonIcon, ComputerDesktopIcon } from '@heroicons/react/24/outline';
import { cn } from './utils';
import { themeConfig } from './config';

type Theme = 'dark' | 'light' | 'system';

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: Theme;
  storageKey?: string;
}

interface ThemeProviderState {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  resolvedTheme: 'dark' | 'light';
}

const initialState: ThemeProviderState = {
  theme: 'dark',
  setTheme: () => null,
  resolvedTheme: 'dark',
};

const ThemeProviderContext = createContext<ThemeProviderState>(initialState);

export function ThemeProvider({
  children,
  defaultTheme = 'dark',
  storageKey = themeConfig.storageKey,
  ...props
}: ThemeProviderProps) {
  const [theme, setTheme] = useState<Theme>(
    () => (localStorage.getItem(storageKey) as Theme) || defaultTheme
  );

  const [resolvedTheme, setResolvedTheme] = useState<'dark' | 'light'>('dark');

  useEffect(() => {
    const root = window.document.documentElement;
    const isDark = 
      theme === 'dark' || 
      (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);

    root.classList.remove('light', 'dark');
    root.classList.add(isDark ? 'dark' : 'light');
    setResolvedTheme(isDark ? 'dark' : 'light');
  }, [theme]);

  // Listen for system theme changes when using 'system' theme
  useEffect(() => {
    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      
      const handleChange = () => {
        const isDark = mediaQuery.matches;
        const root = window.document.documentElement;
        root.classList.remove('light', 'dark');
        root.classList.add(isDark ? 'dark' : 'light');
        setResolvedTheme(isDark ? 'dark' : 'light');
      };

      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, [theme]);

  // ✅ FIX: Use useCallback to memoize setTheme function
  const handleSetTheme = useCallback((newTheme: Theme) => {
    localStorage.setItem(storageKey, newTheme);
    setTheme(newTheme);
  }, [storageKey]);

  // ✅ FIX: Use useMemo to memoize the context value
  const value = useMemo(() => ({
    theme,
    setTheme: handleSetTheme,
    resolvedTheme,
  }), [theme, handleSetTheme, resolvedTheme]);

  return (
    <ThemeProviderContext.Provider {...props} value={value}>
      {children}
    </ThemeProviderContext.Provider>
  );
}

// Hook to use theme context
export const useTheme = () => {
  const context = useContext(ThemeProviderContext);

  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }

  return context;
};

// ThemeToggle Component - Used in settings and other places
export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  const themes: { value: Theme; label: string; icon: React.ComponentType<any> }[] = [
    { value: 'light', label: 'Light', icon: SunIcon },
    { value: 'dark', label: 'Dark', icon: MoonIcon },
    { value: 'system', label: 'System', icon: ComputerDesktopIcon },
  ];

  return (
    <div className="flex items-center gap-1 p-1 bg-muted rounded-lg">
      {themes.map(({ value, label, icon: Icon }) => (
        <button
          key={value}
          onClick={() => setTheme(value)}
          className={cn(
            'flex items-center gap-2 px-3 py-1.5 text-sm rounded-md transition-colors',
            theme === value
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          )}
          title={`Switch to ${label} theme`}
          aria-label={`Switch to ${label} theme`}
        >
          <Icon className="w-4 h-4" />
          <span className="hidden sm:inline">{label}</span>
        </button>
      ))}
    </div>
  );
}

// Simple ThemeToggle button (icon only) - Can be used in compact spaces like header
export function ThemeToggleSimple() {
  const { theme, setTheme, resolvedTheme } = useTheme();

  const toggleTheme = useCallback(() => {
    // Simple toggle between light and dark
    setTheme(theme === 'dark' ? 'light' : 'dark');
  }, [theme, setTheme]);

  const Icon = resolvedTheme === 'dark' ? MoonIcon : SunIcon;

  return (
    <button
      onClick={toggleTheme}
      className={cn(
        'inline-flex items-center justify-center',
        'w-9 h-9 rounded-md',
        'text-muted-foreground hover:text-foreground',
        'hover:bg-accent',
        'transition-colors',
        'focus:outline-none focus:ring-2 focus:ring-primary/20'
      )}
      title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      aria-label="Toggle theme"
    >
      <Icon className="w-5 h-5" />
    </button>
  );
}