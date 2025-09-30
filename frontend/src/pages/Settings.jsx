import React, { useState } from "react";
import { User, Globe, Bell, Shield, Save, Mail, Building, MapPin } from "lucide-react";
import Layout from "../components/Layout";
import Card from "../components/Card";

const Settings = () => {
  const [profile, setProfile] = useState({
    name: "Dr. Sarah Chen",
    email: "sarah.chen@marine-institute.org",
    role: "Marine Biologist",
    institution: "Marine Research Institute",
    location: "California, USA"
  });

  const [preferences, setPreferences] = useState({
    notifications: true,
    emailUpdates: true,
    dataSharing: "open"
  });

  const handleProfileChange = (field) => (e) => {
    setProfile(prev => ({ ...prev, [field]: e.target.value }));
  };

  const handlePreferenceChange = (field) => (e) => {
    const value = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    setPreferences(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    alert("Settings saved successfully!");
  };

  return (
    <Layout title="Settings">
      <div className="max-w-4xl mx-auto space-y-6">
        <Card title="Profile Information" subtitle="Update your personal and professional details">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Full Name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  value={profile.name}
                  onChange={handleProfileChange("name")}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="email"
                  value={profile.email}
                  onChange={handleProfileChange("email")}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        </Card>
        <div className="flex justify-end">
          <button
            onClick={handleSave}
            className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors shadow-md hover:shadow-lg"
          >
            <Save className="h-5 w-5" />
            <span>Save Changes</span>
          </button>
        </div>
      </div>
    </Layout>
  );
};

export default Settings;
