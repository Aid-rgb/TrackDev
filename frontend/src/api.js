import axios from 'axios';

// Get API key and other params from URL/Telegram
const getParams = () => {
  const hashParams = new URLSearchParams(window.location.hash.substring(1));
  const urlParams = new URLSearchParams(window.location.search);
  
  return {
    apiKey: hashParams.get('api_key') || urlParams.get('api_key') || localStorage.getItem('api_key') || '',
    projectId: hashParams.get('project_id') || urlParams.get('project_id') || null,
  };
};

const { apiKey } = getParams();
if (apiKey) localStorage.setItem('api_key', apiKey);

const api = axios.create({
  baseURL: '/api/v1/metrics',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to always use the latest API key
api.interceptors.request.use((config) => {
  const { apiKey } = getParams();
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey;
  }
  return config;
});

export const metricsApi = {
  getProjects: async () => {
    const { apiKey } = getParams();
    const response = await axios.get('/api/v1/projects', {
      headers: { 
        'X-API-Key': apiKey,
        'Content-Type': 'application/json'
      }
    });
    return response.data.projects || [];
  },

  getDashboard: async (projectId = null, period = 'month') => {
    const response = await api.get('/dashboard', {
      params: { project_id: projectId, period }
    });
    return response.data;
  }
};
