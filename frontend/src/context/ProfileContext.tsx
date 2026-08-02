/**
 * 마이페이지 프로필 헤더(닉네임/칭호/레벨/연속접속일/이미지)를 앱 전역에서 공유한다.
 * MyPageScreen과 우측 드로어(DrawerContent) 상단이 같은 계정 정보를 보여줘야 하고,
 * MyPageScreen에서 값이 바뀌면(칭호 장착 후 복귀, 프로필 이미지 변경 등) 드로어도
 * 다시 열 필요 없이 즉시 함께 갱신되어야 하므로 Context로 단일 소스를 둔다.
 * AppDrawer(로그인 이후 메인 셸) 아래에 Provider를 둬서, 로그인 전 화면에서는
 * 불필요한 /mypage/profile 호출이 나가지 않도록 한다.
 */
import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { getMyProfile, type MyProfile } from '../api/mypage';

type ProfileCtx = {
  profile: MyProfile | null;
  loading: boolean;
  error: boolean;
  refreshProfile: () => Promise<void>;
  setProfile: (p: MyProfile) => void;
};

const Ctx = createContext<ProfileCtx | null>(null);

export function ProfileProvider({ children }: { children: React.ReactNode }) {
  const [profile, setProfile] = useState<MyProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const refreshProfile = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const data = await getMyProfile();
      setProfile(data);
    } catch (err) {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshProfile();
  }, [refreshProfile]);

  return (
    <Ctx.Provider value={{ profile, loading, error, refreshProfile, setProfile }}>
      {children}
    </Ctx.Provider>
  );
}

export function useProfile() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useProfile must be used within ProfileProvider');
  return ctx;
}
