// frontend/src/pages/SettingsPage.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { ThemeToggle } from '../lib/theme';
import { useAuth, useAuthActions } from '../store/auth';
import { useSyncStatus } from '../store/app';
import { authApi } from '../services/api';
import { parseErrorMessage } from '../lib/utils';
import toast from 'react-hot-toast';

export default function SettingsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { logout } = useAuthActions();
  const syncStatus = useSyncStatus();
  const [connecting, setConnecting] = useState<{[key: string]: boolean}>({});

  const handleLogout = () => {
    logout();
  };

  const handleGoogleConnect = async () => {
    setConnecting(prev => ({ ...prev, google: true }));
    
    try {
      const response = await authApi.googleLogin();
      if (response.authorization_url) {
        // Redirect to Google OAuth
        window.location.href = response.authorization_url;
      } else {
        throw new Error('No authorization URL received');
      }
    } catch (error) {
      const errorMessage = parseErrorMessage(error);
      toast.error(`Failed to connect Google: ${errorMessage}`);
    } finally {
      setConnecting(prev => ({ ...prev, google: false }));
    }
  };

  const handleHubSpotConnect = async () => {
    setConnecting(prev => ({ ...prev, hubspot: true }));
    
    try {
      const response = await authApi.hubspotLogin();
      if (response.authorization_url) {
        // Redirect to HubSpot OAuth
        window.location.href = response.authorization_url;
      } else {
        throw new Error('No authorization URL received');
      }
    } catch (error) {
      const errorMessage = parseErrorMessage(error);
      toast.error(`Failed to connect HubSpot: ${errorMessage}`);
    } finally {
      setConnecting(prev => ({ ...prev, hubspot: false }));
    }
  };

  const handleDisconnect = async (service: string) => {
    // TODO: Implement disconnect endpoints in backend
    toast.error(`Disconnect ${service} not yet implemented`);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Settings</h1>
        <p className="text-muted-foreground mt-2">
          Manage your account and application preferences
        </p>
      </div>

      {/* Account Section */}
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-foreground mb-4">Account</h2>
          <div className="bg-card border rounded-lg p-6 space-y-4">
            <div>
              <label className="text-sm font-medium text-foreground">Email</label>
              <p className="text-muted-foreground">{user?.email}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-foreground">Name</label>
              <p className="text-muted-foreground">{user?.full_name || 'Not set'}</p>
            </div>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => navigate('/profile')}
            >
              Edit Profile
            </Button>
          </div>
        </div>

        {/* Theme Section */}
        <div>
          <h2 className="text-xl font-semibold text-foreground mb-4">Appearance</h2>
          <div className="bg-card border rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-foreground">Theme</label>
                <p className="text-sm text-muted-foreground">
                  Choose your preferred theme
                </p>
              </div>
              <ThemeToggle />
            </div>
          </div>
        </div>

        {/* Integrations Section */}
        <div>
          <h2 className="text-xl font-semibold text-foreground mb-4">Integrations</h2>
          <div className="bg-card border rounded-lg p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-foreground">Gmail</label>
                <p className="text-sm text-muted-foreground">
                  Status: {syncStatus.gmail.connected ? 'Connected' : 'Not connected'}
                </p>
              </div>
              <Button 
                variant="outline" 
                size="sm"
                loading={connecting.google}
                onClick={syncStatus.gmail.connected 
                  ? () => handleDisconnect('Gmail')
                  : handleGoogleConnect
                }
              >
                {syncStatus.gmail.connected ? 'Disconnect' : 'Connect'}
              </Button>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-foreground">Google Calendar</label>
                <p className="text-sm text-muted-foreground">
                  Status: {syncStatus.calendar.connected ? 'Connected' : 'Not connected'}
                </p>
              </div>
              <Button 
                variant="outline" 
                size="sm"
                loading={connecting.google}
                onClick={syncStatus.calendar.connected 
                  ? () => handleDisconnect('Calendar')
                  : handleGoogleConnect
                }
              >
                {syncStatus.calendar.connected ? 'Disconnect' : 'Connect'}
              </Button>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-foreground">HubSpot</label>
                <p className="text-sm text-muted-foreground">
                  Status: {syncStatus.hubspot.connected ? 'Connected' : 'Not connected'}
                </p>
              </div>
              <Button 
                variant="outline" 
                size="sm"
                loading={connecting.hubspot}
                onClick={syncStatus.hubspot.connected 
                  ? () => handleDisconnect('HubSpot')
                  : handleHubSpotConnect
                }
              >
                {syncStatus.hubspot.connected ? 'Disconnect' : 'Connect'}
              </Button>
            </div>
          </div>
        </div>

        {/* Danger Zone */}
        <div>
          <h2 className="text-xl font-semibold text-destructive mb-4">Danger Zone</h2>
          <div className="bg-card border border-destructive/20 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-foreground">Sign Out</label>
                <p className="text-sm text-muted-foreground">
                  Sign out of your account
                </p>
              </div>
              <Button variant="destructive" size="sm" onClick={handleLogout}>
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Settings</h1>
        <p className="text-muted-foreground mt-2">
          Manage your account and application preferences
        </p>
      </div>

      {/* Account Section */}
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-foreground mb-4">Account</h2>
          <div className="bg-card border rounded-lg p-6 space-y-4">
            <div>
              <label className="text-sm font-medium text-foreground">Email</label>
              <p className="text-muted-foreground">{user?.email}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-foreground">Name</label>
              <p className="text-muted-foreground">{user?.full_name || 'Not set'}</p>
            </div>
            <Button variant="outline" size="sm">
              Edit Profile
            </Button>
          </div>
        </div>

        {/* Theme Section */}
        <div>
          <h2 className="text-xl font-semibold text-foreground mb-4">Appearance</h2>
          <div className="bg-card border rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-foreground">Theme</label>
                <p className="text-sm text-muted-foreground">
                  Choose your preferred theme
                </p>
              </div>
              <ThemeToggle />
            </div>
          </div>
        </div>

        {/* Integrations Section */}
        <div>
          <h2 className="text-xl font-semibold text-foreground mb-4">Integrations</h2>
          <div className="bg-card border rounded-lg p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-foreground">Gmail</label>
                <p className="text-sm text-muted-foreground">
                  Status: {syncStatus.gmail.connected ? 'Connected' : 'Not connected'}
                </p>
              </div>
              <Button variant="outline" size="sm">
                {syncStatus.gmail.connected ? 'Disconnect' : 'Connect'}
              </Button>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-foreground">Google Calendar</label>
                <p className="text-sm text-muted-foreground">
                  Status: {syncStatus.calendar.connected ? 'Connected' : 'Not connected'}
                </p>
              </div>
              <Button variant="outline" size="sm">
                {syncStatus.calendar.connected ? 'Disconnect' : 'Connect'}
              </Button>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-foreground">HubSpot</label>
                <p className="text-sm text-muted-foreground">
                  Status: {syncStatus.hubspot.connected ? 'Connected' : 'Not connected'}
                </p>
              </div>
              <Button variant="outline" size="sm">
                {syncStatus.hubspot.connected ? 'Disconnect' : 'Connect'}
              </Button>
            </div>
          </div>
        </div>

        {/* Danger Zone */}
        <div>
          <h2 className="text-xl font-semibold text-destructive mb-4">Danger Zone</h2>
          <div className="bg-card border border-destructive/20 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-foreground">Sign Out</label>
                <p className="text-sm text-muted-foreground">
                  Sign out of your account
                </p>
              </div>
              <Button variant="destructive" size="sm" onClick={handleLogout}>
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}