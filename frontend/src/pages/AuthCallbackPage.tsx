// frontend/src/pages/AuthCallbackPage.tsx
import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuthActions } from '../store/auth';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { parseErrorMessage } from '../lib/utils';
import toast from 'react-hot-toast';

export default function AuthCallbackPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login, setLoading } = useAuthActions();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = searchParams.get('token');
    const errorParam = searchParams.get('error');

    if (errorParam) {
      setError(`Authentication failed: ${errorParam}`);
      toast.error(`Authentication error: ${errorParam}`);
      navigate('/login', { replace: true });
      return;
    }

    if (token) {
      handleTokenCallback(token);
    } else {
      setError('No authentication token received');
      toast.error('No authentication token received');
      navigate('/login', { replace: true });
    }
  }, [searchParams, navigate]);

  const handleTokenCallback = async (token: string) => {
    setLoading(true);
    setError(null);

    try {
      // Get user info from backend using the token
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1'}/auth/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to get user info' }));
        throw new Error(errorData.detail || errorData.message || 'Failed to get user info');
      }

      const userData = await response.json();

      // Store auth data using Zustand store
      login({
        access_token: token,
        token_type: 'bearer',
        user: userData,
      });

      // Login success - no toast needed
      
      // Check if there's a return URL from settings
      const returnUrl = sessionStorage.getItem('oauth_return_url');
      sessionStorage.removeItem('oauth_return_url');
      
      navigate(returnUrl || '/', { replace: true });
    } catch (err) {
      console.error('Token callback error:', err);
      const errorMessage = parseErrorMessage(err);
      setError(errorMessage);
      toast.error(errorMessage);
      navigate('/login', { replace: true });
    } finally {
      setLoading(false);
    }
  };

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-foreground mb-4">Authentication Error</h1>
          <p className="text-muted-foreground mb-4">{error}</p>
          <button
            onClick={() => navigate('/login')}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center">
        <LoadingSpinner size="lg" />
        <h1 className="text-2xl font-bold text-foreground mt-4">Completing Login...</h1>
        <p className="text-muted-foreground">Please wait while we set up your account.</p>
      </div>
    </div>
  );
}
