import React, { useState } from 'react';
import { User, Key, Globe, Bell, Shield, Save, RefreshCcw } from 'lucide-react';
import Layout from '../components/Layout';
import Card from '../components/Card';
import { Input, Select, Switch } from '../components/FormInputs';
import Badge from '../components/Badge';

const Settings = () => {
  const [activeTab, setActiveTab] = useState('profile');
  const [profile, setProfile] = useState({
    name: 'Dr. Sarah Chen',
    email: 'sarah.chen@university.edu',
    role: 'Marine Biologist',
    institution: 'Ocean Research Institute',
    timezone: 'UTC-08:00'
  });

  const [preferences, setPreferences] = useState({
    theme: 'light',
    notifications: true,
    emailNotifications: true,
    autoRefresh: true,
    dataRetention: '90',
    defaultPageSize: '10'
  });

  const [apiSettings, setApiSettings] = useState({
    baseUrl: 'https://api.edna-dashboard.org/v1',
    apiKey: 'sk-1234567890abcdef...',
    timeout: '30',
    rateLimitPerHour: '1000'
  });

  const tabs = [
    { id: 'profile', name: 'Profile', icon: User },
    { id: 'preferences', name: 'Preferences', icon: Globe },
    { id: 'notifications', name: 'Notifications', icon: Bell },
    { id: 'api', name: 'API Settings', icon: Key },
    { id: 'security', name: 'Security', icon: Shield }
  ];

  const handleProfileChange = (field) => (e) => {
    setProfile(prev => ({ ...prev, [field]: e.target.value }));
  };

  const handlePreferenceChange = (field) => (value) => {
    setPreferences(prev => ({ ...prev, [field]: value }));
  };

  const handleApiChange = (field) => (e) => {
    setApiSettings(prev => ({ ...prev, [field]: e.target.value }));
  };

  const saveSettings = () => {
    // In a real app, this would make an API call
    console.log('Saving settings...', { profile, preferences, apiSettings });
    alert('Settings saved successfully!');
  };

  const testApiConnection = () => {
    // Mock API test
    alert('API connection test successful!');
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'profile':
        return (
          <div className="space-y-6">
            <Card title="Profile Information" subtitle="Update your personal information">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Input
                  label="Full Name"
                  value={profile.name}
                  onChange={handleProfileChange('name')}
                />
                <Input
                  label="Email Address"
                  type="email"
                  value={profile.email}
                  onChange={handleProfileChange('email')}
                />
                <Input
                  label="Role/Title"
                  value={profile.role}
                  onChange={handleProfileChange('role')}
                />
                <Input
                  label="Institution"
                  value={profile.institution}
                  onChange={handleProfileChange('institution')}
                />
                <Select
                  label="Timezone"
                  value={profile.timezone}
                  onChange={handleProfileChange('timezone')}
                  options={[
                    { value: 'UTC-12:00', label: 'UTC-12:00 (Baker Island)' },
                    { value: 'UTC-08:00', label: 'UTC-08:00 (Pacific Time)' },
                    { value: 'UTC-05:00', label: 'UTC-05:00 (Eastern Time)' },
                    { value: 'UTC+00:00', label: 'UTC+00:00 (GMT)' },
                    { value: 'UTC+01:00', label: 'UTC+01:00 (Central European)' },
                    { value: 'UTC+09:00', label: 'UTC+09:00 (Japan Standard)' }
                  ]}
                />
              </div>
            </Card>

            <Card title="Account Status">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">Account Type</p>
                  <p className="text-sm text-gray-600">Research Professional</p>
                </div>
                <Badge variant="success">Active</Badge>
              </div>
              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-sm text-gray-600">
                  Member since: January 15, 2024
                </p>
                <p className="text-sm text-gray-600">
                  Last login: {new Date().toLocaleDateString()}
                </p>
              </div>
            </Card>
          </div>
        );

      case 'preferences':
        return (
          <div className="space-y-6">
            <Card title="Display Preferences">
              <div className="space-y-4">
                <Select
                  label="Theme"
                  value={preferences.theme}
                  onChange={(e) => handlePreferenceChange('theme')(e.target.value)}
                  options={[
                    { value: 'light', label: 'Light' },
                    { value: 'dark', label: 'Dark' },
                    { value: 'auto', label: 'System' }
                  ]}
                />
                <Select
                  label="Default Page Size"
                  value={preferences.defaultPageSize}
                  onChange={(e) => handlePreferenceChange('defaultPageSize')(e.target.value)}
                  options={[
                    { value: '5', label: '5 items per page' },
                    { value: '10', label: '10 items per page' },
                    { value: '25', label: '25 items per page' },
                    { value: '50', label: '50 items per page' }
                  ]}
                />
              </div>
            </Card>

            <Card title="Data Management">
              <div className="space-y-4">
                <Select
                  label="Data Retention Period"
                  value={preferences.dataRetention}
                  onChange={(e) => handlePreferenceChange('dataRetention')(e.target.value)}
                  options={[
                    { value: '30', label: '30 days' },
                    { value: '90', label: '90 days' },
                    { value: '180', label: '6 months' },
                    { value: '365', label: '1 year' },
                    { value: 'forever', label: 'Keep forever' }
                  ]}
                />
                <Switch
                  label="Auto-refresh data"
                  checked={preferences.autoRefresh}
                  onChange={handlePreferenceChange('autoRefresh')}
                />
              </div>
            </Card>
          </div>
        );

      case 'notifications':
        return (
          <div className="space-y-6">
            <Card title="Notification Preferences">
              <div className="space-y-4">
                <Switch
                  label="Enable notifications"
                  checked={preferences.notifications}
                  onChange={handlePreferenceChange('notifications')}
                />
                <Switch
                  label="Email notifications"
                  checked={preferences.emailNotifications}
                  onChange={handlePreferenceChange('emailNotifications')}
                />
              </div>
            </Card>

            <Card title="Email Notifications">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">New sequences detected</p>
                    <p className="text-sm text-gray-600">Get notified when new sequences are analyzed</p>
                  </div>
                  <Switch checked={true} onChange={() => {}} />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">Novel taxa discovered</p>
                    <p className="text-sm text-gray-600">Get alerted when potentially novel taxa are found</p>
                  </div>
                  <Switch checked={true} onChange={() => {}} />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">Analysis complete</p>
                    <p className="text-sm text-gray-600">Receive updates when batch analysis is finished</p>
                  </div>
                  <Switch checked={false} onChange={() => {}} />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">Weekly summary</p>
                    <p className="text-sm text-gray-600">Get a weekly digest of your research activity</p>
                  </div>
                  <Switch checked={true} onChange={() => {}} />
                </div>
              </div>
            </Card>
          </div>
        );

      case 'api':
        return (
          <div className="space-y-6">
            <Card 
              title="API Configuration" 
              subtitle="Configure your API endpoints and authentication"
              action={
                <button
                  onClick={testApiConnection}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  <RefreshCcw className="h-4 w-4 mr-2" />
                  Test Connection
                </button>
              }
            >
              <div className="space-y-4">
                <Input
                  label="API Base URL"
                  value={apiSettings.baseUrl}
                  onChange={handleApiChange('baseUrl')}
                  placeholder="https://api.example.com/v1"
                />
                <Input
                  label="API Key"
                  type="password"
                  value={apiSettings.apiKey}
                  onChange={handleApiChange('apiKey')}
                  placeholder="Enter your API key"
                />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Request Timeout (seconds)"
                    type="number"
                    value={apiSettings.timeout}
                    onChange={handleApiChange('timeout')}
                  />
                  <Input
                    label="Rate Limit (requests/hour)"
                    type="number"
                    value={apiSettings.rateLimitPerHour}
                    onChange={handleApiChange('rateLimitPerHour')}
                  />
                </div>
              </div>
            </Card>

            <Card title="API Status">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Connection Status</span>
                  <Badge variant="success">Connected</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Last Request</span>
                  <span className="text-sm font-medium">2 minutes ago</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Requests Today</span>
                  <span className="text-sm font-medium">247 / 1000</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">API Version</span>
                  <span className="text-sm font-medium">v1.2.3</span>
                </div>
              </div>
            </Card>
          </div>
        );

      case 'security':
        return (
          <div className="space-y-6">
            <Card title="Password & Authentication">
              <div className="space-y-4">
                <Input
                  label="Current Password"
                  type="password"
                  placeholder="Enter current password"
                />
                <Input
                  label="New Password"
                  type="password"
                  placeholder="Enter new password"
                />
                <Input
                  label="Confirm New Password"
                  type="password"
                  placeholder="Confirm new password"
                />
                <button className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700">
                  Update Password
                </button>
              </div>
            </Card>

            <Card title="Two-Factor Authentication">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">Two-Factor Authentication</p>
                  <p className="text-sm text-gray-600">Add an extra layer of security to your account</p>
                </div>
                <Badge variant="warning">Not Enabled</Badge>
              </div>
              <div className="mt-4">
                <button className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
                  Enable 2FA
                </button>
              </div>
            </Card>

            <Card title="Active Sessions">
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">Current Session</p>
                    <p className="text-sm text-gray-600">Chrome on macOS • IP: 192.168.1.100</p>
                  </div>
                  <Badge variant="success">Active</Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">Mobile App</p>
                    <p className="text-sm text-gray-600">iOS Safari • IP: 192.168.1.105</p>
                  </div>
                  <button className="text-sm text-red-600 hover:text-red-700">Revoke</button>
                </div>
              </div>
            </Card>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Layout title="Settings">
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Settings</h2>
          <p className="mt-1 text-sm text-gray-600">
            Manage your account settings and preferences
          </p>
        </div>

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar Navigation */}
          <div className="lg:w-64">
            <nav className="space-y-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                      activeTab === tab.id
                        ? 'bg-primary-50 text-primary-700 border-r-2 border-primary-600'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="h-5 w-5 mr-3" />
                    {tab.name}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Main Content */}
          <div className="flex-1">
            {renderTabContent()}
            
            {/* Save Button */}
            <div className="mt-6 flex justify-end space-x-3">
              <button className="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                Reset
              </button>
              <button
                onClick={saveSettings}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
              >
                <Save className="h-4 w-4 mr-2" />
                Save Changes
              </button>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Settings;