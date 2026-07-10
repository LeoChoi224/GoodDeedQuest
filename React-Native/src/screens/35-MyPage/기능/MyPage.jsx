// 35-MyPage.js — React Native (Expo) 마이페이지
// 선행퀘스트 / 스토리보드 35번 기준 — 프로필 + 달성업적 타임라인 + 숏폼/구매목록 바로가기

import React, { useState, useRef, useEffect } from 'react';
import { View, Text, TouchableOpacity, ScrollView, Modal, Pressable, StyleSheet, Animated, Easing } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronRight, X, Check } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { CareIcon, GreenGradientBG, BottomNav, HamburgerMenu, HamburgerButton } from '../../../shared/기능/components';
import { styles } from '../디자인/MyPage.styles';

// 41번 스토리보드의 강조 이펙트(글로우 펄스 + 배지 팝 + 컨페티 버스트)를 이 팝업에 반영
const CONFETTI_COLORS = [COLORS.mint, COLORS.gold, COLORS.goldTint, '#5fb377'];
function buildConfetti() {
  const count = 10;
  return Array.from({ length: count }, (_, i) => {
    const angle = (360 / count) * i + (i % 2 === 0 ? 4 : -4);
    const rad = (angle * Math.PI) / 180;
    const dist = 34 + (i % 3) * 6;
    return { tx: Math.cos(rad) * dist, ty: Math.sin(rad) * dist, size: 4 + (i % 3), color: CONFETTI_COLORS[i % CONFETTI_COLORS.length], delay: 80 + i * 20 };
  });
}
const CONFETTI = buildConfetti();

function ConfettiDot({ tx, ty, size, color, delay, play }) {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    if (play) {
      anim.setValue(0);
      Animated.timing(anim, { toValue: 1, duration: 800, delay, easing: Easing.bezier(0.2, 0.65, 0.3, 1), useNativeDriver: true }).start();
    }
  }, [play]);
  const translateX = anim.interpolate({ inputRange: [0, 1], outputRange: [0, tx] });
  const translateY = anim.interpolate({ inputRange: [0, 1], outputRange: [0, ty] });
  const opacity = anim.interpolate({ inputRange: [0, 1], outputRange: [1, 0] });
  const scale = anim.interpolate({ inputRange: [0, 1], outputRange: [1, 0.3] });
  return (
    <Animated.View
      style={{ position: 'absolute', left: '50%', top: '50%', width: size, height: size, marginLeft: -size / 2, marginTop: -size / 2, borderRadius: 9999, backgroundColor: color, opacity, transform: [{ translateX }, { translateY }, { scale }] }}
    />
  );
}

