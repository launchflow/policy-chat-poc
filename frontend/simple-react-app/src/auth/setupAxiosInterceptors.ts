import axios from "axios";

const setupAxiosInterceptors = (refreshToken: () => Promise<void>): void => {
  axios.interceptors.response.use(
    (response) => response,
    async (error) => {
      if (error.response.status === 401) {
        const result = (await refreshToken()) as any;
        const originalRequestConfig = error.config;
        originalRequestConfig.headers.Authorization = `Bearer ${result.access_token}`;
        return axios.request(originalRequestConfig);
      }
      return Promise.reject(error);
    }
  );
};

export default setupAxiosInterceptors;
