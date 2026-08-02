import axios from "axios";
import * as SecureStore from 'expo-secure-store'
import  Constants  from "expo-constants";
import { emitUnauthorized } from "./authEvents";

const debuggerHost = Constants.expoConfig?.hostUri?.split(':')[0] ?? 'localhost';
const BASE_URL = `http://${debuggerHost}:8000/api/v1`;

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

const AUTH_PATHS = ['/auth/login', '/auth/social-login'];
api.interceptors.response.use(
  (response) => response,

  (error) => {
    const status = error?.response?.status;
    const url = error?.config?.url ?? '';
    const isAuthRequest = AUTH_PATHS.some((path) => url.includes(path))

    if (status === 401 && !isAuthRequest) {
      emitUnauthorized();
    }

    return Promise.reject(error);
  }
)

export default api