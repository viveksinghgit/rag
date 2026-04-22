import axios from 'axios';

// Get API base URL from environment or use current origin
const API_BASE_URL = process.env.REACT_APP_API_URL || window.location.origin;

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for logging
apiClient.interceptors.request.use(
  config => {
    console.log(`[API] ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  error => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for logging and error handling
apiClient.interceptors.response.use(
  response => {
    console.log(`[API] Response:`, response.status, response.data);
    return response;
  },
  error => {
    console.error('[API] Response error:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

// API Functions

export const healthCheck = async () => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
};

export const getConfig = async () => {
  try {
    const response = await apiClient.get('/config');
    return response.data;
  } catch (error) {
    console.error('Get config failed:', error);
    throw error;
  }
};

export const queryRag = async (query, topK = 5) => {
  try {
    const response = await apiClient.post('/query', {
      query,
      top_k: topK,
    });
    return response.data;
  } catch (error) {
    console.error('Query failed:', error);
    throw error;
  }
};

export const triggerIngestion = async () => {
  try {
    const response = await apiClient.post('/ingest');
    return response.data;
  } catch (error) {
    console.error('Ingestion trigger failed:', error);
    throw error;
  }
};

export default apiClient;
