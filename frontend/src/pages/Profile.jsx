import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { userAPI, datasetAPI } from '../services/api';
import Layout from '../components/Layout';
import Card from '../components/Card';
import Loading from '../components/Loading';
import Badge from '../components/Badge';
import { formatDistanceToNow } from 'date-fns';

// Helper function to safely format dates
const safeFormatDate = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'N/A';
    return formatDistanceToNow(date, { addSuffix: true });
  } catch (error) {
    return 'N/A';
  }
};

const Profile = () => {
  const { user } = useAuth();
  const [profileData, setProfileData] = useState(null);
  const [userDatasets, setUserDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
  });

  useEffect(() => {
    fetchUserProfile();
    fetchUserDatasets();
  }, []);

  const fetchUserProfile = async () => {
    try {
      const data = await userAPI.getProfile();
      setProfileData(data);
      setFormData({
        full_name: data.full_name || '',
        email: data.email || '',
      });
    } catch (error) {
      console.error('Error fetching profile:', error);
      // If API fails, use user from context as fallback
      setProfileData(user);
      setFormData({
        full_name: user?.full_name || '',
        email: user?.email || '',
      });
    }
  };

  const fetchUserDatasets = async () => {
    try {
      setLoading(true);
      // Use user_only=true to get only current user's datasets
      const data = await datasetAPI.getUserDatasets();
      setUserDatasets(data.datasets || []);
    } catch (error) {
      console.error('Error fetching datasets:', error);
      setUserDatasets([]);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await userAPI.updateProfile(formData);
      await fetchUserProfile();
      setEditMode(false);
    } catch (error) {
      console.error('Error updating profile:', error);
      alert('Failed to update profile. Please try again.');
    }
  };

  const handleDownload = async (datasetId, filename) => {
    try {
      const blob = await datasetAPI.downloadDataset(datasetId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading dataset:', error);
      alert('Failed to download dataset. Please try again.');
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      approved: { color: 'green', label: 'Approved' },
      pending: { color: 'yellow', label: 'Pending Review' },
      rejected: { color: 'red', label: 'Rejected' },
    };
    const { color, label } = statusMap[status] || { color: 'gray', label: status };
    return <Badge color={color}>{label}</Badge>;
  };

  if (loading && !profileData) {
    return (
      <Layout>
        <Loading.LoadingOverlay message="Loading profile..." />
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Profile Information */}
        <Card title="Profile Information">
          {!editMode ? (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Username
                  </label>
                  <p className="text-gray-900">{profileData?.username || user?.username}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Full Name
                  </label>
                  <p className="text-gray-900">{profileData?.full_name || 'Not provided'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email
                  </label>
                  <p className="text-gray-900">{profileData?.email || 'Not provided'}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Role
                  </label>
                  <Badge color={user?.role === 'admin' ? 'purple' : 'blue'}>
                    {user?.role === 'admin' ? 'Administrator' : 'User'}
                  </Badge>
                </div>
              </div>
              <div className="flex justify-end mt-6">
                <button
                  onClick={() => setEditMode(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Edit Profile
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Full Name
                  </label>
                  <input
                    type="text"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setEditMode(false);
                    setFormData({
                      full_name: profileData?.full_name || '',
                      email: profileData?.email || '',
                    });
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Save Changes
                </button>
              </div>
            </form>
          )}
        </Card>

        {/* User's Datasets */}
        <Card title="My Uploaded Datasets">
          {loading ? (
            <Loading.LoadingSpinner />
          ) : userDatasets.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>You haven't uploaded any datasets yet.</p>
              <button
                onClick={() => (window.location.href = '/submit')}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Upload Your First Dataset
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Uploaded
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Size
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {userDatasets.map((dataset) => (
                    <tr key={dataset.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {dataset.name}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge color="blue">{dataset.dataset_type}</Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(dataset.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {dataset.created_at
                          ? formatDistanceToNow(new Date(dataset.created_at), {
                              addSuffix: true,
                            })
                          : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {dataset.file_size
                          ? `${(dataset.file_size / 1024 / 1024).toFixed(2)} MB`
                          : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        <button
                          onClick={() => handleDownload(dataset.id, dataset.filename)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Download
                        </button>
                        {dataset.status === 'pending' && (
                          <span className="text-gray-400">• Awaiting approval</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
};

export default Profile;
