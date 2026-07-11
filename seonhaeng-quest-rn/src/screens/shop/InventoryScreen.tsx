/**
 * SCREEN 04-5 · 아이템 목록 (back). 보유 아이템/칭호 SegmentedTabs. 장착/해제 토글 —
 * 새로 장착하면 기존 장착 자동 해제, "장착중" 뱃지, useToast().show('장착 완료').
 * 행 탭 → 아이템 상세. 스태거 등장 + segmented 골드 필 슬라이드.
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import Animated, { FadeInDown } from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import SegmentedTabs from '../../components/SegmentedTabs';
import { useToast } from '../../components/Toast';
import { colors, fonts, shadow } from '../../theme';
import { OWNED_ITEMS, TITLES, OwnedItem, SHOP_ITEMS, ItemTile } from './_parts';

export default function InventoryScreen({ navigation }: any) {
  const toast = useToast();
  const [filter, setFilter] = useState(0); // 0 아이템 · 1 칭호
  const [equippedItem, setEquippedItem] = useState<string | null>('shield');
  const [equippedTitle, setEquippedTitle] = useState<string | null>('hero');

  const list = filter === 0 ? OWNED_ITEMS : TITLES;
  const equipped = filter === 0 ? equippedItem : equippedTitle;
  const setEquipped = filter === 0 ? setEquippedItem : setEquippedTitle;

  const toggle = (id: string) => {
    const isEquip = equipped !== id; // 새로 장착 시 기존 자동 해제 (single slot)
    setEquipped(isEquip ? id : null);
    toast.show(isEquip ? '장착 완료' : '해제 완료');
  };

  const openDetail = (o: OwnedItem) => {
    const match = SHOP_ITEMS.find((s) => s.name === o.name) ?? SHOP_ITEMS[0];
    navigation.navigate('ItemDetail', { item: match, owned: true });
  };

  return (
    <View style={styles.root}>
      <StatusBar style="dark" />
      <HazeBackground />
      <MainHeader showBack title="아이템 목록" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
        <Text style={styles.sub}>보유한 아이템 · 칭호를 장착해 보세요</Text>

        <View style={styles.tabs}>
          <SegmentedTabs tabs={['아이템', '칭호']} index={filter} onChange={setFilter} />
        </View>

        <View style={{ gap: 10 }}>
          {list.map((o, i) => (
            <OwnedRow
              key={filter + o.id}
              item={o}
              index={i}
              equipped={equipped === o.id}
              onToggle={() => toggle(o.id)}
              onPress={() => openDetail(o)}
            />
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

function OwnedRow({
  item,
  index,
  equipped,
  onToggle,
  onPress,
}: {
  item: OwnedItem;
  index: number;
  equipped: boolean;
  onToggle: () => void;
  onPress: () => void;
}) {
  return (
    <Animated.View entering={FadeInDown.delay(50 + index * 70).duration(360)}>
      <SpringButton style={styles.card} pressScale={0.985} onPress={onPress}>
        <ItemTile c1={item.c1} c2={item.c2} emoji={item.emoji} size={64} radius={10} emojiSize={26} diagonal />
        <View style={styles.info}>
          <View style={styles.nameRow}>
            <Text style={styles.name} numberOfLines={1}>{item.name}</Text>
            {equipped ? (
              <View style={styles.equipBadge}>
                <Text style={styles.equipBadgeText}>장착중</Text>
              </View>
            ) : null}
          </View>
          <Text style={styles.desc} numberOfLines={1}>{item.desc}</Text>
        </View>
        <SpringButton
          style={[styles.toggleBtn, { backgroundColor: equipped ? colors.danger : colors.primaryDark }]}
          pressScale={0.94}
          onPress={onToggle}
        >
          <Text style={styles.toggleText}>{equipped ? '해제' : '장착'}</Text>
        </SpringButton>
      </SpringButton>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 16, paddingTop: 18, paddingBottom: 28 },
  sub: { fontSize: 12, color: colors.textSecondary, marginBottom: 12, fontFamily: fonts.bodyR },
  tabs: { marginBottom: 16 },

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
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 3 },
  name: { flexShrink: 1, fontSize: 15, fontWeight: '700', color: colors.textPrimary, fontFamily: fonts.bodyB },
  equipBadge: { backgroundColor: colors.screenBg, borderRadius: 10, paddingHorizontal: 8, paddingVertical: 2 },
  equipBadgeText: { fontSize: 11, fontWeight: '700', color: colors.primaryDark, fontFamily: fonts.bodyB },
  desc: { fontSize: 13, color: colors.textSecondary, fontFamily: fonts.bodyR },

  toggleBtn: { width: 72, height: 36, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  toggleText: { color: colors.white, fontSize: 13, fontWeight: '700', fontFamily: fonts.bodyB },
});
