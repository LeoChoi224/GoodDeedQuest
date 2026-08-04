/**
 * Shared signup wizard state (약관 → 계정 → 프로필 → 완료) so back-navigation
 * preserves input. Mirrors the state shape in 01_login_flow.dc.html Component.state,
 * plus the fields the mockup implies (email/pw/nickname values).
 */
import React, { createContext, useContext, useMemo, useRef, useState } from 'react';
import { CATEGORY_DEFS } from '../theme';
import { checkEmailAvailable, checkNicknameAvailable } from '../api/auth';

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
  // 서버에 물어보므로 Promise 다. 부르는 쪽에서 await 해야 결과를 얻는다.
  checkEmail: () => Promise<boolean>;
  emailChecking: boolean;

  password: string;
  setPassword: (v: string) => void;
  passwordConfirm: string;
  setPasswordConfirm: (v: string) => void;

  nickname: string;
  setNickname: (v: string) => void;
  nickMsg: Msg;
  nickOk: boolean;
  checkNick: () => Promise<boolean>;
  nickChecking: boolean;

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
  const [emailChecking, setEmailChecking] = useState(false);
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [nickname, setNickname] = useState('');
  const [nickMsg, setNickMsg] = useState<Msg>(null);
  const [nickOk, setNickOk] = useState(false);
  const [nickChecking, setNickChecking] = useState(false);

  // 【판단】 state 는 검사 함수가 시작될 때의 값으로 얼어붙는다(클로저). 응답이
  // 돌아오는 사이 사용자가 입력칸을 고쳤는지 보려면 "지금 이 순간의 값"이 필요해서
  // ref 를 따로 둔다. ref.current 는 항상 최신값이다.
  const emailRef = useRef('');
  const nickRef = useRef('');
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
        emailRef.current = v;
        setEmail(v);
        if (emailMsg) {
          setEmailMsg(null);
          setEmailOk(false);
        }
      },
      emailMsg,
      emailOk,
      emailChecking,
      checkEmail: async () => {
        const v = email.trim();

        // 형식이 틀리면 서버를 부를 것도 없다.
        if (!EMAIL_RE.test(v)) {
          setEmailOk(false);
          setEmailMsg({ text: '사용할 수 없는 이메일입니다. 형식을 확인해 주세요.', color: BAD_RED });
          return false;
        }

        setEmailChecking(true);
        try {
          const res = await checkEmailAvailable(v);

          // 응답을 기다리는 동안 사용자가 이메일을 고쳤으면 이 결과는 남의 것이다.
          // 그대로 반영하면 바뀐 이메일에 "사용 가능"이 붙는다.
          if (emailRef.current.trim() !== v) return false;

          setEmailOk(res.available);
          setEmailMsg({ text: res.message, color: res.available ? OK_GREEN : BAD_RED });
          return res.available;
        } catch {
          // 서버가 안 되는 것과 중복인 것은 다르다. 통과시키지 않되 사유는 구분해서 알린다.
          setEmailOk(false);
          setEmailMsg({ text: '중복확인에 실패했습니다. 잠시 후 다시 시도해 주세요.', color: BAD_RED });
          return false;
        } finally {
          setEmailChecking(false);
        }
      },

      password,
      setPassword,
      passwordConfirm,
      setPasswordConfirm,

      nickname,
      setNickname: (v) => {
        nickRef.current = v;
        setNickname(v);
        if (nickMsg) {
          setNickMsg(null);
          setNickOk(false);
        }
      },
      nickMsg,
      nickOk,
      nickChecking,
      checkNick: async () => {
        const v = nickname.trim();

        if (v.length < 2 || v.length > 10) {
          setNickOk(false);
          setNickMsg({ text: '사용할 수 없는 닉네임입니다. (2~10자)', color: BAD_RED });
          return false;
        }

        setNickChecking(true);
        try {
          const res = await checkNicknameAvailable(v);

          if (nickRef.current.trim() !== v) return false;

          setNickOk(res.available);
          setNickMsg({ text: res.message, color: res.available ? OK_GREEN : BAD_RED });
          return res.available;
        } catch {
          setNickOk(false);
          setNickMsg({ text: '중복확인에 실패했습니다. 잠시 후 다시 시도해 주세요.', color: BAD_RED });
          return false;
        } finally {
          setNickChecking(false);
        }
      },

      cats,
      toggleCat: (k) => setCats((s) => ({ ...s, [k]: !s[k] })),
      times,
      toggleTime: (k) => setTimes((s) => ({ ...s, [k]: !s[k] })),

      birthday,
      setBirthday,

      reset: () => {
        setTerms({ t1: false, t2: false, t3: false });
        emailRef.current = '';
        setEmail('');
        setEmailMsg(null);
        setEmailOk(false);
        setEmailChecking(false);
        setPassword('');
        setPasswordConfirm('');
        nickRef.current = '';
        setNickname('');
        setNickMsg(null);
        setNickOk(false);
        setNickChecking(false);
        setCats(initialCats());
        setTimes(initialTimes());
        setBirthday(null);
      },
    }),
    [terms, allAgreed, email, emailMsg, emailOk, emailChecking, password, passwordConfirm, nickname, nickMsg, nickOk, nickChecking, cats, times, birthday]
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
