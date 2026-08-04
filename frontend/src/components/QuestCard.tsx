/**
 * RPG 퀘스트 카드 — ported from questcard.dc.html. Metallic gold frame → deep-teal
 * card → double-ring crest (category glyph, bob) → DotGothic16 title → gold flourish
 * divider → EXP/포인트 reward pills. mode 'active' adds a 진행중 badge + frame glow.
 * Radial gradients approximated with vertical LinearGradients (expo-linear-gradient).
 */
import React, { useEffect } from 'react';
import { View, Text, Image, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  withDelay,
  Easing,
  FadeInDown,
} from 'react-native-reanimated';
import { colors, fonts, CATEGORY_COLORS, CATEGORY_GLYPHS } from '../theme';

export type QuestCardProps = {
  category?: string;
  mode?: 'idle' | 'active';
  title: string;
  desc?: string;
  point?: number | string;
  exp?: number | string;
  showDesc?: boolean;
};

const SPARKS = [
  { left: '9%', top: '20%', size: 16, delay: 0 },
  { left: '85%', top: '30%', size: 11, delay: 700 },
  { left: '15%', top: '58%', size: 10, delay: 1300 },
  { left: '88%', top: '64%', size: 13, delay: 400 },
];

function Crest({ category }: { category: string }) {
  const bob = useSharedValue(0);
  useEffect(() => {
    bob.value = withRepeat(withTiming(1, { duration: 1700, easing: Easing.inOut(Easing.ease) }), -1, true);
  }, []);
  const style = useAnimatedStyle(() => ({ transform: [{ translateY: -3 * bob.value }] }));
  return (
    <View style={styles.crestWrap}>
      <LinearGradient colors={['#F8E6A6', '#C9A44C', '#9A7526']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.crestRing}>
        <LinearGradient colors={['#0A4F55', '#022528']} start={{ x: 0.5, y: 0.2 }} end={{ x: 0.5, y: 1 }} style={styles.crestInner}>
          <Animated.View style={style}>
            <Image source={CATEGORY_GLYPHS[category]} style={styles.emblem} />
          </Animated.View>
        </LinearGradient>
      </LinearGradient>
    </View>
  );
}

function Spark({ def }: { def: (typeof SPARKS)[number] }) {
  const v = useSharedValue(0);
  useEffect(() => {
    v.value = withDelay(def.delay, withRepeat(withTiming(1, { duration: 1400, easing: Easing.inOut(Easing.ease) }), -1, true));
  }, []);
  const st = useAnimatedStyle(() => ({ opacity: 0.15 + v.value * 0.8, transform: [{ scale: 0.55 + v.value * 0.55 }] }));
  return (
    <Animated.Text style={[{ position: 'absolute', left: def.left as any, top: def.top as any, fontSize: def.size, color: '#F2D783' }, st]}>
      ✦
    </Animated.Text>
  );
}

