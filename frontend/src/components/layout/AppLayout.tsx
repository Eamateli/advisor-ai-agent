// frontend/src/components/layout/AppLayout.tsx - FIXED
import React, { useEffect } from 'react';
import { cn } from '../../lib/utils';
import { useSidebarOpen, useAppStore } from '../../store/app';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { SettingsModal } from '../ui/SettingsModal';

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  // ✅ FIXED: Use individual selectors
  const sidebarOpen = useSidebarOpen();
  const setSidebarOpen = useAppStore((state) => state.setSidebarOpen);
  const settingsOpen = useAppStore((state) => state.settingsOpen);
  const setSettingsOpen = useAppStore((state) => state.setSettingsOpen);

  // Handle responsive behavior - set initial sidebar state based on screen size
  useEffect(() => {
    const handleResize = () => {
      // Only change sidebar state when switching between mobile and desktop
      // Don't force changes when already in the correct state
      if (window.innerWidth >= 768) {
        // Desktop: show full sidebar (true = full sidebar)
        // Only set if not already true to avoid unnecessary re-renders
        if (!sidebarOpen) {
          setSidebarOpen(true);
        }
      }
      // Remove forced mobile behavior - let user control sidebar on mobile
    };

    // Add resize listener
    window.addEventListener('resize', handleResize);
    
    // Set initial state on mount
    handleResize();

    // Cleanup
    return () => window.removeEventListener('resize', handleResize);
  }, [setSidebarOpen, sidebarOpen]);

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <aside
        className={cn(
          'flex-shrink-0 border-r border-border bg-card transition-all duration-300 ease-in-out',
          'fixed md:relative z-50 md:z-auto',
          sidebarOpen 
            ? 'w-80 translate-x-0' 
            : 'w-80 -translate-x-full md:w-16 md:translate-x-0 md:block'
        )}
      >
        <Sidebar />
      </aside>

      {/* Main content area */}
      <div className="flex flex-col flex-1 min-w-0">
        <Header />
        
        <main className="flex-1 overflow-hidden">
          {children}
        </main>
      </div>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Settings Modal */}
      <SettingsModal 
        isOpen={settingsOpen} 
        onClose={() => setSettingsOpen(false)} 
      />
    </div>
  );
}