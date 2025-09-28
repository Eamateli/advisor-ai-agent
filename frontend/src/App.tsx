// frontend/src/App.tsx
import React, { useEffect, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { ThemeProvider } from './lib/theme';
import { useAuthStore } from './store/auth';
import { useAppStore } from './store/app';
import { wsService } from './services/websocket';

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