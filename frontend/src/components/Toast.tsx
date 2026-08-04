/**
 * Toast — bottom slide-up notification (auto-dismiss). Provider + useToast() hook.
 * Used for "다운로드 완료", "장착 완료", copy/share confirmations, etc.
 */
import React, { createContext, useCallback, useContext, useRef, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { SlideInDown, SlideOutDown } from 'react-native-reanimated';
import { colors, fonts, radii } from '../theme';

type ToastCtx = { show: (msg: string, ms?: number) => void };
const Ctx = createContext<ToastCtx>({ show: () => {} });

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const insets = useSafeAreaInsets();
  const [msg, setMsg] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 【판단】 기본 1800ms 는 인증 거절 사유처럼 두세 줄짜리 안내를 읽기엔 짧다.
  //        5초로 늘린다. 부르는 쪽에서 두 번째 인자로 따로 지정할 수도 있다.
  const show = useCallback((m: string, ms = 5000) => {
    if (timer.current) clearTimeout(timer.current);
    setMsg(m);
    timer.current = setTimeout(() => setMsg(null), ms);
  }, []);

  return (
    <Ctx.Provider value={{ show }}>
      {children}
      {msg ? (
        <Animated.View
          entering={SlideInDown.duration(220)}
          exiting={SlideOutDown.duration(200)}
          style={[styles.toast, { bottom: insets.bottom + 96 }]}
          pointerEvents="none"
        >
          <Text style={styles.text}>{msg}</Text>
        </Animated.View>
      ) : null}
    </Ctx.Provider>
  );
}

export function useToast() {
  return useContext(Ctx);
}

const styles = StyleSheet.create({
  toast: {
    position: 'absolute',
    alignSelf: 'center',
    maxWidth: '86%',
    backgroundColor: 'rgba(3,50,54,0.95)',
    borderRadius: radii.pill,
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: 'rgba(212,160,23,0.4)',
  },
  text: { color: colors.parchment, fontSize: 13, fontWeight: '600', fontFamily: fonts.bodyM, textAlign: 'center' },
});
