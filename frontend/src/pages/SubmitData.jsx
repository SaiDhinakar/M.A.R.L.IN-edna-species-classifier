import React, { useState } from 'react';
import { 
  Upload, 
  FileText, 
  MapPin, 
  CheckCircle, 
  AlertCircle,
  Loader
} from 'lucide-react';
import Layout from '../components/Layout';
import Card from '../components/Card';
import { datasetAPI } from '../services/api';

const SubmitData = () => {
  const [formData, setFormData] = useState({
    datasetName: '',
    description: '',
    sampleLocation: '',
    sampleDate: '',
    sampleDepth: '',
    file: null,
  });

  const [errors, setErrors] = useState({});
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    
    if (file) {
      // Validate file size (max 500MB)
      const maxSize = 500 * 1024 * 1024;
      if (file.size > maxSize) {
        setErrors(prev => ({
          ...prev,
          file: 'File size exceeds 500MB limit'
        }));
        return;
      }
      
      // Validate file type
      const validExtensions = ['.fasta', '.fastq', '.fa', '.fq', '.txt', '.tar.gz', '.tgz', '.gz', '.zip'];
      const fileName = file.name.toLowerCase();
      const isValid = validExtensions.some(ext => fileName.endsWith(ext));
      
      if (!isValid) {
        setErrors(prev => ({
          ...prev,
          file: 'Invalid file format. Please upload FASTA, FASTQ, or compressed archive files.'
        }));
        return;
      }
      
      // Clear any previous errors
      setErrors(prev => ({
        ...prev,
        file: ''
      }));
    }
    
    setFormData(prev => ({
      ...prev,
      file: file
    }));
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.datasetName.trim()) {
      newErrors.datasetName = 'Dataset name is required';
    }
    
    if (!formData.file) {
      newErrors.file = 'Please select a file to upload';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setIsSubmitting(true);
    setUploadProgress(0);
    setUploadSuccess(false);
    
    try {
      // Create FormData for file upload
      const uploadData = new FormData();
      uploadData.append('file', formData.file);
      uploadData.append('description', formData.description || '');
      uploadData.append('sample_location', formData.sampleLocation || '');
      uploadData.append('sample_date', formData.sampleDate || '');
      
      if (formData.sampleDepth) {
        uploadData.append('sample_depth', parseFloat(formData.sampleDepth));
      }
      
      // Upload with progress tracking
      await datasetAPI.uploadDataset(uploadData, (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(percentCompleted);
      });
      
      // Success!
      setUploadSuccess(true);
      setUploadProgress(100);
      
      // Reset form after 2 seconds
      setTimeout(() => {
        setFormData({
          datasetName: '',
          description: '',
          sampleLocation: '',
          sampleDate: '',
          sampleDepth: '',
          file: null,
        });
        setUploadProgress(0);
        setUploadSuccess(false);
      }, 2000);
      
    } catch (error) {
      console.error('Upload error:', error);
      setErrors({
        submit: error.response?.data?.detail || 'Failed to upload dataset. Please try again.'
      });
    } finally {
      setIsSubmitting(false);
    }
  };



  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900">Upload Dataset</h2>
          <p className="text-gray-600 mt-2 max-w-2xl mx-auto">
            Upload your environmental DNA samples for analysis. We accept sequence files in various formats.
          </p>
        </div>

        {/* Upload Form */}
        <Card>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* File Upload Area */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sequence File *
              </label>
              <div className="mt-2">
                <label className={`flex flex-col items-center justify-center w-full h-48 border-2 border-dashed rounded-xl cursor-pointer transition-colors ${
                  formData.file 
                    ? 'border-green-500 bg-green-50' 
                    : errors.file 
                    ? 'border-red-500 bg-red-50' 
                    : 'border-gray-300 hover:border-blue-500 bg-gray-50 hover:bg-blue-50'
                }`}>
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    {formData.file ? (
                      <>
                        <CheckCircle className="w-12 h-12 text-green-600 mb-3" />
                        <p className="text-sm font-medium text-gray-900">{formData.file.name}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {(formData.file.size / (1024 * 1024)).toFixed(2)} MB
                        </p>
                      </>
                    ) : (
                      <>
                        <Upload className="w-12 h-12 text-gray-400 mb-3" />
                        <p className="mb-2 text-sm text-gray-500">
                          <span className="font-semibold">Click to upload</span> or drag and drop
                        </p>
                        <p className="text-xs text-gray-500">
                          FASTA, FASTQ, TAR.GZ, TGZ, GZ, ZIP (Max 500MB)
                        </p>
                      </>
                    )}
                  </div>
                  <input
                    type="file"
                    className="hidden"
                    accept=".fasta,.fastq,.fa,.fq,.txt,.tar.gz,.tgz,.gz,.zip"
                    onChange={handleFileChange}
                  />
                </label>
              </div>
              {errors.file && (
                <p className="mt-2 text-sm text-red-600">{errors.file}</p>
              )}
            </div>

            {/* Dataset Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Dataset Name *
              </label>
              <input
                type="text"
                name="datasetName"
                value={formData.datasetName}
                onChange={handleInputChange}
                className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-blue-500 ${
                  errors.datasetName ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Coastal Marine Sample - January 2024"
              />
              {errors.datasetName && (
                <p className="mt-1 text-sm text-red-600">{errors.datasetName}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={4}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                placeholder="Provide details about your dataset, sampling methodology, and research objectives..."
              />
            </div>

            {/* Optional Metadata */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sample Location
                </label>
                <input
                  type="text"
                  name="sampleLocation"
                  value={formData.sampleLocation}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                  placeholder="Pacific Ocean, 32.5°N 117.2°W"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sample Date
                </label>
                <input
                  type="date"
                  name="sampleDate"
                  value={formData.sampleDate}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sample Depth (m)
                </label>
                <input
                  type="number"
                  name="sampleDepth"
                  value={formData.sampleDepth}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                  placeholder="50"
                  step="0.1"
                />
              </div>
            </div>

            {/* Upload Progress */}
            {isSubmitting && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-700">Uploading...</span>
                  <span className="text-gray-900 font-medium">{uploadProgress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Success Message */}
            {uploadSuccess && (
              <div className="flex items-center gap-2 p-4 bg-green-50 border border-green-200 rounded-xl">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <p className="text-green-800 font-medium">
                  Dataset uploaded successfully! It will be processed shortly.
                </p>
              </div>
            )}

            {/* Error Message */}
            {errors.submit && (
              <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-xl">
                <AlertCircle className="h-5 w-5 text-red-600" />
                <p className="text-red-800">{errors.submit}</p>
              </div>
            )}

            {/* Submit Button */}
            <div className="flex justify-end pt-4 border-t border-gray-200">
              <button
                type="submit"
                disabled={isSubmitting || uploadSuccess}
                className="px-8 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
              >
                {isSubmitting ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="h-5 w-5" />
                    Upload Dataset
                  </>
                )}
              </button>
            </div>
          </form>
        </Card>
      </div>
    </Layout>
  );
};

export default SubmitData;
