// frontend/src/pages/LoginPage.tsx
import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth, useAuthActions } from '../store/auth';
import { authApi } from '../services/api';
import { Button } from '../components/ui/Button';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { ThemeToggle } from '../lib/theme';
import { parseErrorMessage } from '../lib/utils';
import toast from 'react-hot-toast';

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
    const error = searchParams.get('error');

    if (error) {
      setError('Authentication failed. Please try again.');
      return;
    }

    if (code && state) {
      handleOAuthCallback(code, state);
    }
  }, [searchParams]);

  const handleOAuthCallback = async (code: string, state: string) => {
    setLoading(true);
    setError(null);

    try {
      // The backend should handle the OAuth callback and return user data
      const response = await fetch(`/auth/google/callback?code=${code}&state=${state}`);
      
      if (!response.ok) {
        throw new Error('Authentication failed');
      }

      const data = await response.json();
      
      login({
        access_token: data.access_token,
        token_type: 'bearer',
        user: data.user,
      });

      toast.success('Successfully logged in!');
      navigate('/', { replace: true });
    } catch (err) {
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
      const response = await authApi.googleLogin();
      
      if (response.authorization_url) {
        window.location.href = response.authorization_url;
      } else {
        throw new Error('No authorization URL received');
      }
    } catch (err) {
      const errorMessage = parseErrorMessage(err);
      setError(errorMessage);
      toast.error(errorMessage);
      setLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <LoadingSpinner size="lg" className="mx-auto mb-4" />
          <p className="text-muted-foreground">Authenticating...</p>
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
              <svg
                className="w-8 h-8 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-foreground">
              Financial Advisor AI
            </h1>
            <p className="mt-2 text-muted-foreground">
              Your intelligent assistant for managing client relationships
            </p>
          </div>

          {/* Login form */}
          <div className="space-y-6">
            {error && (
              <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <Button
              onClick={handleGoogleLogin}
              disabled={isLoading}
              className="w-full"
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

            <div className="text-center text-sm text-muted-foreground">
              <p>
                By continuing, you agree to our Terms of Service and Privacy Policy.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}