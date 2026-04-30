import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // token expired or invalid, get new one
      localStorage.removeItem('token');
      await getToken();
      // retry original request
      const config = error.config;
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return apiClient.request(config);
    }
    return Promise.reject(error);
  }
);

// get JWT token
export const getToken = async () => {
  try {
    const response = await axios.post(`${API_BASE_URL}/token`);
    const token = response.data.access_token;
    localStorage.setItem('token', token);
    return token;
  } catch (error) {
    console.error('Failed to get token:', error);
    throw error;
  }
};

// create new job
export const createJob = async (url) => {
  try {
    const response = await apiClient.post('/jobs', { url });
    return response.data;
  } catch (error) {
    console.error('Failed to create job:', error);
    throw error;
  }
};

// get all jobs for current user
export const getJobs = async () => {
  try {
    const response = await apiClient.get('/jobs');
    return response.data;
  } catch (error) {
    console.error('Failed to get jobs:', error);
    throw error;
  }
};

// get job result (presigned URL)
export const getJobResult = async (jobId) => {
  try {
    const response = await apiClient.get(`/jobs/${jobId}/result`);
    return response.data.presigned_url;
  } catch (error) {
    console.error('Failed to get job result:', error);
    throw error;
  }
};

// fetch and parse result JSON data
export const getJobResultData = async (jobId) => {
  try {
    const presignedUrl = await getJobResult(jobId);
    const response = await axios.get(presignedUrl);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch result data:', error);
    throw error;
  }
};

// initialize token on app load
export const initializeAuth = async () => {
  const token = localStorage.getItem('token');
  if (!token) {
    await getToken();
  }
};
