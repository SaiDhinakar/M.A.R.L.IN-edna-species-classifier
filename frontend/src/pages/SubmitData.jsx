import React, { useState } from 'react';
import { 
  Upload, 
  FileText, 
  MapPin, 
  Calendar, 
  Database, 
  CheckCircle, 
  AlertCircle,
  User,
  Mail,
  Phone,
  Building,
  Dna,
  Microscope,
  Thermometer,
  Droplets
} from 'lucide-react';
import Layout from '../components/Layout';
import Card from '../components/Card';

const SubmitData = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    // Researcher Information
    researcherName: '',
    email: '',
    phone: '',
    institution: '',
    orcid: '',
    
    // Sample Information
    sampleName: '',
    collectionDate: '',
    location: '',
    coordinates: '',
    depth: '',
    temperature: '',
    salinity: '',
    ph: '',
    
    // Sequence Information
    sequencingMethod: '',
    targetGene: '',
    primerSet: '',
    sequenceFile: null,
    metadataFile: null,
    
    // Additional Information
    projectDescription: '',
    fundingSource: '',
    permissions: false,
    dataSharing: 'open'
  });

  const [errors, setErrors] = useState({});
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const steps = [
    { id: 1, title: 'Researcher Info', icon: User },
    { id: 2, title: 'Sample Data', icon: Microscope },
    { id: 3, title: 'Sequence Files', icon: Dna },
    { id: 4, title: 'Review & Submit', icon: CheckCircle }
  ];

  const handleInputChange = (field) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const handleFileChange = (field) => (e) => {
    const file = e.target.files[0];
    setFormData(prev => ({
      ...prev,
      [field]: file
    }));
  };

  const validateStep = (step) => {
    const newErrors = {};
    
    switch (step) {
      case 1:
        if (!formData.researcherName) newErrors.researcherName = 'Name is required';
        if (!formData.email) newErrors.email = 'Email is required';
        if (!formData.institution) newErrors.institution = 'Institution is required';
        break;
      case 2:
        if (!formData.sampleName) newErrors.sampleName = 'Sample name is required';
        if (!formData.collectionDate) newErrors.collectionDate = 'Collection date is required';
        if (!formData.location) newErrors.location = 'Location is required';
        break;
      case 3:
        if (!formData.sequenceFile) newErrors.sequenceFile = 'Sequence file is required';
        if (!formData.targetGene) newErrors.targetGene = 'Target gene is required';
        break;
      case 4:
        if (!formData.permissions) newErrors.permissions = 'Permission confirmation is required';
        break;
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const nextStep = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, 4));
    }
  };

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    if (!validateStep(4)) return;
    
    setIsSubmitting(true);
    
    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 10;
      });
    }, 200);
    
    // Simulate API call
    setTimeout(() => {
      setIsSubmitting(false);
      alert('Data submitted successfully! You will receive a confirmation email shortly.');
    }, 3000);
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Researcher Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Full Name *
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    value={formData.researcherName}
                    onChange={handleInputChange('researcherName')}
                    className={`w-full pl-10 pr-4 py-3 border rounded-xl focus:ring-2 focus:ring-blue-500 ${
                      errors.researcherName ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="Dr. Jane Smith"
                  />
                </div>
                {errors.researcherName && (
                  <p className="mt-1 text-sm text-red-600">{errors.researcherName}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address *
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="email"
                    value={formData.email}
                    onChange={handleInputChange('email')}
                    className={`w-full pl-10 pr-4 py-3 border rounded-xl focus:ring-2 focus:ring-blue-500 ${
                      errors.email ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="jane.smith@university.edu"
                  />
                </div>
                {errors.email && (
                  <p className="mt-1 text-sm text-red-600">{errors.email}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone Number
                </label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={handleInputChange('phone')}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                    placeholder="+1 (555) 123-4567"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Institution *
                </label>
                <div className="relative">
                  <Building className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    value={formData.institution}
                    onChange={handleInputChange('institution')}
                    className={`w-full pl-10 pr-4 py-3 border rounded-xl focus:ring-2 focus:ring-blue-500 ${
                      errors.institution ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="Marine Research Institute"
                  />
                </div>
                {errors.institution && (
                  <p className="mt-1 text-sm text-red-600">{errors.institution}</p>
                )}
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ORCID iD (Optional)
                </label>
                <input
                  type="text"
                  value={formData.orcid}
                  onChange={handleInputChange('orcid')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                  placeholder="0000-0000-0000-0000"
                />
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Sample Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sample Name *
                </label>
                <input
                  type="text"
                  value={formData.sampleName}
                  onChange={handleInputChange('sampleName')}
                  className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-blue-500 ${
                    errors.sampleName ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="PacificDeepSea_001"
                />
                {errors.sampleName && (
                  <p className="mt-1 text-sm text-red-600">{errors.sampleName}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Collection Date *
                </label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="date"
                    value={formData.collectionDate}
                    onChange={handleInputChange('collectionDate')}
                    className={`w-full pl-10 pr-4 py-3 border rounded-xl focus:ring-2 focus:ring-blue-500 ${
                      errors.collectionDate ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                </div>
                {errors.collectionDate && (
                  <p className="mt-1 text-sm text-red-600">{errors.collectionDate}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Location *
                </label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    value={formData.location}
                    onChange={handleInputChange('location')}
                    className={`w-full pl-10 pr-4 py-3 border rounded-xl focus:ring-2 focus:ring-blue-500 ${
                      errors.location ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="Pacific Ocean, Deep Sea Trench"
                  />
                </div>
                {errors.location && (
                  <p className="mt-1 text-sm text-red-600">{errors.location}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Coordinates (GPS)
                </label>
                <input
                  type="text"
                  value={formData.coordinates}
                  onChange={handleInputChange('coordinates')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                  placeholder="35.6762°N, 139.6503°E"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Depth (meters)
                </label>
                <input
                  type="number"
                  value={formData.depth}
                  onChange={handleInputChange('depth')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                  placeholder="1500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Temperature (°C)
                </label>
                <div className="relative">
                  <Thermometer className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="number"
                    step="0.1"
                    value={formData.temperature}
                    onChange={handleInputChange('temperature')}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                    placeholder="4.2"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Salinity (PSU)
                </label>
                <div className="relative">
                  <Droplets className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="number"
                    step="0.1"
                    value={formData.salinity}
                    onChange={handleInputChange('salinity')}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                    placeholder="35.0"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  pH Level
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.ph}
                  onChange={handleInputChange('ph')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                  placeholder="8.1"
                />
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Sequence Data</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sequencing Method
                </label>
                <select
                  value={formData.sequencingMethod}
                  onChange={handleInputChange('sequencingMethod')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select method</option>
                  <option value="illumina">Illumina</option>
                  <option value="nanopore">Oxford Nanopore</option>
                  <option value="pacbio">PacBio</option>
                  <option value="454">454 Pyrosequencing</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Target Gene *
                </label>
                <select
                  value={formData.targetGene}
                  onChange={handleInputChange('targetGene')}
                  className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-blue-500 ${
                    errors.targetGene ? 'border-red-500' : 'border-gray-300'
                  }`}
                >
                  <option value="">Select target gene</option>
                  <option value="16S">16S ribosomal RNA</option>
                  <option value="18S">18S ribosomal RNA</option>
                  <option value="28S">28S ribosomal RNA</option>
                  <option value="COI">Cytochrome c oxidase I</option>
                  <option value="ITS">ITS region</option>
                  <option value="other">Other</option>
                </select>
                {errors.targetGene && (
                  <p className="mt-1 text-sm text-red-600">{errors.targetGene}</p>
                )}
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Primer Set Used
                </label>
                <input
                  type="text"
                  value={formData.primerSet}
                  onChange={handleInputChange('primerSet')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                  placeholder="515F/806R for 16S V4 region"
                />
              </div>
            </div>

            {/* File Upload Section */}
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sequence File (FASTA/FASTQ) *
                </label>
                <div className="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center hover:border-blue-400 transition-colors">
                  <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <div className="space-y-2">
                    <label className="cursor-pointer">
                      <span className="text-blue-600 hover:text-blue-700 font-medium">
                        Click to upload sequence file
                      </span>
                      <input
                        type="file"
                        accept=".fasta,.fastq,.fa,.fq,.txt"
                        onChange={handleFileChange('sequenceFile')}
                        className="hidden"
                      />
                    </label>
                    <p className="text-sm text-gray-500">
                      Supported formats: FASTA, FASTQ (max 500MB)
                    </p>
                    {formData.sequenceFile && (
                      <p className="text-sm text-green-600 font-medium">
                        ✓ {formData.sequenceFile.name}
                      </p>
                    )}
                  </div>
                </div>
                {errors.sequenceFile && (
                  <p className="mt-1 text-sm text-red-600">{errors.sequenceFile}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Metadata File (Optional)
                </label>
                <div className="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center hover:border-blue-400 transition-colors">
                  <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <div className="space-y-2">
                    <label className="cursor-pointer">
                      <span className="text-blue-600 hover:text-blue-700 font-medium">
                        Click to upload metadata file
                      </span>
                      <input
                        type="file"
                        accept=".csv,.xlsx,.txt,.json"
                        onChange={handleFileChange('metadataFile')}
                        className="hidden"
                      />
                    </label>
                    <p className="text-sm text-gray-500">
                      Supported formats: CSV, Excel, JSON, TXT
                    </p>
                    {formData.metadataFile && (
                      <p className="text-sm text-green-600 font-medium">
                        ✓ {formData.metadataFile.name}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Review & Submit</h3>
            
            {/* Summary */}
            <div className="bg-gray-50 rounded-xl p-6">
              <h4 className="font-semibold text-gray-900 mb-4">Submission Summary</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Researcher:</span>
                  <span className="ml-2 font-medium">{formData.researcherName}</span>
                </div>
                <div>
                  <span className="text-gray-600">Institution:</span>
                  <span className="ml-2 font-medium">{formData.institution}</span>
                </div>
                <div>
                  <span className="text-gray-600">Sample:</span>
                  <span className="ml-2 font-medium">{formData.sampleName}</span>
                </div>
                <div>
                  <span className="text-gray-600">Location:</span>
                  <span className="ml-2 font-medium">{formData.location}</span>
                </div>
                <div>
                  <span className="text-gray-600">Target Gene:</span>
                  <span className="ml-2 font-medium">{formData.targetGene}</span>
                </div>
                <div>
                  <span className="text-gray-600">Files:</span>
                  <span className="ml-2 font-medium">
                    {formData.sequenceFile ? '✓ Sequence file' : '✗ No sequence file'}
                    {formData.metadataFile && ', ✓ Metadata file'}
                  </span>
                </div>
              </div>
            </div>

            {/* Additional Information */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Project Description
                </label>
                <textarea
                  value={formData.projectDescription}
                  onChange={handleInputChange('projectDescription')}
                  rows={4}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                  placeholder="Brief description of your research project and objectives..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Funding Source
                </label>
                <input
                  type="text"
                  value={formData.fundingSource}
                  onChange={handleInputChange('fundingSource')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                  placeholder="National Science Foundation, Grant #12345"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Data Sharing Preference
                </label>
                <select
                  value={formData.dataSharing}
                  onChange={handleInputChange('dataSharing')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                >
                  <option value="open">Open Access (Recommended)</option>
                  <option value="embargo">Embargo for 12 months</option>
                  <option value="restricted">Restricted Access</option>
                </select>
              </div>
            </div>

            {/* Permissions */}
            <div className="bg-blue-50 rounded-xl p-6 border border-blue-200">
              <div className="flex items-start">
                <input
                  type="checkbox"
                  id="permissions"
                  checked={formData.permissions}
                  onChange={handleInputChange('permissions')}
                  className="mt-1 mr-3"
                />
                <label htmlFor="permissions" className="text-sm text-gray-700">
                  <span className="font-medium">I confirm that:</span>
                  <ul className="mt-2 space-y-1 list-disc list-inside">
                    <li>I have the necessary permissions to submit this data</li>
                    <li>The data does not contain sensitive or protected information</li>
                    <li>I agree to the platform's terms of service and data policy</li>
                    <li>The submitted data can be used for research purposes</li>
                  </ul>
                </label>
              </div>
              {errors.permissions && (
                <p className="mt-2 text-sm text-red-600">{errors.permissions}</p>
              )}
            </div>

            {/* Upload Progress */}
            {isSubmitting && (
              <div className="bg-white rounded-xl p-6 border border-gray-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Uploading...</span>
                  <span className="text-sm text-gray-500">{uploadProgress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Layout title="Submit Data">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Submit eDNA Data</h1>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Contribute your environmental DNA samples and sequences to our growing database. 
            Your data will help advance marine biodiversity research worldwide.
          </p>
        </div>

        {/* Progress Steps */}
        <Card>
          <div className="flex items-center justify-between">
            {steps.map((step, index) => {
              const IconComponent = step.icon;
              const isActive = currentStep === step.id;
              const isCompleted = currentStep > step.id;
              
              return (
                <div key={step.id} className="flex items-center">
                  <div className={`flex items-center justify-center w-10 h-10 rounded-full ${
                    isCompleted ? 'bg-green-600 text-white' :
                    isActive ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                  }`}>
                    {isCompleted ? (
                      <CheckCircle className="h-5 w-5" />
                    ) : (
                      <IconComponent className="h-5 w-5" />
                    )}
                  </div>
                  <div className="ml-3">
                    <div className={`text-sm font-medium ${
                      isActive ? 'text-blue-600' : isCompleted ? 'text-green-600' : 'text-gray-500'
                    }`}>
                      {step.title}
                    </div>
                  </div>
                  {index < steps.length - 1 && (
                    <div className={`w-20 h-0.5 mx-4 ${
                      currentStep > step.id ? 'bg-green-600' : 'bg-gray-200'
                    }`} />
                  )}
                </div>
              );
            })}
          </div>
        </Card>

        {/* Form Content */}
        <Card>
          {renderStepContent()}
          
          {/* Navigation Buttons */}
          <div className="flex justify-between pt-6 mt-6 border-t border-gray-200">
            <button
              onClick={prevStep}
              disabled={currentStep === 1}
              className="px-6 py-2 text-gray-600 border border-gray-300 rounded-xl hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            
            {currentStep < 4 ? (
              <button
                onClick={nextStep}
                className="px-6 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="px-6 py-2 bg-green-600 text-white rounded-xl hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Submitting...' : 'Submit Data'}
              </button>
            )}
          </div>
        </Card>
      </div>
    </Layout>
  );
};

export default SubmitData;