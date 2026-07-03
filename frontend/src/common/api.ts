import axios from 'axios';
import { Platform } from 'react-native';

// React Native 에뮬레이터/시뮬레이터용 백엔드 기본 IP 세팅
// - Android 에뮬레이터: 10.0.2.2
// - iOS 시뮬레이터: localhost
const DEFAULT_API_URL = Platform.select({
  android: 'http://10.0.2.2:8000/api/v1',
  ios: 'http://localhost:8000/api/v1',
  default: 'http://localhost:8000/api/v1',
});

const api = axios.create({
  baseURL: DEFAULT_API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 임시 메모리 기반 JWT 토큰 보관소 (실배포 시 @react-native-async-storage/async-storage 권장)
let userToken: string | null = null;

export const setAuthToken = (token: string | null) => {
  userToken = token;
};

// 요청 인터셉터: 토큰 주입
api.interceptors.request.use(
  async (config) => {
    if (userToken) {
      config.headers.Authorization = `Bearer ${userToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      userToken = null;
    }
    return Promise.reject(error);
  }
);

export default api;
