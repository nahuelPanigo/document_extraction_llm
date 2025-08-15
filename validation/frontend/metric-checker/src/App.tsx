import React, { useState } from 'react';
import './App.css';
import FileUpload from './components/FileUpload';
import MetricsVisualization from './components/MetricsVisualization';
import { compareJsonFiles, mockCompareJsonFiles, validateJsonFile, MetricResult, TypeSpecificResult } from './services/api';

// Application states
type AppState = 'upload' | 'loading' | 'results' | 'error';

interface AppError {
  message: string;
  details?: string;
}

function App() {
  const [currentState, setCurrentState] = useState<AppState>('upload');
  const [results, setResults] = useState<MetricResult[]>([]);
  const [typeSpecificResults, setTypeSpecificResults] = useState<Record<string, TypeSpecificResult>>({});
  const [error, setError] = useState<AppError | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<{
    predicted: File | null;
    real: File | null;
  }>({ predicted: null, real: null });

  // Handle file selection
  const handleFilesSelected = (predictedFile: File | null, realFile: File | null) => {
    setUploadedFiles({ predicted: predictedFile, real: realFile });
    // Clear any previous errors
    if (error) {
      setError(null);
    }
  };

  // Validate files before comparison
  const validateFiles = async (predictedFile: File, realFile: File): Promise<boolean> => {
    try {
      // Check file sizes (max 10MB each)
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (predictedFile.size > maxSize || realFile.size > maxSize) {
        setError({
          message: 'File size too large',
          details: 'Each file must be smaller than 10MB'
        });
        return false;
      }

      // Validate JSON format
      const predictedValidation = await validateJsonFile(predictedFile);
      if (!predictedValidation.valid) {
        setError({
          message: 'Invalid predicted file',
          details: predictedValidation.error
        });
        return false;
      }

      const realValidation = await validateJsonFile(realFile);
      if (!realValidation.valid) {
        setError({
          message: 'Invalid ground truth file',
          details: realValidation.error
        });
        return false;
      }

      return true;
    } catch (err) {
      setError({
        message: 'File validation failed',
        details: err instanceof Error ? err.message : 'Unknown error'
      });
      return false;
    }
  };

  // Handle comparison request
  const handleCompare = async () => {
    if (!uploadedFiles.predicted || !uploadedFiles.real) {
      setError({
        message: 'Missing files',
        details: 'Please upload both predicted and ground truth JSON files'
      });
      return;
    }

    setCurrentState('loading');
    setError(null);

    try {
      // Validate files first
      const isValid = await validateFiles(uploadedFiles.predicted, uploadedFiles.real);
      if (!isValid) {
        setCurrentState('error');
        return;
      }

      // Attempt real API call first, fall back to mock if it fails
      let response;
      try {
        response = await compareJsonFiles(uploadedFiles.predicted, uploadedFiles.real);
      } catch (apiError) {
        console.warn('API call failed, using mock data:', apiError);
        // Use mock data for development/demo purposes
        response = await mockCompareJsonFiles(uploadedFiles.predicted, uploadedFiles.real);
      }

      if (response.success && response.results) {
        setResults(response.results);
        setTypeSpecificResults(response.typeSpecificResults || {});
        setCurrentState('results');
      } else {
        throw new Error(response.error || 'Comparison failed');
      }
    } catch (err) {
      console.error('Comparison error:', err);
      setError({
        message: 'Comparison failed',
        details: err instanceof Error ? err.message : 'Unknown error occurred'
      });
      setCurrentState('error');
    }
  };

  // Reset to initial state
  const handleReset = () => {
    setCurrentState('upload');
    setResults([]);
    setTypeSpecificResults({});
    setError(null);
    setUploadedFiles({ predicted: null, real: null });
  };

  // Render loading state
  const renderLoading = () => (
    <div className="loading-container">
      <div className="loading-spinner"></div>
      <h2>Comparing JSON Files...</h2>
      <p>Analyzing metadata and calculating metrics</p>
      <div className="loading-details">
        <div className="loading-step">✓ Files validated</div>
        <div className="loading-step">⏳ Running comparisons</div>
        <div className="loading-step">⏳ Calculating metrics</div>
        <div className="loading-step">⏳ Generating report</div>
      </div>
    </div>
  );

  // Render error state
  const renderError = () => (
    <div className="error-container">
      <div className="error-icon">⚠️</div>
      <h2>Error</h2>
      <p className="error-message">{error?.message}</p>
      {error?.details && (
        <div className="error-details">
          <strong>Details:</strong> {error.details}
        </div>
      )}
      <button onClick={handleReset} className="error-reset-btn">
        Try Again
      </button>
    </div>
  );

  return (
    <div className="App">
      {currentState === 'upload' && (
        <FileUpload 
          onFilesSelected={handleFilesSelected}
          onCompare={handleCompare}
        />
      )}
      
      {currentState === 'loading' && renderLoading()}
      
      {currentState === 'results' && (
        <MetricsVisualization 
          results={results}
          typeSpecificResults={typeSpecificResults}
          onReset={handleReset}
        />
      )}
      
      {currentState === 'error' && renderError()}
    </div>
  );
}

export default App;