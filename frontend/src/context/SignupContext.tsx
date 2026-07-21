/**
 * Shared signup wizard state (약관 → 계정 → 프로필 → 완료) so back-navigation
 * preserves input. Mirrors the state shape in 01_login_flow.dc.html Component.state,
 * plus the fields the mockup implies (email/pw/nickname values).
 */
import React, { createContext, useContext, useMemo, useState } from 'react';
import { CATEGORY_DEFS } from '../theme';

export type Msg = { text: string; color: string } | null;

type SignupState = {
  // terms — the mockup defaults all-true; we start unchecked to demonstrate the
  // 전체동의 → "다음" gating + enable animation the flow arrow calls out ("전체동의").
  terms: { t1: boolean; t2: boolean; t3: boolean };
  setTerm: (k: 't1' | 't2' | 't3') => void;
  toggleAllTerms: () => void;
  allAgreed: boolean;

  email: string;
  setEmail: (v: string) => void;
  emailMsg: Msg;
  emailOk: boolean;
  checkEmail: () => boolean;

  password: string;
  setPassword: (v: string) => void;
  passwordConfirm: string;
  setPasswordConfirm: (v: string) => void;

  nickname: string;
  setNickname: (v: string) => void;
  nickMsg: Msg;
  nickOk: boolean;
  checkNick: () => boolean;

  cats: Record<string, boolean>;
  toggleCat: (k: string) => void;

  times: Record<string, boolean>;
  toggleTime: (k: string) => void;

  birthday: Date | null;
  setBirthday: (v: Date) => void;

  reset: () => void;
};

const Ctx = createContext<SignupState | null>(null);

const OK_GREEN = '#4CAF50';
const BAD_RED = '#E53935';
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const initialCats = () => {
  const o: Record<string, boolean> = {};
  CATEGORY_DEFS.forEach((c) => (o[c.key] = c.key === 'volunteer' || c.key === 'environment'));
  return o;
};
const initialTimes = () => ({ '0시~06시': false, '06시~12시': false, '12시~18시': false, '18시~24시': true });

export function SignupProvider({ children }: { children: React.ReactNode }) {
  const [terms, setTerms] = useState({ t1: false, t2: false, t3: false });
  const [email, setEmail] = useState('');
  const [emailMsg, setEmailMsg] = useState<Msg>(null);
  const [emailOk, setEmailOk] = useState(false);
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [nickname, setNickname] = useState('');
  const [nickMsg, setNickMsg] = useState<Msg>(null);
  const [nickOk, setNickOk] = useState(false);
  const [cats, setCats] = useState<Record<string, boolean>>(initialCats);
  const [times, setTimes] = useState<Record<string, boolean>>(initialTimes);
  const [birthday, setBirthday] = useState<Date | null>(null);

  const allAgreed = terms.t1 && terms.t2 && terms.t3;

  const value = useMemo<SignupState>(
    () => ({
      terms,
      setTerm: (k) => setTerms((s) => ({ ...s, [k]: !s[k] })),
      toggleAllTerms: () => {
        const next = !(terms.t1 && terms.t2 && terms.t3);
        setTerms({ t1: next, t2: next, t3: next });
      },
      allAgreed,

      email,
      setEmail: (v) => {
        setEmail(v);
        if (emailMsg) {
          setEmailMsg(null);
          setEmailOk(false);
        }
      },
      emailMsg,
      emailOk,
      checkEmail: () => {
        const v = email.trim();
        const ok = EMAIL_RE.test(v);
        setEmailOk(ok);
        setEmailMsg(
          ok
            ? { text: '사용 가능한 이메일입니다.', color: OK_GREEN }
            : { text: '사용할 수 없는 이메일입니다. 형식을 확인해 주세요.', color: BAD_RED }
        );
        return ok;
      },

      password,
      setPassword,
      passwordConfirm,
      setPasswordConfirm,

      nickname,
      setNickname: (v) => {
        setNickname(v);
        if (nickMsg) {
          setNickMsg(null);
          setNickOk(false);
        }
      },
      nickMsg,
      nickOk,
      checkNick: () => {
        const v = nickname.trim();
        const ok = v.length >= 2 && v.length <= 10;
        setNickOk(ok);
        setNickMsg(
          ok
            ? { text: '사용 가능한 닉네임입니다.', color: OK_GREEN }
            : { text: '사용할 수 없는 닉네임입니다. (2~10자)', color: BAD_RED }
        );
        return ok;
      },

      cats,
      toggleCat: (k) => setCats((s) => ({ ...s, [k]: !s[k] })),
      times,
      toggleTime: (k) => setTimes((s) => ({ ...s, [k]: !s[k] })),

      birthday,
      setBirthday,

      reset: () => {
        setTerms({ t1: false, t2: false, t3: false });
        setEmail('');
        setEmailMsg(null);
        setEmailOk(false);
        setPassword('');
        setPasswordConfirm('');
        setNickname('');
        setNickMsg(null);
        setNickOk(false);
        setCats(initialCats());
        setTimes(initialTimes());
        setBirthday(null);
      },
    }),
    [terms, allAgreed, email, emailMsg, emailOk, password, passwordConfirm, nickname, nickMsg, nickOk, cats, times, birthday]
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useSignup() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useSignup must be used within SignupProvider');
  return ctx;
}

/** Password rule from the mockup: "영문·숫자 포함 8자 이상". */
export function isPasswordValid(pw: string) {
  return pw.length >= 8 && /[A-Za-z]/.test(pw) && /[0-9]/.test(pw);
}
