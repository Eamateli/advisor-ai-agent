// frontend/src/pages/ProfilePage.tsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Avatar } from '../components/ui/Avatar';
import { useAuth } from '../store/auth';
import { formatDate } from '../lib/utils';

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  if (!user) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <div className="text-center">
          <p className="text-muted-foreground">User not found</p>
          <Button onClick={() => navigate('/')} className="mt-4">
            Go to Chat
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Profile</h1>
        <p className="text-muted-foreground mt-2">
          Your account information and preferences
        </p>
      </div>

      {/* Profile Card */}
      <div className="bg-card border rounded-lg p-6">
        <div className="flex items-start gap-6">
          <Avatar
            src={user.profile_picture}
            name={user.full_name || user.email}
            size="xl"
          />
          
          <div className="flex-1 space-y-4">
            <div>
              <h2 className="text-xl font-semibold text-foreground">
                {user.full_name || 'No name set'}
              </h2>
              <p className="text-muted-foreground">{user.email}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <label className="font-medium text-foreground">User ID</label>
                <p className="text-muted-foreground">{user.id}</p>
              </div>
              <div>
                <label className="font-medium text-foreground">Member since</label>
                <p className="text-muted-foreground">
                  {formatDate(user.created_at)}
                </p>
              </div>
              <div>
                <label className="font-medium text-foreground">Google Connected</label>
                <p className="text-muted-foreground">
                  {user.google_connected ? 'Yes' : 'No'}
                </p>
              </div>
              <div>
                <label className="font-medium text-foreground">HubSpot Connected</label>
                <p className="text-muted-foreground">
                  {user.hubspot_connected ? 'Yes' : 'No'}
                </p>
              </div>
            </div>

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => navigate('/settings')}>
                Edit Profile
              </Button>
              <Button variant="outline" onClick={() => navigate('/settings')}>
                Settings
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Integration Status */}
      <div className="bg-card border rounded-lg p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">
          Integration Status
        </h3>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-foreground">Gmail Integration</span>
            <span className={`text-sm px-2 py-1 rounded ${
              user.google_connected 
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
            }`}>
              {user.google_connected ? 'Connected' : 'Not Connected'}
            </span>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-foreground">HubSpot Integration</span>
            <span className={`text-sm px-2 py-1 rounded ${
              user.hubspot_connected 
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
            }`}>
              {user.hubspot_connected ? 'Connected' : 'Not Connected'}
            </span>
          </div>
        </div>

        {(!user.google_connected || !user.hubspot_connected) && (
          <div className="mt-4 p-4 bg-muted/50 rounded-lg">
            <p className="text-sm text-muted-foreground">
              Connect your integrations to get the most out of the AI assistant.
            </p>
            <Button 
              variant="outline" 
              size="sm" 
              className="mt-2"
              onClick={() => navigate('/settings')}
            >
              Manage Integrations
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}