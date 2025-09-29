// frontend/src/pages/LoginPage.tsx
import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth, useAuthActions } from '../store/auth';
import { config, endpoints } from '../lib/config';
import { Button } from '../components/ui/Button';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { ThemeToggle } from '../lib/theme';
import { parseErrorMessage } from '../lib/utils';
import toast from 'react-hot-toast';
import {
  ChatBubbleLeftRightIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

export default function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { isAuthenticated, isLoading } = useAuth();
  const { login, setLoading } = useAuthActions();
  const [error, setError] = useState<string | null>(null);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Handle OAuth callback
  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const errorParam = searchParams.get('error');

    if (errorParam) {
      setError(`Authentication failed: ${errorParam}`);
      toast.error(`Authentication error: ${errorParam}`);
      return;
    }

    if (code) {
      handleOAuthCallback(code, state);
    }
  }, [searchParams]);

  const handleOAuthCallback = async (code: string, state: string | null) => {
    setLoading(true);
    setError(null);

    try {
      // Verify state for CSRF protection (optional but recommended)
      if (state) {
        const storedState = sessionStorage.getItem('oauth_state');
        if (storedState && state !== storedState) {
          throw new Error('Invalid state parameter - possible CSRF attack');
        }
        sessionStorage.removeItem('oauth_state');
      }

      // Call backend OAuth callback endpoint
      // Backend expects GET /auth/google/callback?code=xxx&state=xxx
      const response = await fetch(
        `${endpoints.auth.googleCallback}?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state || '')}`,
        {
          method: 'GET',
          credentials: 'include', // Include cookies if backend uses them
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Authentication failed' }));
        throw new Error(errorData.detail || errorData.message || 'Authentication failed');
      }

      const data = await response.json();

      // Store auth data using Zustand store
      login({
        access_token: data.access_token,
        token_type: data.token_type || 'bearer',
        user: data.user,
      });

      toast.success('Successfully logged in!');
      
      // Check if there's a return URL from settings
      const returnUrl = sessionStorage.getItem('oauth_return_url');
      sessionStorage.removeItem('oauth_return_url');
      
      navigate(returnUrl || '/', { replace: true });
    } catch (err) {
      console.error('OAuth callback error:', err);
      const errorMessage = parseErrorMessage(err);
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setLoading(true);
    setError(null);

    try {
      // Generate and store state for CSRF protection
      const state = generateRandomString(32);
      sessionStorage.setItem('oauth_state', state);

      // Call backend to get OAuth URL
      // Backend returns { authorization_url: "https://accounts.google.com/..." }
      const response = await fetch(endpoints.auth.google, {
        method: 'GET',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to initiate authentication');
      }

      const data = await response.json();

      if (!data.authorization_url) {
        throw new Error('No authorization URL received from server');
      }

      // Redirect to Google OAuth
      window.location.href = data.authorization_url;
    } catch (err) {
      console.error('Failed to initiate OAuth:', err);
      const errorMessage = parseErrorMessage(err);
      setError(errorMessage);
      toast.error(errorMessage);
      setLoading(false);
      sessionStorage.removeItem('oauth_state');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <LoadingSpinner size="lg" className="mx-auto mb-4" />
          <p className="text-muted-foreground">
            {searchParams.get('code') ? 'Completing authentication...' : 'Redirecting to Google...'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Theme toggle in top right */}
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>

      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="w-full max-w-md space-y-8">
          {/* Header */}
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center">
              <ChatBubbleLeftRightIcon className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-foreground">
              Financial Advisor AI
            </h1>
            <p className="mt-2 text-muted-foreground">
              Your intelligent assistant for managing client relationships
            </p>
          </div>

          {/* Login Card */}
          <div className="bg-card border border-border rounded-2xl p-8 shadow-lg">
            <h2 className="text-xl font-semibold text-foreground mb-6 text-center">
              Sign in to continue
            </h2>

            {/* Error message */}
            {error && (
              <div className="mb-6 bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            {/* Google Login Button */}
            <Button
              onClick={handleGoogleLogin}
              disabled={isLoading}
              className="w-full h-12"
              size="lg"
            >
              <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                <path
                  fill="currentColor"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="currentColor"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="currentColor"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="currentColor"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              Continue with Google
            </Button>

            {/* Features List */}
            <div className="mt-8 pt-6 border-t border-border">
              <p className="text-sm text-muted-foreground mb-4 text-center">
                With your account, you can:
              </p>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-center gap-2">
                  <SparklesIcon className="w-4 h-4 text-primary flex-shrink-0" />
                  <span>Search and analyze your meetings</span>
                </li>
                <li className="flex items-center gap-2">
                  <SparklesIcon className="w-4 h-4 text-primary flex-shrink-0" />
                  <span>Get AI-powered insights from your emails</span>
                </li>
                <li className="flex items-center gap-2">
                  <SparklesIcon className="w-4 h-4 text-primary flex-shrink-0" />
                  <span>Manage contacts from HubSpot</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Privacy Notice */}
          <div className="text-center text-sm text-muted-foreground">
            <p>
              By continuing, you agree to our Terms of Service and Privacy Policy.
            </p>
            <p className="mt-2 text-xs">
              We'll access your Google Calendar and Gmail to provide personalized assistance.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Helper: Generate random string for OAuth state
function generateRandomString(length: number): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  const randomValues = new Uint8Array(length);
  crypto.getRandomValues(randomValues);
  
  for (let i = 0; i < length; i++) {
    result += chars[randomValues[i] % chars.length];
  }
  
  return result;
}