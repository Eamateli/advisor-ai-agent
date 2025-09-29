// frontend/src/components/layout/AppLayout.tsx - FIXED
import React from 'react';
import { cn } from '../../lib/utils';
import { useSidebarOpen, useAppStore } from '../../store/app';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  // ✅ FIXED: Use individual selectors
  const sidebarOpen = useSidebarOpen();
  const setSidebarOpen = useAppStore((state) => state.setSidebarOpen);

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <aside
        className={cn(
          'flex-shrink-0 border-r border-border bg-card transition-all duration-300 ease-in-out',
          sidebarOpen 
            ? 'w-80 translate-x-0' 
            : 'w-0 -translate-x-full md:w-16 md:translate-x-0'
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
    </div>
  );
}