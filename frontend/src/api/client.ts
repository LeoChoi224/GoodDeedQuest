import axios from "axios";
import * as SecureStore from 'expo-secure-store'
import  Constants  from "expo-constants";
import { emitUnauthorized } from "./authEvents";

declare module 'axios' {
  interface InternalAxiosRequestConfig {
    _retry?: boolean;
  }
}

// Metro(개발 서버)로 실행 중이면 hostUri 에 개발 PC 주소가 들어온다.
// APK 로 빌드하면 hostUri 가 undefined 라 app.json 의 extra.apiUrl 을 쓴다.
// (예전에는 'localhost' 로 떨어져서 앱이 자기 자신에게 요청을 보냈다)
const debuggerHost = Constants.expoConfig?.hostUri?.split(':')[0];
const configuredApiUrl = Constants.expoConfig?.extra?.apiUrl as string | undefined;

const BASE_URL = debuggerHost
  ? `http://${debuggerHost}:8000/api/v1`
  : `${configuredApiUrl}/api/v1`;

export const TOKEN_KEY = 'access_token';
export const REFRESH_TOKEN_KEY = 'refresh_token';

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

const AUTH_PATHS = ['/auth/login', '/auth/social-login', '/auth/refresh'];


let refreshing: Promise<string | null> | null = null;
async function doRefresh(): Promise<string | null> {
  const refreshToken = await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
  if (!refreshToken) return null;

  try {
    // 【판단】 api 가 아니라 맨 axios 를 쓴다. api 로 부르면 이 인터셉터를
    //        다시 타고, 요청 인터셉터가 죽은 access 를 또 붙인다.
    const response = await axios.post(`${BASE_URL}/auth/refresh`, {
      refresh_token: refreshToken,
    });
    const data = response.data.data;
    await SecureStore.setItemAsync(TOKEN_KEY, data.access_token);
    await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, data.refresh_token);
    return data.access_token as string;
  } catch {
    // 재발급마저 실패. 남은 토큰은 쓸모가 없으니 지운다.
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
    return null;
  }
}

function refreshOnce(): Promise<string | null> {
  if (!refreshing) {
    refreshing = doRefresh().finally(() => { refreshing = null; });
  }
  return refreshing;
}

api.interceptors.response.use(
  (response) => response,

async (error) => {
    const status = error?.response?.status;
    const config = error?.config
    const url = error?.config?.url ?? '';
    const isAuthRequest = AUTH_PATHS.some((path) => url.includes(path))

    if (status === 401 && !isAuthRequest && config && !config._retry) {
      config._retry = true;

      const newToken = await refreshOnce();
      if (newToken) {
        config.headers = config.headers ?? {};
        config.headers.Authorization = `Bearer ${newToken}`;
        return api(config);          // 원래 요청을 그대로 다시 보낸다
      }

      emitUnauthorized();
    }

    return Promise.reject(error);
  }
)

export default api