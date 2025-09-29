// frontend/src/pages/SettingsPage.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { ThemeToggle } from '../lib/theme';
import { useAuth, useAuthActions } from '../store/auth';
import { useSyncStatus, useSyncActions } from '../store/app';
import { authApi, profileApi, syncApi } from '../services/api';
import { parseErrorMessage } from '../lib/utils';
import toast from 'react-hot-toast';

export default function SettingsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { logout, updateUser } = useAuthActions();
  const syncStatus = useSyncStatus();
  const { updateSyncStatus } = useSyncActions();
  const [connecting, setConnecting] = useState<{[key: string]: boolean}>({});
  const [refreshingStatus, setRefreshingStatus] = useState(false);

  // Fetch current sync status on component mount
  useEffect(() => {
    fetchSyncStatus();
  }, []);

  const fetchSyncStatus = async () => {
    setRefreshingStatus(true);
    try {
      const status = await syncApi.getStatus();
      updateSyncStatus(status);
    } catch (error) {
      console.error('Failed to fetch sync status:', error);
    } finally {
      setRefreshingStatus(false);
    }
  };

  const handleLogout = async () => {
    try {
      await authApi.logout();
      logout();
    } catch (error) {
      // Even if logout fails on server, clear client state
      logout();
    }
  };

  const handleGoogleConnect = async () => {
    setConnecting(prev => ({ ...prev, google: true }));
    
    try {
      const response = await authApi.googleLogin();
      if (response.authorization_url) {
        // Store current page to return after OAuth
        sessionStorage.setItem('oauth_return_url', window.location.pathname);
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
        // Store current page to return after OAuth
        sessionStorage.setItem('oauth_return_url', window.location.pathname);
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

  const handleDisconnect = async (service: 'Gmail' | 'Calendar' | 'HubSpot') => {
    const serviceKey = service.toLowerCase();
    setConnecting(prev => ({ ...prev, [serviceKey]: true }));
    
    try {
      if (service === 'Gmail' || service === 'Calendar') {
        await profileApi.disconnectGoogle();
        
        // Update user state to reflect disconnection
        updateUser({
          google_connected: false,
        });

        // Update sync status for both Gmail and Calendar
        updateSyncStatus({
          gmail: { ...syncStatus.gmail, connected: false },
          calendar: { ...syncStatus.calendar, connected: false },
        });

        toast.success(`Google services disconnected successfully`);
      } else if (service === 'HubSpot') {
        await profileApi.disconnectHubspot();
        
        // Update user state to reflect disconnection
        updateUser({
          hubspot_connected: false,
        });

        // Update sync status
        updateSyncStatus({
          hubspot: { ...syncStatus.hubspot, connected: false },
        });

        toast.success('HubSpot disconnected successfully');
      }
      
      // Refresh status to ensure consistency
      await fetchSyncStatus();
    } catch (error) {
      const errorMessage = parseErrorMessage(error);
      toast.error(`Failed to disconnect ${service}: ${errorMessage}`);
    } finally {
      setConnecting(prev => ({ ...prev, [serviceKey]: false }));
    }
  };

  const triggerSync = async (service: 'gmail' | 'hubspot' | 'calendar') => {
    setConnecting(prev => ({ ...prev, [`sync_${service}`]: true }));
    
    try {
      let result;
      switch (service) {
        case 'gmail':
          result = await syncApi.syncGmail();
          break;
        case 'hubspot':
          result = await syncApi.syncHubspot();
          break;
        case 'calendar':
          result = await syncApi.syncCalendar();
          break;
      }
      
      toast.success(`${service.charAt(0).toUpperCase() + service.slice(1)} sync started`);
      
      // Refresh status after a short delay
      setTimeout(fetchSyncStatus, 2000);
    } catch (error) {
      const errorMessage = parseErrorMessage(error);
      toast.error(`Failed to sync ${service}: ${errorMessage}`);
    } finally {
      setConnecting(prev => ({ ...prev, [`sync_${service}`]: false }));
    }
  };

  const formatLastSync = (lastSync: string | null) => {
    if (!lastSync) return 'Never';
    const date = new Date(lastSync);
    return date.toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'syncing':
        return 'text-yellow-600';
      case 'success':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-muted-foreground';
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Settings</h1>
        <p className="text-muted-foreground mt-2">
          Manage your account and application preferences
        </p>
      </div>

      <div className="space-y-6">
        {/* Account Section */}
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
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-foreground">Integrations</h2>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchSyncStatus}
              loading={refreshingStatus}
            >
              Refresh Status
            </Button>
          </div>
          
          <div className="bg-card border rounded-lg p-6 space-y-6">
            {/* Gmail Integration */}
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-foreground">Gmail</label>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    syncStatus.gmail.connected 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                  }`}>
                    {syncStatus.gmail.connected ? 'Connected' : 'Not connected'}
                  </span>
                </div>
                <div className="text-xs text-muted-foreground space-y-1">
                  <p>Last sync: {formatLastSync(syncStatus.gmail.last_sync)}</p>
                  <p>Status: <span className={getStatusColor(syncStatus.gmail.status)}>{syncStatus.gmail.status}</span></p>
                  {syncStatus.gmail.connected && (
                    <p>Total emails: {syncStatus.gmail.total_emails || 0}</p>
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                {syncStatus.gmail.connected && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => triggerSync('gmail')}
                    loading={connecting.sync_gmail}
                  >
                    Sync Now
                  </Button>
                )}
                <Button 
                  variant="outline" 
                  size="sm"
                  loading={connecting.google || connecting.gmail}
                  onClick={syncStatus.gmail.connected 
                    ? () => handleDisconnect('Gmail')
                    : handleGoogleConnect
                  }
                >
                  {syncStatus.gmail.connected ? 'Disconnect' : 'Connect'}
                </Button>
              </div>
            </div>
            
            {/* Calendar Integration */}
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-foreground">Google Calendar</label>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    syncStatus.calendar.connected 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                  }`}>
                    {syncStatus.calendar.connected ? 'Connected' : 'Not connected'}
                  </span>
                </div>
                <div className="text-xs text-muted-foreground space-y-1">
                  <p>Last sync: {formatLastSync(syncStatus.calendar.last_sync)}</p>
                  <p>Status: <span className={getStatusColor(syncStatus.calendar.status)}>{syncStatus.calendar.status}</span></p>
                  {syncStatus.calendar.connected && (
                    <p>Total events: {syncStatus.calendar.total_events || 0}</p>
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                {syncStatus.calendar.connected && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => triggerSync('calendar')}
                    loading={connecting.sync_calendar}
                  >
                    Sync Now
                  </Button>
                )}
                <Button 
                  variant="outline" 
                  size="sm"
                  loading={connecting.google || connecting.calendar}
                  onClick={syncStatus.calendar.connected 
                    ? () => handleDisconnect('Calendar')
                    : handleGoogleConnect
                  }
                >
                  {syncStatus.calendar.connected ? 'Disconnect' : 'Connect'}
                </Button>
              </div>
            </div>
            
            {/* HubSpot Integration */}
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-foreground">HubSpot</label>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    syncStatus.hubspot.connected 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                  }`}>
                    {syncStatus.hubspot.connected ? 'Connected' : 'Not connected'}
                  </span>
                </div>
                <div className="text-xs text-muted-foreground space-y-1">
                  <p>Last sync: {formatLastSync(syncStatus.hubspot.last_sync)}</p>
                  <p>Status: <span className={getStatusColor(syncStatus.hubspot.status)}>{syncStatus.hubspot.status}</span></p>
                  {syncStatus.hubspot.connected && (
                    <p>Total contacts: {syncStatus.hubspot.total_contacts || 0}</p>
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                {syncStatus.hubspot.connected && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => triggerSync('hubspot')}
                    loading={connecting.sync_hubspot}
                  >
                    Sync Now
                  </Button>
                )}
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