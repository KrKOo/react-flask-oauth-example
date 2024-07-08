import axios from 'axios';
import router from './router';

const api = axios.create({ baseURL: 'http://127.0.0.1:5000/' });

api.interceptors.response.use(
  (response) => {
    console.log('Response:', response);
    return response;
  },
  async (error) => {
    console.log('Error:', error);
    const originalRequest = error.config;

    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      console.log('Refreshing token');

      const response = await fetch('/oauth/refresh');
      if (response.status !== 200) {
        console.log('Could not refresh the token, redirecting to login page');
        router.navigate('/login');
        return Promise.resolve();
      }
      return api(originalRequest);
    }
    return Promise.reject(error);
  }
);

export default api;
