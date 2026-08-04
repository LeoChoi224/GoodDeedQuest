/**
 * 로그인 상태를 앱 전체가 공유하는 자리.
 *
 * 왜 필요한가:
 *   토큰은 SecureStore 에 7일간 남아 있는데(ACCESS_TOKEN_EXPIRE_MINUTES = 60*24*7),
 *   앱을 켤 때 그걸 확인하지 않고 무조건 로그인 화면부터 띄우고 있었다.
 *   여기서 앱이 뜰 때 한 번 확인하고, 그 결과로 어느 화면을 보여줄지 정한다.
 */
import React, { createContext, useContext, useCallback, useEffect, useMemo, useState } from 'react';
import * as SecureStore from 'expo-secure-store';
import { TOKEN_KEY, REFRESH_TOKEN_KEY } from '../api/client';
import { setUnauthorizedHandler } from '../api/authEvents';
import { getMyProfile } from '../api/auth';

type AuthValue = {
  /** 저장된 토큰. 없으면 로그인 안 된 상태 */
  token: string | null;
  /** 현재 계정이 관리자인지. 확인 실패 시 안전하게 false로 둔다 */
  isAdmin: boolean;
  /** 앱이 뜨면서 토큰을 확인하는 중인지. true 면 아직 아무 화면도 보여주면 안 된다 */
  booting: boolean;
  /** 로그인 성공 시 호출. 토큰을 저장하고 화면을 로그인 후 상태로 바꾼다 */
  signIn: (token: string) => Promise<void>;
  /** 로그아웃. 토큰을 지우고 로그인 화면으로 돌아간다 */
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [booting, setBooting] = useState(true);

  // 앱이 뜰 때 딱 한 번, 주머니에 열쇠가 있는지 확인한다.
  useEffect(() => {
    (async () => {
      try {
        const storedToken = await SecureStore.getItemAsync(TOKEN_KEY);
        setToken(storedToken);

        if (storedToken) {
          try {
            const currentUser = await getMyProfile();
            setIsAdmin(currentUser.role === 'ADMIN');
          } catch {
            setIsAdmin(false);
          }
        }
      } catch {
        // 【판단】 읽기에 실패하면 로그인 안 된 것으로 본다. 여기서 앱을 멈추면
        //        저장소 문제 하나로 아무것도 못 하게 된다.
        setToken(null);
        setIsAdmin(false);
      } finally {
        setBooting(false);
      }
    })();
  }, []);

  const signIn = useCallback(async (next: string) => {
    await SecureStore.setItemAsync(TOKEN_KEY, next);
    setToken(next);

    try {
      const currentUser = await getMyProfile();
      setIsAdmin(currentUser.role === 'ADMIN');
    } catch {
      setIsAdmin(false);
    }
  }, []);

  const signOut = useCallback(async () => {
    try {
      await SecureStore.deleteItemAsync(TOKEN_KEY);
      await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
    } finally {
      // 【판단】 지우기에 실패해도 화면은 로그아웃으로 넘긴다. 토큰이 죽은 건
      //        이미 확정이라, 남겨두면 계속 401 만 받는 상태에 갇힌다.
      setToken(null);
      setIsAdmin(false);
    }
  }, []);

  // client.ts 의 인터셉터가 401 을 받으면 emitUnauthorized() 를 부르고,
  // 그 신호가 여기로 와서 로그아웃된다.
  useEffect(() => {
    setUnauthorizedHandler(() => { void signOut(); });
    return () => setUnauthorizedHandler(null);
  }, [signOut]);

  const value = useMemo(
    () => ({ token, isAdmin, booting, signIn, signOut }),
    [token, isAdmin, booting, signIn, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/** 화면에서 로그인 상태를 쓰고 싶을 때. AuthProvider 안에서만 부를 수 있다. */
export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth 는 AuthProvider 안에서만 쓸 수 있습니다.');
  return ctx;
}
