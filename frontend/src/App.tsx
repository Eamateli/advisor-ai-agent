// frontend/src/App.tsx
import React, { useEffect, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { ThemeProvider } from './lib/theme';
import { useAuthStore } from './store/auth';
import { useAppStore } from './store/app';
import { wsService } from './services/websocket';
import { ErrorBoundary } from './components/ErrorBoundary';

// Layout components
import { AppLayout } from './components/layout/AppLayout';
import { LoadingSpinner } from './components/ui/LoadingSpinner';

// Pages (lazy loaded for better performance)
const ChatPage = React.lazy(() => import('./pages/ChatPage'));
const LoginPage = React.lazy(() => import('./pages/LoginPage'));
const SettingsPage = React.lazy(() => import('./pages/SettingsPage'));
const ProfilePage = React.lazy(() => import('./pages/ProfilePage'));

// Protected route wrapper
interface ProtectedRouteProps {
  children: React.ReactNode;
}

function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated } = useAuthStore();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
}

// Loading fallback component
function PageLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center">
        <LoadingSpinner size="lg" className="mx-auto mb-4" />
        <p className="text-muted-foreground">Loading...</p>
      </div>
    </div>
  );
}

function App() {
  const { isAuthenticated } = useAuthStore();
  const { setOnlineStatus, setWebSocketStatus } = useAppStore();

  // Set up online/offline listeners
  useEffect(() => {
    const handleOnline = () => setOnlineStatus(true);
    const handleOffline = () => setOnlineStatus(false);

    // Set initial online status
    setOnlineStatus(navigator.onLine);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [setOnlineStatus]);

  // Initialize WebSocket connection when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      try {
        const token = localStorage.getItem('access_token');
        if (token) {
          wsService.connect(token);
          setWebSocketStatus(true);
        }
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        setWebSocketStatus(false);
      }

      return () => {
        try {
          wsService.disconnect();
          setWebSocketStatus(false);
        } catch (error) {
          console.error('Error disconnecting WebSocket:', error);
        }
      };
    }
  }, [isAuthenticated, setWebSocketStatus]);

  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="system" storageKey="app-theme">
        <Router>
          <Routes>
            {/* Public route */}
            <Route
              path="/login"
              element={
                <Suspense fallback={<PageLoader />}>
                  <LoginPage />
                </Suspense>
              }
            />

            {/* Protected routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <Suspense fallback={<PageLoader />}>
                      <ChatPage />
                    </Suspense>
                  </AppLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <Suspense fallback={<PageLoader />}>
                      <SettingsPage />
                    </Suspense>
                  </AppLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <Suspense fallback={<PageLoader />}>
                      <ProfilePage />
                    </Suspense>
                  </AppLayout>
                </ProtectedRoute>
              }
            />

            {/* Catch-all redirect */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>

          {/* Toast notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: 'var(--background)',
                color: 'var(--foreground)',
                border: '1px solid var(--border)',
              },
            }}
          />
        </Router>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;