export default function QuestCard({ category = 'environment', mode = 'idle', title, desc, point = 30, exp = 20, showDesc = false }: QuestCardProps) {
  const catKey = CATEGORY_COLORS[category] ? category : 'environment';
  const cat = CATEGORY_COLORS[catKey];
  const active = mode === 'active';

  return (
    <View>
      <Animated.View entering={FadeInDown.duration(420)} style={styles.frameOuter}>
        <LinearGradient colors={['#F8E6A6', '#D8B45E', '#9A7526', '#F2D783']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.frameGrad}>
          <LinearGradient colors={['#0A4F55', '#033236', '#022528']} start={{ x: 0.5, y: 0 }} end={{ x: 0.5, y: 1 }} style={[styles.green, active && styles.greenGlow]}>
            {SPARKS.map((s, i) => (
              <Spark key={i} def={s} />
            ))}

            {active ? (
              <View style={styles.badge}>
                <View style={styles.badgeDot} />
                <Text style={styles.badgeText}>진행중</Text>
              </View>
            ) : null}

            <Text style={styles.title}>{title}</Text>

            <View style={styles.divider}>
              <LinearGradient colors={['transparent', '#D8B860']} start={{ x: 0, y: 0.5 }} end={{ x: 1, y: 0.5 }} style={styles.divLine} />
              <View style={styles.diamond} />
              <LinearGradient colors={['#D8B860', 'transparent']} start={{ x: 0, y: 0.5 }} end={{ x: 1, y: 0.5 }} style={styles.divLine} />
            </View>

            <View style={styles.pills}>
              <View style={styles.pill}>
                <Text style={[styles.pillLabel, { color: cat.deep }]}>EXP</Text>
                <Text style={styles.pillVal}>+{exp}</Text>
              </View>
              <View style={styles.pill}>
                <Text style={[styles.pillLabel, { color: '#8A6A2E' }]}>포인트</Text>
                <Text style={styles.pillVal}>+{point}</Text>
              </View>
            </View>
          </LinearGradient>
        </LinearGradient>
      </Animated.View>

      <Crest category={catKey} />

      {showDesc && desc ? (
        <Animated.View entering={FadeInDown.delay(200)} style={styles.descWrap}>
          <View style={styles.descHead}>
            <View style={styles.descBar} />
            <Text style={styles.descTitle}>퀘스트 설명</Text>
          </View>
          <Text style={styles.descBody}>{desc}</Text>
        </Animated.View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  frameOuter: { marginTop: 46, borderRadius: 30 },
  frameGrad: { padding: 3, borderRadius: 30 },
  green: {
    borderRadius: 27,
    paddingTop: 74,
    paddingHorizontal: 22,
    paddingBottom: 26,
    overflow: 'hidden',
    borderWidth: 1.5,
    borderColor: 'rgba(242,215,131,0.4)',
  },
  greenGlow: {
    shadowColor: '#F2D783',
    shadowOpacity: 0.45,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 0 },
    elevation: 10,
  },
  badge: {
    position: 'absolute',
    top: 30,
    right: 22,
    zIndex: 3,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: 'rgba(143,224,168,0.12)',
    borderWidth: 1,
    borderColor: '#57C878',
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 4,
  },
  badgeDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: '#6FDC92' },
  badgeText: { fontSize: 11, fontWeight: '800', letterSpacing: 0.5, color: '#A8ECBF', fontFamily: fonts.bodyB },
  title: {
    textAlign: 'center',
    fontFamily: fonts.pixel,
    fontSize: 27,
    color: '#F5EFD8',
    lineHeight: 34,
    letterSpacing: 0.5,
    marginBottom: 14,
    textShadowColor: 'rgba(0,0,0,0.45)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 0,
  },
  divider: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9, marginBottom: 22 },
  divLine: { width: 52, height: 1 },
  diamond: { width: 6, height: 6, transform: [{ rotate: '45deg' }], backgroundColor: '#EBCB78' },
  pills: { flexDirection: 'row', justifyContent: 'center', gap: 12 },
  pill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    backgroundColor: '#F6ECCF',
    borderWidth: 1,
    borderColor: '#D8B860',
    borderRadius: 999,
    paddingHorizontal: 18,
    paddingVertical: 10,
  },
  pillLabel: { fontSize: 15, fontWeight: '800', fontFamily: fonts.bodyB },
  pillVal: { fontSize: 15, fontWeight: '800', color: '#A9822E', fontFamily: fonts.bodyB },
  crestWrap: { position: 'absolute', top: 12, left: 0, right: 0, alignItems: 'center', zIndex: 5 },
  crestRing: { width: 94, height: 94, borderRadius: 47, padding: 3 },
  crestInner: { flex: 1, borderRadius: 44, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: 'rgba(242,215,131,0.5)' },
  emblem: { width: 56, height: 56 },
  descWrap: { marginTop: 22, paddingHorizontal: 6 },
  descHead: { flexDirection: 'row', alignItems: 'center', gap: 7, marginBottom: 9 },
  descBar: { width: 4, height: 14, borderRadius: 2, backgroundColor: colors.primaryDark },
  descTitle: { fontSize: 14, fontWeight: '800', color: colors.textPrimary, fontFamily: fonts.bodyB },
  descBody: { fontSize: 14, color: '#5B6B60', lineHeight: 24, fontFamily: fonts.bodyR },
});
