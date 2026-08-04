/**
 * SCREEN 04-4 · 구매 내역 (back). 구매한 아이템 리스트(이미지·이름·정보·일자). 행 탭 →
 * 아이템 상세. 스태거 등장. 빈 상태: 빈 상자 + "상점 가기" 링크.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, ActivityIndicator } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import Animated, { FadeInDown } from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import { colors, fonts, shadow } from '../../theme';
import { ItemTile } from './_parts';
import { getPurchaseHistory, PurchaseRecord } from '../../api/shop';

export default function PurchaseHistoryScreen({ navigation }: any) {
  const [purchases, setPurchases] = useState<PurchaseRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadHistory = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getPurchaseHistory();
      setPurchases(data);
    } catch (error) {
      console.error('구매 내역 로딩 오류:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title="구매 내역" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
        <Text style={styles.sub}>포인트를 모아 아이템을 구매하세요</Text>

        {loading ? (
          <View style={styles.loadingBox}>
            <ActivityIndicator size="large" color={colors.primaryDark} />
          </View>
        ) : purchases.length === 0 ? (
          <View style={styles.empty}>
            <Text style={styles.emptyIcon}>📦</Text>
            <Text style={styles.emptyText}>아직 구매한 아이템이 없어요</Text>
            <Pressable hitSlop={8} onPress={() => navigation.navigate('ShopHome')}>
              <Text style={styles.emptyLink}>상점 가기</Text>
            </Pressable>
          </View>
        ) : (
          <View style={{ gap: 10 }}>
            {purchases.map((h, i) => (
              <HistoryRow
                key={h.purchase_id || i}
                record={h}
                index={i}
                onPress={() => navigation.navigate('ItemDetail', { item: h.item, owned: true })}
              />
            ))}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

function HistoryRow({ record, index, onPress }: { record: PurchaseRecord; index: number; onPress: () => void }) {
  const item = record.item || {};
  const itemName = item.name || '프로필 테두리';
  const itemDesc = item.description || '아이템 · 장식';
  
  const formattedDate = record.purchased_at
    ? record.purchased_at.split('T')[0].replace(/-/g, '.')
    : '2026.07.26';
  const c1 = (item as any).c1 || '#4A90E2';
  const c2 = (item as any).c2 || '#50E3C2';
  const emoji = (item as any).emoji || '🖼️';
  return (
    <Animated.View entering={FadeInDown.delay(50 + index * 80).duration(360)}>
      <SpringButton style={styles.card} pressScale={0.985} onPress={onPress}>
        <ItemTile
          imageUrl={item.image_url}
          c1={c1}
          c2={c2}
          emoji={emoji}
          size={64}
          radius={10}
          emojiSize={26}
          diagonal
        />
        <View style={styles.info}>
          <Text style={styles.name} numberOfLines={1}>
            {itemName}
          </Text>
          <Text style={styles.metaInfo} numberOfLines={1}>
            {itemDesc}
          </Text>
          <Text style={styles.date}>{formattedDate}</Text>
        </View>
      </SpringButton>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 16, paddingTop: 18, paddingBottom: 28 },
  sub: { fontSize: 12, color: colors.textSecondary, marginBottom: 14, fontFamily: fonts.bodyR },

  loadingBox: { paddingVertical: 60, alignItems: 'center', justifyContent: 'center' },

  card: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: colors.white,
    borderRadius: 12,
    padding: 10,
    ...shadow.card,
    shadowOpacity: 0.06,
    shadowRadius: 10,
  },
  info: { flex: 1, minWidth: 0 },
  name: { fontSize: 15, fontWeight: '700', color: colors.textPrimary, fontFamily: fonts.bodyB },
  metaInfo: { fontSize: 13, color: colors.textSecondary, marginTop: 2, marginBottom: 3, fontFamily: fonts.bodyR },
  date: { fontSize: 12, color: colors.textMuted, fontFamily: fonts.bodyR },

  empty: { alignItems: 'center', paddingTop: 90, gap: 10 },
  emptyIcon: { fontSize: 46 },
  emptyText: { fontSize: 14, color: colors.textSecondary, fontFamily: fonts.bodyR },
  emptyLink: { fontSize: 14, color: colors.primaryDark, fontWeight: '700', textDecorationLine: 'underline', fontFamily: fonts.bodyB },
});