import * as SecureStore from 'expo-secure-store'
import api, { TOKEN_KEY } from './client'

export async function login(email: string, password: string): Promise<string> {
  const resposnse = await api.post('/auth/login', { email, password });
  const token: string = resposnse.data.data.access_token;
  await SecureStore.setItemAsync(TOKEN_KEY, token);
  return token
}

export async function logout(): Promise<void> {
  await SecureStore.deleteItemAsync(TOKEN_KEY)
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