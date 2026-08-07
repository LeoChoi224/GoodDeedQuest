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

// 【판단】 세 단계로 찾는다. 앞에 있는 것이 이기고, 없으면 다음으로 넘어간다.
//   ① EXPO_PUBLIC_API_URL — eas.json 이 빌드할 때 주입 (preview/production)
//   ② Metro 의 hostUri — 개발 중이면 개발 PC 를 본다
//   ③ app.json 의 extra.apiUrl — Metro 도 없는 배포 빌드의 안전망
//
// ②를 ③보다 앞에 둬야 한다. extra.apiUrl 은 app.json 에 늘 값이 있어서,
// ③이 먼저면 Metro 를 켜고 개발하는 중에도 배포 서버를 부르게 된다.
// ①을 맨 앞에 둔 덕에, 개발 빌드로도 배포 서버를 보게 할 수 있다(시연용).
const BASE_URL =
  process.env.EXPO_PUBLIC_API_URL
  ?? (debuggerHost ? `http://${debuggerHost}:8000/api/v1` : undefined)
  ?? `${(configuredApiUrl ?? '').replace(/\/$/, '')}/api/v1`;

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