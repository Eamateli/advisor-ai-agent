// frontend/src/pages/SettingsPage.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth, useAuthActions } from '../store/auth';
import { useSyncStatus, useSyncActions } from '../store/app';
import { useTheme } from '../lib/theme';
import { authApi, profileApi, syncApi } from '../services/api';
import { parseErrorMessage } from '../lib/utils';
import { Button } from '../components/ui/Button';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import toast from 'react-hot-toast';
import {
  UserIcon,
  BellIcon,
  ShieldCheckIcon,
  KeyIcon,
  CalendarIcon,
  EnvelopeIcon,
  MoonIcon,
  SunIcon,
  ComputerDesktopIcon,
  CheckIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

type TabId = 'profile' | 'notifications' | 'privacy' | 'integrations';

export default function SettingsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { logout, updateUser } = useAuthActions();
  const syncStatus = useSyncStatus();
  const { updateSyncStatus } = useSyncActions();
  const { theme, setTheme } = useTheme();
  
  const [activeTab, setActiveTab] = useState<TabId>('profile');
  const [isLoading, setIsLoading] = useState(false);
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

  const handleSaveProfile = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const formData = new FormData(e.currentTarget);
      const updates = {
        full_name: formData.get('name') as string,
      };

      updateUser(updates);
      toast.success('Profile updated successfully');
    } catch (error) {
      toast.error('Failed to update profile');
    } finally {
      setIsLoading(false);
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
        
        updateUser({ google_connected: false });
        updateSyncStatus({
          gmail: { ...syncStatus.gmail, connected: false },
          calendar: { ...syncStatus.calendar, connected: false },
        });

        toast.success('Google services disconnected successfully');
      } else if (service === 'HubSpot') {
        await profileApi.disconnectHubspot();
        
        updateUser({ hubspot_connected: false });
        updateSyncStatus({
          hubspot: { ...syncStatus.hubspot, connected: false },
        });

        toast.success('HubSpot disconnected successfully');
      }
      
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
      switch (service) {
        case 'gmail':
          await syncApi.syncGmail();
          break;
        case 'hubspot':
          await syncApi.syncHubspot();
          break;
        case 'calendar':
          await syncApi.syncCalendar();
          break;
      }
      
      toast.success(`${service.charAt(0).toUpperCase() + service.slice(1)} sync started`);
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
    return new Date(lastSync).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'syncing': return 'text-yellow-600';
      case 'idle': return 'text-green-600';
      case 'error': return 'text-red-600';
      default: return 'text-muted-foreground';
    }
  };

  const tabs = [
    { id: 'profile' as const, label: 'Profile', icon: UserIcon },
    { id: 'notifications' as const, label: 'Notifications', icon: BellIcon },
    { id: 'privacy' as const, label: 'Privacy & Security', icon: ShieldCheckIcon },
    { id: 'integrations' as const, label: 'Integrations', icon: KeyIcon },
  ];

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Settings</h1>
          <p className="text-muted-foreground">
            Manage your account preferences and integrations
          </p>
        </div>

        <div className="flex flex-col md:flex-row gap-6">
          {/* Sidebar */}
          <div className="w-full md:w-64 flex-shrink-0">
            <nav className="space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
                    activeTab === tab.id
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-muted'
                  }`}
                >
                  <tab.icon className="w-5 h-5" />
                  <span className="font-medium">{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1">
            <div className="bg-card border border-border rounded-xl p-6">
              {/* Profile Tab */}
              {activeTab === 'profile' && (
                <div>
                  <h2 className="text-xl font-semibold text-foreground mb-6">
                    Profile Information
                  </h2>
                  
                  <form onSubmit={handleSaveProfile} className="space-y-6">
                    {/* Email (read-only) */}
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        Email Address
                      </label>
                      <input
                        type="email"
                        value={user?.email || ''}
                        disabled
                        className="w-full px-4 py-2 rounded-lg border border-border bg-muted text-muted-foreground cursor-not-allowed"
                      />
                      <p className="mt-1 text-xs text-muted-foreground">
                        Email cannot be changed
                      </p>
                    </div>

                    {/* Name */}
                    <div>
                      <label htmlFor="name" className="block text-sm font-medium text-foreground mb-2">
                        Display Name
                      </label>
                      <input
                        type="text"
                        id="name"
                        name="name"
                        defaultValue={user?.full_name || ''}
                        className="w-full px-4 py-2 rounded-lg border border-border bg-background text-foreground focus:ring-2 focus:ring-primary/50 focus:border-primary"
                        placeholder="Your name"
                      />
                    </div>

                    {/* Theme */}
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        Theme
                      </label>
                      <div className="grid grid-cols-3 gap-3">
                        {[
                          { value: 'light', label: 'Light', icon: SunIcon },
                          { value: 'dark', label: 'Dark', icon: MoonIcon },
                          { value: 'system', label: 'System', icon: ComputerDesktopIcon },
                        ].map((option) => (
                          <button
                            key={option.value}
                            type="button"
                            onClick={() => setTheme(option.value as any)}
                            className={`flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all ${
                              theme === option.value
                                ? 'border-primary bg-primary/10'
                                : 'border-border hover:border-primary/50'
                            }`}
                          >
                            <option.icon className="w-6 h-6" />
                            <span className="text-sm font-medium">{option.label}</span>
                            {theme === option.value && (
                              <CheckIcon className="w-4 h-4 text-primary" />
                            )}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Save Button */}
                    <div className="flex justify-end">
                      <Button type="submit" disabled={isLoading}>
                        {isLoading ? (
                          <>
                            <LoadingSpinner size="sm" className="mr-2" />
                            Saving...
                          </>
                        ) : (
                          'Save Changes'
                        )}
                      </Button>
                    </div>
                  </form>
                </div>
              )}

              {/* Notifications Tab */}
              {activeTab === 'notifications' && (
                <div>
                  <h2 className="text-xl font-semibold text-foreground mb-6">
                    Notification Preferences
                  </h2>
                  
                  <div className="space-y-4">
                    <NotificationToggle
                      title="Email Notifications"
                      description="Receive email updates about your meetings and contacts"
                      defaultChecked={true}
                    />
                    <NotificationToggle
                      title="Meeting Reminders"
                      description="Get notified before upcoming meetings"
                      defaultChecked={true}
                    />
                    <NotificationToggle
                      title="New Contact Alerts"
                      description="Notification when new contacts are added"
                      defaultChecked={false}
                    />
                    <NotificationToggle
                      title="Weekly Summary"
                      description="Receive a weekly summary of your activities"
                      defaultChecked={true}
                    />
                  </div>
                </div>
              )}

              {/* Privacy Tab */}
              {activeTab === 'privacy' && (
                <div>
                  <h2 className="text-xl font-semibold text-foreground mb-6">
                    Privacy & Security
                  </h2>
                  
                  <div className="space-y-6">
                    <div>
                      <h3 className="font-medium text-foreground mb-2">Data Access</h3>
                      <p className="text-sm text-muted-foreground mb-4">
                        We access your data to provide personalized assistance. You can revoke access at any time.
                      </p>
                      <div className="space-y-2">
                        <DataAccessItem
                          icon={CalendarIcon}
                          label="Google Calendar"
                          description="Read-only access to your calendar events"
                          isConnected={syncStatus.calendar.connected}
                        />
                        <DataAccessItem
                          icon={EnvelopeIcon}
                          label="Gmail"
                          description="Read-only access to your emails"
                          isConnected={syncStatus.gmail.connected}
                        />
                      </div>
                    </div>

                    <div>
                      <h3 className="font-medium text-foreground mb-2">Sign Out</h3>
                      <p className="text-sm text-muted-foreground mb-4">
                        Sign out of your account on this device.
                      </p>
                      <Button variant="destructive" size="sm" onClick={handleLogout}>
                        Sign Out
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              {/* Integrations Tab */}
              {activeTab === 'integrations' && (
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-semibold text-foreground">
                      Connected Integrations
                    </h2>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={fetchSyncStatus}
                      disabled={refreshingStatus}
                    >
                      {refreshingStatus ? (
                        <LoadingSpinner size="sm" />
                      ) : (
                        <>
                          <ArrowPathIcon className="w-4 h-4 mr-2" />
                          Refresh
                        </>
                      )}
                    </Button>
                  </div>
                  
                  <div className="space-y-4">
                    {/* Gmail */}
                    <IntegrationCard
                      name="Gmail"
                      description="Access to your emails for context"
                      icon={<EnvelopeIcon className="w-6 h-6 text-red-500" />}
                      isConnected={syncStatus.gmail.connected}
                      lastSync={formatLastSync(syncStatus.gmail.last_sync)}
                      status={syncStatus.gmail.status}
                      statusColor={getStatusColor(syncStatus.gmail.status)}
                      stats={`${syncStatus.gmail.total_emails || 0} emails`}
                      onConnect={handleGoogleConnect}
                      onDisconnect={() => handleDisconnect('Gmail')}
                      onSync={() => triggerSync('gmail')}
                      isLoading={connecting.google || connecting.gmail || connecting.sync_gmail}
                    />

                    {/* Calendar */}
                    <IntegrationCard
                      name="Google Calendar"
                      description="Access to your calendar events"
                      icon={<CalendarIcon className="w-6 h-6 text-blue-500" />}
                      isConnected={syncStatus.calendar.connected}
                      lastSync={formatLastSync(syncStatus.calendar.last_sync)}
                      status={syncStatus.calendar.status}
                      statusColor={getStatusColor(syncStatus.calendar.status)}
                      stats={`${syncStatus.calendar.total_events || 0} events`}
                      onConnect={handleGoogleConnect}
                      onDisconnect={() => handleDisconnect('Calendar')}
                      onSync={() => triggerSync('calendar')}
                      isLoading={connecting.google || connecting.calendar || connecting.sync_calendar}
                    />

                    {/* HubSpot */}
                    <IntegrationCard
                      name="HubSpot"
                      description="CRM and contacts management"
                      icon={<KeyIcon className="w-6 h-6 text-orange-500" />}
                      isConnected={syncStatus.hubspot.connected}
                      lastSync={formatLastSync(syncStatus.hubspot.last_sync)}
                      status={syncStatus.hubspot.status}
                      statusColor={getStatusColor(syncStatus.hubspot.status)}
                      stats={`${syncStatus.hubspot.total_contacts || 0} contacts`}
                      onConnect={handleHubSpotConnect}
                      onDisconnect={() => handleDisconnect('HubSpot')}
                      onSync={() => triggerSync('hubspot')}
                      isLoading={connecting.hubspot || connecting.sync_hubspot}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Helper Components
function NotificationToggle({
  title,
  description,
  defaultChecked,
}: {
  title: string;
  description: string;
  defaultChecked: boolean;
}) {
  const [checked, setChecked] = useState(defaultChecked);

  return (
    <div className="flex items-start justify-between py-4 border-b border-border last:border-0">
      <div className="flex-1">
        <h4 className="font-medium text-foreground">{title}</h4>
        <p className="text-sm text-muted-foreground mt-1">{description}</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => setChecked(!checked)}
        className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-2 ${
          checked ? 'bg-primary' : 'bg-muted'
        }`}
      >
        <span
          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
            checked ? 'translate-x-5' : 'translate-x-0'
          }`}
        />
      </button>
    </div>
  );
}

function DataAccessItem({
  icon: Icon,
  label,
  description,
  isConnected,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  description: string;
  isConnected: boolean;
}) {
  return (
    <div className="flex items-center justify-between p-4 rounded-lg border border-border">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
          <Icon className="w-5 h-5 text-primary" />
        </div>
        <div>
          <p className="font-medium text-foreground">{label}</p>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </div>
      {isConnected && (
        <span className="px-3 py-1 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs font-medium">
          Connected
        </span>
      )}
    </div>
  );
}

function IntegrationCard({
  name,
  description,
  icon,
  isConnected,
  lastSync,
  status,
  statusColor,
  stats,
  onConnect,
  onDisconnect,
  onSync,
  isLoading,
}: {
  name: string;
  description: string;
  icon: React.ReactNode;
  isConnected: boolean;
  lastSync?: string;
  status?: string;
  statusColor?: string;
  stats?: string;
  onConnect: () => void;
  onDisconnect: () => void;
  onSync?: () => void;
  isLoading?: boolean;
}) {
  return (
    <div className="flex flex-col gap-4 p-4 rounded-lg border border-border hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg bg-muted flex items-center justify-center">
            {icon}
          </div>
          <div>
            <h4 className="font-medium text-foreground">{name}</h4>
            <p className="text-sm text-muted-foreground">{description}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {isConnected && onSync && (
            <Button
              variant="outline"
              size="sm"
              onClick={onSync}
              disabled={isLoading}
            >
              {isLoading ? <LoadingSpinner size="sm" /> : 'Sync'}
            </Button>
          )}
          <Button
            variant={isConnected ? 'outline' : 'default'}
            size="sm"
            onClick={isConnected ? onDisconnect : onConnect}
            disabled={isLoading}
          >
            {isLoading ? <LoadingSpinner size="sm" /> : isConnected ? 'Disconnect' : 'Connect'}
          </Button>
        </div>
      </div>

      {isConnected && (
        <div className="flex items-center gap-4 text-xs text-muted-foreground pt-2 border-t border-border">
          <span>Last sync: {lastSync}</span>
          <span className="flex items-center gap-1">
            Status: <span className={statusColor}>{status}</span>
          </span>
          {stats && <span>{stats}</span>}
        </div>
      )}
    </div>
  );
}