/**
 * SCREEN 04-1 · 상점 메인 — 상점 tab ROOT (MainHeader, no back). 등급 프레임 아이템
 * 그리드(리스트) + 골드 코인 파우치(보유 포인트). 아이템 탭 → 상세, 구매 목록 → 구매 내역,
 * 보유 아이템 → 아이템 목록. 카드 스태거 등장 + 스프링 프레스.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, RefreshControl, Alert } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import Animated, { FadeInDown } from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import { colors, fonts, shadow } from '../../theme';
import { SHOP_ITEMS, ShopItem, ItemTile, PixelCoin, ChevronRight, PointsPouch } from './_parts';
import { getShopItems, getPurchaseHistory } from '../../api/shop';
import { getMyProfile } from '../../api/auth';

export default function ShopScreen({ navigation }: any) {
  
  const [items, setItems] = useState<ShopItem[]>([]);
  const [userPoints, setUserPoints] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const loadItems = useCallback(async () => {
      try {
        setLoading(true);

        const [allProducts, profile, history] = await Promise.all([
        getShopItems(),
        getMyProfile().catch(() => null),
        getPurchaseHistory().catch(() => []),
      ]);

      // 1. 실시간 포인트 바인딩 (res.point_balance 예외 가드)
      if (profile && profile.point_balance !== undefined) {
        console.log(profile.point_balance)
        setUserPoints(profile.point_balance);
      }

      // 2. 이미 구매한 아이템 ID 추출 후 상점 목록에서 제외 (미구매 상품만 노출)
      const purchasedIds = new Set((history || []).map((h: any) => h.item_id));
      const unownedItems = (allProducts || []).filter((it) => !purchasedIds.has(it.item_id));

      setItems(unownedItems);
      } catch (error: any) {
        console.error('상점 목록 로딩 오류:', error);
        Alert.alert('알림', '상점 상품 목록을 불러오지 못했습니다.');
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    }, []);

    useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      loadItems();
    });
    loadItems();
    return unsubscribe;
  }, [navigation, loadItems]);
  
    const onRefresh = () => {
      setRefreshing(true);
      loadItems();
    };


  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader />

      <ScrollView
        contentContainerStyle={styles.body}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[colors.primaryDark]} />
        }
      >
        {/* title + points pouch */}
        <View style={styles.topRow}>
          <View style={{ flex: 1 }}>
            <Text style={styles.h1}>상점 페이지</Text>
            <Text style={styles.sub}>포인트를 모아 아이템을 구매하세요</Text>
          </View>
          <PointsPouch points={`${userPoints.toLocaleString()} P`} />
        </View>

        {/* actions — 보유 아이템 / 구매 목록 */}
        <View style={styles.actions}>
          {/* ⭐ 수정: 자체 Inventory 화면(더미 데이터, 죽은 화면) 대신 마이페이지 아이템 목록의 "아이템" 탭으로 이동 */}
          <SpringButton
            style={[styles.actionBtn, styles.actionGhost]}
            pressScale={0.94}
            onPress={() => navigation.navigate('My', { screen: 'ItemList', params: { initialTab: 'item' } })}
          >
            <Text style={styles.actionGhostText}>보유 아이템</Text>
          </SpringButton>
          <SpringButton style={[styles.actionBtn, styles.actionSolid]} pressScale={0.94} onPress={() => navigation.navigate('PurchaseHistory')}>
            <Text style={styles.actionSolidText}>구매 목록</Text>
          </SpringButton>
        </View>

        {/* item list */}
        {loading && !refreshing ? (
          <View style={styles.loadingBox}>
            <ActivityIndicator size="large" color={colors.primaryDark} />
            <Text style={styles.loadingText}>상품 목록을 불러오는 중...</Text>
          </View>
        ) : (
          <View style={{ gap: 10 }}>
            {items.length === 0 ? (
              <View style={styles.emptyContainer}>
                <Text style={styles.emptyText}>모든 아이템을 구매하여 보유 중입니다!</Text>
              </View>
            ) : (
              items.map((it, i) => (
                <ShopRow
                  key={it.item_id || i}
                  item={it}
                  index={i}
                  onPress={() => navigation.navigate('ItemDetail', { item: it, itemId: it.item_id })}
                />
              ))
            )}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

function ShopRow({ item, index, onPress }: { item: ShopItem; index: number; onPress: () => void }) {
  const rareColor = (item as any).rare || colors.primaryDark;
  const rareLabel = (item as any).rareLabel || '테두리';
  
  return (
    <Animated.View entering={FadeInDown.delay(50 + index * 70).duration(360)}>
      <SpringButton style={[styles.card, { borderLeftColor: (item as any).rare || colors.primaryDark }]} pressScale={0.985} onPress={onPress}>
        <ItemTile
          imageUrl={(item as any).image_url} // ========================================== [추가] 백엔드 테두리 이미지 바인딩
          c1={(item as any).c1 || '#4A90E2'}
          c2={(item as any).c2 || '#50E3C2'}
          emoji={(item as any).emoji || '🖼️'}
          size={66}
          radius={12}
          emojiSize={30}
          frame={rareColor}
          epic={(item as any).epic}
          shine
        />
        <View style={styles.cardInfo}>
          <View style={styles.nameRow}>
            <Text style={styles.name} numberOfLines={1}>{item.name}</Text>
            <View style={[styles.rareBadge, { backgroundColor: rareColor }]}>
              <Text style={styles.rareBadgeText}>{rareLabel}</Text>
            </View>
          </View>
          <Text style={styles.desc} numberOfLines={1}>
            {(item as any).description || item.desc}
          </Text>
          <View style={styles.priceChip}>
            <PixelCoin size={13} />
            <Text style={styles.priceChipText}>{((item as any).price_point || item.priceNum || 0).toLocaleString()} P</Text>
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
