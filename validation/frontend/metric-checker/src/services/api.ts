import axios, { AxiosResponse } from 'axios';

// Types for the API responses
export interface MetricResult {
  metric_type: string;
  field_name: string | null;
  total_items: number;
  exact_matches?: number;
  accuracy?: number;
  mismatches?: Array<{
    id: string;
    field?: string;
    predicted?: any;
    real?: any;
    mismatched_fields?: Array<{
      field: string;
      predicted: any;
      real: any;
    }>;
  }>;
  perfect_matches?: number;
  average_percentage?: number;
  details?: Array<{
    id: string;
    predicted_list: string[];
    real_list: string[];
    match_percentage: number;
    matching_elements: string[];
    missing_elements: string[];
    extra_elements: string[];
  }>;
}

export interface TypeSpecificResult {
  type: string;
  total_documents: number;
  detailed_results: MetricResult[];
  summary: any;
}

export interface ComparisonResponse {
  success: boolean;
  results: MetricResult[];
  typeSpecificResults?: Record<string, TypeSpecificResult>;
  error?: string;
}

export interface BackendResponse {
  detailed_results: MetricResult[];
  summary: {
    total_metrics_run: number;
    exact_equality_metrics: any[];
    list_percentage_metrics: any[];
    overall_performance: any;
  };
  type_specific_results?: Record<string, TypeSpecificResult>;
}

// Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  // Don't set Content-Type header - let axios handle it for FormData
});

// Add request interceptor for logging (development only)
if (process.env.NODE_ENV === 'development') {
  apiClient.interceptors.request.use(
    (config) => {
      console.log('API Request:', {
        method: config.method?.toUpperCase(),
        url: config.url,
        data: config.data instanceof FormData ? 'FormData' : config.data,
      });
      return config;
    },
    (error) => {
      console.error('API Request Error:', error);
      return Promise.reject(error);
    }
  );
}

// Add response interceptor for logging and error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    if (process.env.NODE_ENV === 'development') {
      console.log('API Response:', {
        status: response.status,
        data: response.data,
      });
    }
    return response;
  },
  (error) => {
    console.error('API Response Error:', {
      status: error.response?.status,
      data: error.response?.data,
      message: error.message,
    });
    
    // Transform error for better handling
    const transformedError = {
      message: error.response?.data?.error || error.message || 'An unexpected error occurred',
      status: error.response?.status || 0,
      data: error.response?.data,
    };
    
    return Promise.reject(transformedError);
  }
);

/**
 * Upload and compare two JSON files
 */
export const compareJsonFiles = async (
  predictedFile: File,
  realFile: File
): Promise<ComparisonResponse> => {
  try {
    console.log('Starting API call to:', API_BASE_URL);
    console.log('Files:', { predicted: predictedFile.name, real: realFile.name });
    
    // Validate files
    if (!predictedFile || !realFile) {
      throw new Error('Both predicted and real files are required');
    }

    // Validate file types
    if (!predictedFile.name.endsWith('.json') || !realFile.name.endsWith('.json')) {
      throw new Error('Both files must be JSON files');
    }

    // Create FormData (match backend parameter names)
    const formData = new FormData();
    formData.append('predicted_file', predictedFile);
    formData.append('original_file', realFile);
    
    console.log('FormData created, making API call...');

    // Try with fetch instead of axios to debug
    try {
      const fetchResponse = await fetch(`${API_BASE_URL}/api/metrics`, {
        method: 'POST',
        body: formData,
        // Don't set Content-Type header - let browser handle it for FormData
      });
      
      console.log('Fetch response status:', fetchResponse.status);
      console.log('Fetch response ok:', fetchResponse.ok);
      
      if (!fetchResponse.ok) {
        throw new Error(`HTTP error! status: ${fetchResponse.status}`);
      }
      
      const backendData = await fetchResponse.json();
      console.log('Backend response via fetch:', backendData);
      
      // Check if backend returned an error
      if (backendData.error) {
        throw new Error(backendData.error);
      }
      
      // Extract results from backend response
      const results = backendData.detailed_results || [];
      const typeSpecificResults = backendData.type_specific_results || {};
      
      console.log('Transformed results:', results);
      console.log('Type-specific results:', typeSpecificResults);
      
      return {
        success: true,
        results: results,
        typeSpecificResults: typeSpecificResults,
      };
      
    } catch (fetchError) {
      console.error('Fetch failed, trying axios:', fetchError);
      
      // Fallback to axios
      const response = await apiClient.post<BackendResponse>('/api/metrics', formData);
      
      console.log('Backend response via axios:', response.data);
      
      const backendData = response.data;
      
      if ('error' in backendData) {
        throw new Error((backendData as any).error);
      }
      
      const results = backendData.detailed_results || [];
      const typeSpecificResults = backendData.type_specific_results || {};
      
      return {
        success: true,
        results: results,
        typeSpecificResults: typeSpecificResults,
      };
    }
    
  } catch (error: any) {
    console.error('Error in compareJsonFiles:', error);
    
    // Return a structured error response
    return {
      success: false,
      results: [],
      error: error.message || 'Failed to compare files',
    };
  }
};

