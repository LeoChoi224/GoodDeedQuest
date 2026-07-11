/**
 * ItemListScreen (route: ItemList) — 스토리보드 #51. 마이페이지 > 아이템 목록.
 * 탭 [아이템 | 칭호] + 아이템 행(이미지·이름·설명·장착/해제). 장착중 배지. 무한 스크롤.
 */
import React, { useMemo, useRef, useState } from 'react';
import { View, Text, StyleSheet, FlatList } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeInDown } from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import SegmentedTabs from '../../components/SegmentedTabs';
import { colors, fonts, radii } from '../../theme';

type Item = { id: string; name: string; desc: string; equipped: boolean; type: 'item' | 'title' };

const ITEMS: Item[] = [
  { id: '1', name: '황금 왕관', desc: '영웅의 증표', equipped: false, type: 'item' },
  { id: '2', name: '선행 망토', desc: '선함을 두른 자의 외투', equipped: true, type: 'item' },
  { id: '3', name: '빛의 검', desc: '어둠을 밝히는 검', equipped: false, type: 'item' },
  { id: '4', name: '마을 수호자', desc: '지역사회를 지킨 칭호', equipped: false, type: 'title' },
  { id: '5', name: '선한 영웅', desc: '꾸준한 봉사의 증거', equipped: false, type: 'title' },
];

const MORE_ITEMS = ['수호의 방패', '치유의 물약', '용맹의 깃발', '축복의 반지'];
const MORE_TITLES = ['빛의 인도자', '나눔의 손길', '자연의 벗', '생명의 수호자'];
const MAX_PAGES = 3;

function makePage(page: number): Item[] {
  return Array.from({ length: 4 }, (_, k) => {
    const isItem = k % 2 === 0;
    const idx = (page + k) % 4;
    return {
      id: `p${page}-${k}`,
      name: (isItem ? MORE_ITEMS : MORE_TITLES)[idx],
      desc: '꾸준한 선행으로 얻은 보상',
      equipped: false,
      type: isItem ? 'item' : 'title',
    };
  });
}

export default function ItemListScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const [tab, setTab] = useState(0); // 0=아이템, 1=칭호
  const [items, setItems] = useState<Item[]>(ITEMS);
  const [loadingMore, setLoadingMore] = useState(false);
  const pageRef = useRef(0);

  const filtered = useMemo(
    () => items.filter((i) => (tab === 0 ? i.type === 'item' : i.type === 'title')),
    [items, tab]
  );

  const toggleEquip = (id: string) =>
    setItems((prev) => prev.map((p) => (p.id === id ? { ...p, equipped: !p.equipped } : p)));

  const loadMore = () => {
    if (loadingMore || pageRef.current >= MAX_PAGES) return;
    setLoadingMore(true);
    setTimeout(() => {
      pageRef.current += 1;
      setItems((prev) => [...prev, ...makePage(pageRef.current)]);
      setLoadingMore(false);
    }, 700);
  };

  const renderItem = ({ item, index }: { item: Item; index: number }) => (
    <Animated.View entering={FadeInDown.delay(Math.min(index, 6) * 55).duration(420)}>
      <View style={styles.itemRow}>
        <View style={styles.itemImg} />
        <View style={styles.itemInfo}>
          <View style={styles.nameRow}>
            <Text style={styles.itemName}>{item.name}</Text>
            {item.equipped ? (
              <View style={styles.equippedBadge}>
                <Text style={styles.equippedText}>장착중</Text>
              </View>
            ) : null}
          </View>
          <Text style={styles.itemDesc}>{item.desc}</Text>
        </View>
        <SpringButton
          style={[styles.equipBtn, item.equipped && styles.unequipBtn]}
          onPress={() => toggleEquip(item.id)}
        >
          <Text style={[styles.equipText, item.equipped && styles.unequipText]}>
            {item.equipped ? '해제' : '장착'}
          </Text>
        </SpringButton>
      </View>
    </Animated.View>
  );

  return (
    <View style={styles.root}>
      <StatusBar style="dark" />
      <HazeBackground />
      <MainHeader showBack title="아이템 목록" onBack={() => navigation.goBack()} />

      <Text style={styles.sub}>포인트를 모아 아이템을 구매하세요</Text>
      <View style={styles.tabsWrap}>
        <SegmentedTabs tabs={['아이템', '칭호']} index={tab} onChange={setTab} />
      </View>

      <FlatList
        data={filtered}
        keyExtractor={(i) => i.id}
        renderItem={renderItem}
        contentContainerStyle={{ paddingBottom: insets.bottom + 24 }}
        showsVerticalScrollIndicator={false}
        onEndReached={loadMore}
        onEndReachedThreshold={0.4}
        ListFooterComponent={
          loadingMore ? (
            <Text style={styles.loading}>불러오는 중…</Text>
          ) : (
            <View style={{ height: 12 }} />
          )
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  sub: { fontSize: 13, fontFamily: fonts.bodyR, color: colors.textSecondary, paddingHorizontal: 16, paddingTop: 10 },
  tabsWrap: { paddingHorizontal: 16, paddingVertical: 12 },
  itemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 14,
    backgroundColor: colors.white,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
  },
  itemImg: { width: 56, height: 56, borderRadius: 10, backgroundColor: colors.inputBorder },
  itemInfo: { flex: 1, gap: 4 },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  itemName: { fontSize: 15, fontFamily: fonts.bodyM, color: colors.primaryDark },
  itemDesc: { fontSize: 12, fontFamily: fonts.bodyR, color: colors.textSecondary },
  equippedBadge: { backgroundColor: 'rgba(76,175,80,0.12)', borderRadius: 99, paddingHorizontal: 6, paddingVertical: 2 },
  equippedText: { fontSize: 10, color: colors.xpGreen, fontFamily: fonts.bodyM },
  equipBtn: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 8, backgroundColor: colors.primaryDark },
  equipText: { fontSize: 13, fontFamily: fonts.bodyM, color: colors.parchment },
  unequipBtn: { backgroundColor: colors.white, borderWidth: 1, borderColor: colors.primaryDark },
  unequipText: { color: colors.primaryDark },
  loading: { textAlign: 'center', color: colors.textMuted, fontSize: 13, fontFamily: fonts.bodyR, paddingVertical: 16 },
});
