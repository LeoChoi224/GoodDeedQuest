/**
 * SCREEN 08-1 · 사진 선택 및 상세설정 (route: PhotoSelect — Shortform stack ROOT,
 * reached from the drawer). MainHeader (no back, hamburger) + haze bg.
 * 기간 필터 칩 · 인증 사진 3열 그리드(다중 선택, 골드 체크 배지) · N장 선택됨.
 * Footer: AI 대본 / 음악 → 각 오버레이, 생성하기 → Generating.
 * Motion: grid cells stagger-pop (ZoomIn.delay), chips/buttons spring press.
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, Pressable, ScrollView, useWindowDimensions } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { ZoomIn } from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import { CheckMark } from '../../components/PixelIcons';
import { colors, fonts } from '../../theme';
import { AiScriptPopup, MusicSheet } from './_parts';

const PERIODS = ['전체', '이번주', '1주전', '2주전', '3주전'];

// 9 placeholder 썸네일 gradients (neutral art — CONTRACT: no new imagery).
const PHOTO_COLORS: [string, string][] = [
  ['#5B8C6E', '#3E6B52'],
  ['#3A5A7A', '#24405E'],
  ['#8A6A4A', '#5E4630'],
  ['#6A5A8A', '#42305E'],
  ['#4CAF50', '#2E7D32'],
  ['#B96A28', '#7A4A00'],
  ['#5B9BD5', '#2E5A9B'],
  ['#B04A4A', '#7A2E2E'],
  ['#7A4A9B', '#4A2E6B'],
];
const INITIAL_SELECTED = [0, 1, 3, 5];

export default function PhotoSelectScreen({ navigation, route }: any) {
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();

  const [period, setPeriod] = useState(0);
  const [selected, setSelected] = useState<number[]>(INITIAL_SELECTED);
  const [scriptOpen, setScriptOpen] = useState(false);
  const [musicOpen, setMusicOpen] = useState(false);

  const GAP = 4;
  const GRID_PAD = 16;
  const cell = Math.floor((width - GRID_PAD * 2 - GAP * 2) / 3);

  const toggle = (i: number) =>
    setSelected((cur) => (cur.includes(i) ? cur.filter((x) => x !== i) : [...cur, i]));

  const footerH = 46 + 10 + 52 + 20; // buttons row + gap + primary + top pad

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader />

      <ScrollView
        contentContainerStyle={[styles.body, { paddingBottom: footerH + insets.bottom + 40 }]}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.h1}>숏폼 생성</Text>
        <Text style={styles.sub}>퀘스트 인증 사진으로 숏폼 영상을 만들어보세요.</Text>

        {/* 기간 필터 칩 */}
        <View style={styles.chipsRow}>
          {PERIODS.map((label, i) => {
            const active = i === period;
            return (
              <SpringButton
                key={label}
                onPress={() => setPeriod(i)}
                pressScale={0.92}
                style={[styles.chip, active ? styles.chipActive : styles.chipIdle]}
              >
                <Text style={[styles.chipText, active ? styles.chipTextActive : styles.chipTextIdle]}>
                  {label}
                </Text>
              </SpringButton>
            );
          })}
        </View>

        {/* 3열 사진 그리드 */}
        <View style={styles.grid}>
          {PHOTO_COLORS.map((c, i) => {
            const sel = selected.includes(i);
            return (
              <Animated.View
                key={i}
                entering={ZoomIn.delay(30 + i * 40).duration(360)}
                style={{ width: cell, height: cell }}
              >
                <Pressable
                  onPress={() => toggle(i)}
                  style={[styles.cell, sel && styles.cellSelected]}
                >
                  <LinearGradient
                    colors={c}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 1 }}
                    style={StyleSheet.absoluteFill}
                  />
                  {sel ? (
                    <View style={styles.badge}>
                      <CheckMark size={12} color="#fff" />
                    </View>
                  ) : null}
                </Pressable>
              </Animated.View>
            );
          })}
        </View>

        <Text style={styles.count}>{selected.length}장 선택됨</Text>
      </ScrollView>

      {/* 하단 액션 (사진첩 fade → 배경으로 자연스럽게) */}
      <LinearGradient
        colors={['rgba(238,246,240,0)', colors.screenBg]}
        locations={[0, 0.3]}
        style={[styles.footer, { paddingBottom: insets.bottom + 12 }]}
      >
        <View style={styles.footerRow}>
          <View style={styles.footerHalf}>
            <SpringButton onPress={() => setScriptOpen(true)} style={styles.ghostBtn}>
              <Text style={styles.ghostText}>AI 대본</Text>
            </SpringButton>
          </View>
          <View style={styles.footerHalf}>
            <SpringButton onPress={() => setMusicOpen(true)} style={styles.ghostBtn}>
              <Text style={styles.ghostText}>음악</Text>
            </SpringButton>
          </View>
        </View>
        <SpringButton onPress={() => navigation.navigate('Generating')} style={styles.primaryBtn}>
          <Text style={styles.primaryText}>생성하기</Text>
        </SpringButton>
      </LinearGradient>

      <AiScriptPopup visible={scriptOpen} onClose={() => setScriptOpen(false)} />
      <MusicSheet visible={musicOpen} onClose={() => setMusicOpen(false)} />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 16, paddingTop: 16 },
  h1: { fontFamily: fonts.pixel, fontSize: 18, color: colors.primaryDark },
  sub: { fontSize: 13, color: '#888', marginTop: 2, marginBottom: 14, fontFamily: fonts.bodyR },

  chipsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 14 },
  chip: { borderRadius: 20, paddingHorizontal: 14, paddingVertical: 6 },
  chipActive: { backgroundColor: colors.primaryDark, borderWidth: 2, borderColor: colors.primaryDark },
  chipIdle: { backgroundColor: colors.white, borderWidth: 1, borderColor: colors.pixelBorder },
  chipText: { fontSize: 13, fontWeight: '700', fontFamily: fonts.bodyB },
  chipTextActive: { color: colors.parchment },
  chipTextIdle: { color: colors.primaryDark },

  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 4, marginBottom: 12 },
  cell: { flex: 1, borderRadius: 8, overflow: 'hidden', borderWidth: 2, borderColor: 'transparent' },
  cellSelected: { borderColor: colors.gold },
  badge: {
    position: 'absolute',
    top: 5,
    right: 5,
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: colors.gold,
    alignItems: 'center',
    justifyContent: 'center',
  },
  count: { textAlign: 'right', fontFamily: fonts.pixel, fontSize: 14, color: colors.gold },

  footer: { position: 'absolute', left: 0, right: 0, bottom: 0, paddingHorizontal: 16, paddingTop: 10 },
  footerRow: { flexDirection: 'row', gap: 10, marginBottom: 10 },
  footerHalf: { flex: 1 },
  ghostBtn: {
    height: 46,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: colors.pixelBorder,
    backgroundColor: colors.screenBg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  ghostText: { fontFamily: fonts.pixel, fontSize: 15, color: colors.primaryDark },
  primaryBtn: {
    height: 52,
    borderRadius: 8,
    backgroundColor: colors.gold,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: colors.gold,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 14,
    elevation: 5,
  },
  primaryText: { fontFamily: fonts.pixel, fontSize: 18, color: colors.primaryDark },
});