/**
 * Health check endpoint to verify API connectivity
 */
export const healthCheck = async (): Promise<{ status: string; timestamp: string }> => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error: any) {
    throw new Error(`Health check failed: ${error.message}`);
  }
};

/**
 * Get API status and configuration
 */
export const getApiStatus = async (): Promise<{
  status: string;
  version: string;
  supported_formats: string[];
  max_file_size: number;
}> => {
  try {
    const response = await apiClient.get('/status');
    return response.data;
  } catch (error: any) {
    throw new Error(`Failed to get API status: ${error.message}`);
  }
};

/**
 * Utility function to validate JSON file content
 */
export const validateJsonFile = async (file: File): Promise<{ valid: boolean; error?: string }> => {
  return new Promise((resolve) => {
    const reader = new FileReader();
    
    reader.onload = (event) => {
      try {
        const content = event.target?.result as string;
        JSON.parse(content);
        resolve({ valid: true });
      } catch (error) {
        resolve({ 
          valid: false, 
          error: `Invalid JSON format: ${error instanceof Error ? error.message : 'Unknown error'}` 
        });
      }
    };
    
    reader.onerror = () => {
      resolve({ 
        valid: false, 
        error: 'Failed to read file' 
      });
    };
    
    reader.readAsText(file);
  });
};

/**
 * Mock API function for development/testing when backend is not available
 */
export const mockCompareJsonFiles = async (
  predictedFile: File,
  realFile: File
): Promise<ComparisonResponse> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Mock response data
  const mockResults: MetricResult[] = [
    {
      metric_type: 'exact_equality',
      field_name: null,
      total_items: 10,
      exact_matches: 6,
      accuracy: 0.6,
      mismatches: [
        {
          id: 'item1',
          mismatched_fields: [
            {
              field: 'title',
              predicted: 'Predicted Title',
              real: 'Real Title'
            }
          ]
        }
      ]
    },
    {
      metric_type: 'exact_equality',
      field_name: 'title',
      total_items: 10,
      exact_matches: 8,
      accuracy: 0.8,
      mismatches: [
        {
          id: 'item2',
          field: 'title',
          predicted: 'Machine Learning Analysis',
          real: 'Deep Learning Analysis'
        }
      ]
    },
    {
      metric_type: 'list_percentage_match',
      field_name: 'keywords',
      total_items: 10,
      perfect_matches: 4,
      average_percentage: 0.75,
      details: [
        {
          id: 'item1',
          predicted_list: ['AI', 'Machine Learning', 'Neural Networks'],
          real_list: ['AI', 'Deep Learning', 'Neural Networks'],
          match_percentage: 0.75,
          matching_elements: ['AI', 'Neural Networks'],
          missing_elements: ['Deep Learning'],
          extra_elements: ['Machine Learning']
        }
      ]
    }
  ];

  return {
    success: true,
    results: mockResults
  };
};

// Export configuration for use in components
export const apiConfig = {
  baseURL: API_BASE_URL,
  maxFileSize: 10 * 1024 * 1024, // 10MB
  supportedFormats: ['.json'],
  timeout: 30000,
};