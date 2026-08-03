import * as SecureStore from 'expo-secure-store'
import api, { TOKEN_KEY, REFRESH_TOKEN_KEY } from './client'

export async function login(email: string, password: string): Promise<string> {
  const resposnse = await api.post('/auth/login', { email, password });
  const token: string = resposnse.data.data.access_token;
  const refresh: string = resposnse.data.data.refresh_token;
  await SecureStore.setItemAsync(TOKEN_KEY, token);
  await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refresh);
  return token
}

export async function logout(): Promise<void> {
  try {
    await api.post('/auth/logout');
  } catch {
    
  }
  await SecureStore.deleteItemAsync(TOKEN_KEY)
  await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY)  
}

export type RegisterPayload = {
  email: string;
  password: string;
  nickname: string;
  birthday: string; // YYYY-MM-DD
  active_time?: string[];
  category?: string[];
};

export async function register(payload: RegisterPayload) {
  const response = await api.post('/auth/register', payload);
  return response.data;
}

export async function socialLogin(
  idToken: string,
  provider: 'google' | 'kakao' = 'google',
): Promise<{ token: string; isNewUser: boolean }> {
  const response = await api.post('/auth/social-login', {
    provider,
    id_token: idToken
  });
  const token: string = response.data.data.access_token;
  const refresh: string = response.data.data.refresh_token;
  const isNewUser: boolean = response.data.data.is_new_user
  await SecureStore.setItemAsync(TOKEN_KEY, token);
  await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refresh);
  return { token, isNewUser }
}

export type ProfileCompletePayload = {
  nickname: string;
  birthday: string;
  active_time?: string[];
  category?: string[];
}

export async function completeProfile(payload: ProfileCompletePayload) {
  const response = await api.patch('/auth/me', payload);
  return response.data;
}

export async function getMyProfile() {
  const response = await api.get('/auth/me');
    return response.data?.data || response.data;
}

export async function updateMyLocation(latitude: number, longitude: number) {
  const response = await api.patch('/auth/me/location', {
    current_latitude: latitude,
    current_longitude: longitude,
  });
  return response.data?.data || response.data;
}