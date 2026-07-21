import axios from "axios";
import * as SecureStore from 'expo-secure-store'

const BASE_URL = 'http://192.168.0.224:8000/api/v1';

export const TOKEN_KEY = 'access_token';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
})

api.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api