function GlowPulse({ style, delay = 0 }) {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: 1, duration: 900, delay, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(anim, { toValue: 0, duration: 900, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, []);
  const opacity = anim.interpolate({ inputRange: [0, 1], outputRange: [0.5, 1] });
  const scale = anim.interpolate({ inputRange: [0, 1], outputRange: [0.9, 1.1] });
  return <Animated.View style={[style, { opacity, transform: [{ scale }] }]} />;
}

const ACHIEVEMENTS = [
  { id: 'a1', title: '노약자 자리 양보하기', date: '2026-07-01', completedAt: '2026-07-01 18:32', exp: 20, point: 30 },
  { id: 'a2', title: '헌혈하기', date: '2026-06-30', completedAt: '2026-06-30 11:05', exp: 30, point: 50 },
  { id: 'a3', title: '동네 쓰레기 줍기', date: '2026-06-25', completedAt: '2026-06-25 08:40', exp: 15, point: 20 },
];
const PAGE_LABELS = ['1', '2', '3', '4', '5', '…', '10'];

export default function MyPageScreen({ navigation }) {
  const [menuVisible, setMenuVisible] = useState(false);
  const [page, setPage] = useState(1);
  const [activeId, setActiveId] = useState(null);
  const active = activeId ? ACHIEVEMENTS.find((a) => a.id === activeId) : null;
  const badgeScale = useRef(new Animated.Value(0)).current;
  const badgeRotate = useRef(new Animated.Value(-25)).current;

  useEffect(() => {
    if (active) {
      badgeScale.setValue(0);
      badgeRotate.setValue(-25);
      Animated.sequence([
        Animated.parallel([
          Animated.spring(badgeScale, { toValue: 1, friction: 5, tension: 120, useNativeDriver: true }),
          Animated.timing(badgeRotate, { toValue: 0, duration: 550, easing: Easing.bezier(0.34, 1.56, 0.64, 1), useNativeDriver: true }),
        ]),
      ]).start();
    }
  }, [activeId]);

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <View style={styles.logoBadge}>
            <CareIcon size={18} />
          </View>
          <Text style={styles.logo}>선·퀘</Text>
          <View style={{ flex: 1 }} />
          <HamburgerButton onPress={() => setMenuVisible(true)} />
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <TouchableOpacity style={styles.profileCard} onPress={() => navigation.navigate('MyLevel')}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>민</Text>
            </View>
            <View style={{ flex: 1, minWidth: 0, gap: 4 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <Text style={styles.nickname}>민선행</Text>
                <View style={styles.titleTag}>
                  <Text style={styles.titleTagText}>따뜻한 이웃</Text>
                </View>
              </View>
              <View style={styles.levelTag}>
                <Text style={styles.levelTagText}>Lv.12</Text>
              </View>
            </View>
            <ChevronRight size={18} color={COLORS.inkMuted48} />
          </TouchableOpacity>

          <View style={{ gap: 12 }}>
            <Text style={styles.sectionTitle}>퀘스트 달성업적 및 타임라인</Text>
            {ACHIEVEMENTS.map((a) => (
              <View key={a.id} style={styles.achievementCard}>
                <View style={{ flex: 1, gap: 6 }}>
                  <View style={{ flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
                    <Text style={styles.achievementTitle}>{a.title}</Text>
                    <Text style={styles.achievementDate}>{a.date}</Text>
                  </View>
                  <TouchableOpacity style={styles.viewButton} onPress={() => setActiveId(a.id)}>
                    <Text style={styles.viewButtonText}>달성 업적 보기</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ))}
            <View style={styles.pagination}>
              {PAGE_LABELS.map((label, i) => {
                const isActive = label !== '…' && Number(label) === page;
                return (
                  <TouchableOpacity key={i} style={[styles.pageDot, isActive && { backgroundColor: COLORS.primary }]} onPress={() => label !== '…' && setPage(Number(label))}>
                    <Text style={[styles.pageDotText, isActive && { color: '#fff', fontWeight: '700' }]}>{label}</Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>

          <View style={{ flexDirection: 'row', gap: 10 }}>
            <TouchableOpacity style={styles.shortcutButton} onPress={() => navigation.navigate('ShortFormCreate')}>
              <Text style={styles.shortcutButtonText}>숏폼 만들기</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.shortcutButton} onPress={() => navigation.navigate('PurchaseList')}>
              <Text style={styles.shortcutButtonText}>구매 목록</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>

        <BottomNav navigation={navigation} active="mypage" translucent />
        <HamburgerMenu visible={menuVisible} onClose={() => setMenuVisible(false)} navigation={navigation} />

        <Modal statusBarTranslucent visible={!!active} transparent animationType="fade" onRequestClose={() => setActiveId(null)}>
          <View style={styles.achOverlay}>
            <Pressable style={StyleSheet.absoluteFill} onPress={() => setActiveId(null)} />
            {active && (
              <View style={styles.achCard}>
                <TouchableOpacity style={styles.achClose} onPress={() => setActiveId(null)} hitSlop={8}>
                  <X size={18} color="rgba(255,255,255,0.6)" />
                </TouchableOpacity>
                <View style={{ width: 88, height: 88, alignItems: 'center', justifyContent: 'center' }}>
                  <GlowPulse style={[styles.glowOuter]} />
                  <GlowPulse style={[styles.glowInner]} delay={300} />
                  {CONFETTI.map((c, i) => (
                    <ConfettiDot key={i} {...c} play={!!active} />
                  ))}
                  <Animated.View style={[styles.badgeCircle, { transform: [{ scale: badgeScale }, { rotate: badgeRotate.interpolate({ inputRange: [-25, 0], outputRange: ['-25deg', '0deg'] }) }] }]}>
                    <Check size={28} color={COLORS.primary} strokeWidth={3} />
                  </Animated.View>
                </View>
                <Text style={styles.achLabel}>달성 완료</Text>
                <Text style={styles.achTitle}>{active.title}</Text>
                <Text style={styles.achTime}>완료 시각 · {active.completedAt}</Text>
                <View style={{ flexDirection: 'row', gap: 8 }}>
                  <View style={styles.rewardBadge}>
                    <Text style={styles.rewardBadgeLabel}>EXP</Text>
                    <Text style={styles.rewardBadgeValue}>+{active.exp}</Text>
                  </View>
                  <View style={styles.rewardBadge}>
                    <Text style={styles.rewardBadgeLabel}>포인트</Text>
                    <Text style={styles.rewardBadgeValue}>+{active.point}</Text>
                  </View>
                </View>
                <TouchableOpacity style={styles.achConfirmButton} onPress={() => setActiveId(null)}>
                  <Text style={styles.achConfirmText}>확인 완료</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        </Modal>
      </SafeAreaView>
    </GreenGradientBG>
  );
}

