/**
 * SCREEN 04-4 · 구매 내역 (back). 구매한 아이템 리스트(이미지·이름·정보·일자). 행 탭 →
 * 아이템 상세. 스태거 등장. 빈 상태: 빈 상자 + "상점 가기" 링크.
 */
import React from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import Animated, { FadeInDown } from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import { colors, fonts, shadow } from '../../theme';
import { HISTORY, HistoryItem, SHOP_ITEMS, ItemTile } from './_parts';

export default function PurchaseHistoryScreen({ navigation }: any) {
  const rows = HISTORY;

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title="구매 내역" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
        <Text style={styles.sub}>포인트를 모아 아이템을 구매하세요</Text>

        {rows.length === 0 ? (
          <View style={styles.empty}>
            <Text style={styles.emptyIcon}>📦</Text>
            <Text style={styles.emptyText}>아직 구매한 아이템이 없어요</Text>
            <Pressable hitSlop={8} onPress={() => navigation.navigate('Shop')}>
              <Text style={styles.emptyLink}>상점 가기</Text>
            </Pressable>
          </View>
        ) : (
          <View style={{ gap: 10 }}>
            {rows.map((h, i) => (
              <HistoryRow key={h.name + h.date} item={h} index={i} onPress={() => navigation.navigate('ItemDetail', { item: matchItem(h) })} />
            ))}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

function matchItem(h: HistoryItem) {
  return SHOP_ITEMS.find((s) => s.name === h.name) ?? SHOP_ITEMS[0];
}

function HistoryRow({ item, index, onPress }: { item: HistoryItem; index: number; onPress: () => void }) {
  return (
    <Animated.View entering={FadeInDown.delay(50 + index * 80).duration(360)}>
      <SpringButton style={styles.card} pressScale={0.985} onPress={onPress}>
        <ItemTile c1={item.c1} c2={item.c2} emoji={item.emoji} size={64} radius={10} emojiSize={26} diagonal />
        <View style={styles.info}>
          <Text style={styles.name} numberOfLines={1}>{item.name}</Text>
          <Text style={styles.metaInfo} numberOfLines={1}>{item.info}</Text>
          <Text style={styles.date}>{item.date}</Text>
        </View>
      </SpringButton>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 16, paddingTop: 18, paddingBottom: 28 },
  sub: { fontSize: 12, color: colors.textSecondary, marginBottom: 14, fontFamily: fonts.bodyR },

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
