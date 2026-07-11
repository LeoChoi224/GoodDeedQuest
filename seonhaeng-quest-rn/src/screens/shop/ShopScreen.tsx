/**
 * SCREEN 04-1 · 상점 메인 — 상점 tab ROOT (MainHeader, no back). 등급 프레임 아이템
 * 그리드(리스트) + 골드 코인 파우치(보유 포인트). 아이템 탭 → 상세, 구매 목록 → 구매 내역,
 * 보유 아이템 → 아이템 목록. 카드 스태거 등장 + 스프링 프레스.
 */
import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import Animated, { FadeInDown } from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import { colors, fonts, shadow } from '../../theme';
import { SHOP_ITEMS, ShopItem, ItemTile, PixelCoin, ChevronRight, PointsPouch } from './_parts';

export default function ShopScreen({ navigation }: any) {
  return (
    <View style={styles.root}>
      <StatusBar style="dark" />
      <HazeBackground />
      <MainHeader />

      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
        {/* title + points pouch */}
        <View style={styles.topRow}>
          <View style={{ flex: 1 }}>
            <Text style={styles.h1}>상점 페이지</Text>
            <Text style={styles.sub}>포인트를 모아 아이템을 구매하세요</Text>
          </View>
          <PointsPouch />
        </View>

        {/* actions — 보유 아이템 / 구매 목록 */}
        <View style={styles.actions}>
          <SpringButton style={[styles.actionBtn, styles.actionGhost]} pressScale={0.94} onPress={() => navigation.navigate('Inventory')}>
            <Text style={styles.actionGhostText}>보유 아이템</Text>
          </SpringButton>
          <SpringButton style={[styles.actionBtn, styles.actionSolid]} pressScale={0.94} onPress={() => navigation.navigate('PurchaseHistory')}>
            <Text style={styles.actionSolidText}>구매 목록</Text>
          </SpringButton>
        </View>

        {/* item list */}
        <View style={{ gap: 10 }}>
          {SHOP_ITEMS.map((it, i) => (
            <ShopRow key={it.id} item={it} index={i} onPress={() => navigation.navigate('ItemDetail', { item: it })} />
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

function ShopRow({ item, index, onPress }: { item: ShopItem; index: number; onPress: () => void }) {
  return (
    <Animated.View entering={FadeInDown.delay(50 + index * 70).duration(360)}>
      <SpringButton style={[styles.card, { borderLeftColor: item.rare }]} pressScale={0.985} onPress={onPress}>
        <ItemTile c1={item.c1} c2={item.c2} emoji={item.emoji} size={66} radius={12} emojiSize={30} frame={item.rare} epic={item.epic} shine />
        <View style={styles.cardInfo}>
          <View style={styles.nameRow}>
            <Text style={styles.name} numberOfLines={1}>{item.name}</Text>
            <View style={[styles.rareBadge, { backgroundColor: item.rare }]}>
              <Text style={styles.rareBadgeText}>{item.rareLabel}</Text>
            </View>
          </View>
          <Text style={styles.desc} numberOfLines={1}>{item.desc}</Text>
          <View style={styles.priceChip}>
            <PixelCoin size={13} />
            <Text style={styles.priceChipText}>{item.price} P</Text>
          </View>
        </View>
        <ChevronRight />
      </SpringButton>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 16, paddingTop: 18, paddingBottom: 28 },

  topRow: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10, marginBottom: 14 },
  h1: { fontSize: 18, fontWeight: '700', color: colors.textPrimary, fontFamily: fonts.bodyB },
  sub: { fontSize: 12, color: colors.textSecondary, marginTop: 2, fontFamily: fonts.bodyR },

  actions: { flexDirection: 'row', justifyContent: 'flex-end', gap: 8, marginBottom: 16 },
  actionBtn: { height: 40, borderRadius: 10, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 16 },
  actionSolid: { backgroundColor: colors.primaryDark },
  actionSolidText: { color: colors.white, fontSize: 13, fontWeight: '700', fontFamily: fonts.bodyB },
  actionGhost: { backgroundColor: colors.white, borderWidth: 1, borderColor: colors.inputBorder },
  actionGhostText: { color: colors.textSecondary, fontSize: 13, fontWeight: '700', fontFamily: fonts.bodyB },

  card: {
    position: 'relative',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: colors.white,
    borderRadius: 14,
    padding: 11,
    borderLeftWidth: 5,
    ...shadow.card,
  },
  cardInfo: { flex: 1, minWidth: 0 },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 3 },
  name: { flexShrink: 1, fontSize: 15, fontWeight: '700', color: colors.textPrimary, fontFamily: fonts.bodyB },
  rareBadge: { borderRadius: 6, paddingHorizontal: 7, paddingVertical: 1 },
  rareBadgeText: { fontSize: 10, fontWeight: '800', color: colors.white, fontFamily: fonts.bodyB },
  desc: { fontSize: 12, color: colors.textSecondary, marginBottom: 6, fontFamily: fonts.bodyR },
  priceChip: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#FBF3D6',
    borderWidth: 1,
    borderColor: '#EBD9A0',
    borderRadius: 999,
    paddingHorizontal: 9,
    paddingVertical: 3,
  },
  priceChipText: { fontSize: 12, fontWeight: '800', color: '#B8860B', fontFamily: fonts.bodyB },
});
