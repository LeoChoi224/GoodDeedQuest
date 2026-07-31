/**
 * ItemListScreen (route: ItemList) — 스토리보드 #51. 마이페이지 > 아이템 목록.
 * 탭 [아이템 | 칭호] + 행(이미지·이름·설명·장착/해제). 장착중 배지.
 * ⭐ 수정: 아이템 탭 = 실 데이터(api/shop.ts, 구매 내역=보유 아이템). 상점 "보유 아이템" 버튼이
 *          여기로 이동해온다 (route.params.initialTab).
 * 칭호 탭 = 실 데이터(api/badge.ts). 카테고리별로 묶어서 전체 노출, 미보유는 장착버튼 비활성화,
 *          보유 칭호 장착 시 단일 슬롯(자동 해제) — 백엔드 PATCH /badges/{id}/equip이 이미 그렇게 동작함.
 */
import React, { useEffect, useMemo, useState } from 'react';
import { View, Text, Image, StyleSheet, FlatList, SectionList, ActivityIndicator } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeInDown } from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import SegmentedTabs from '../../components/SegmentedTabs';
import { useToast } from '../../components/Toast';
import { colors, fonts, radii } from '../../theme';
import { getAllBadges, getMyBadges, equipBadge, unequipBadge, type Badge } from '../../api/badge';
import { getPurchaseHistory, equipShopItem, unequipShopItem, type PurchaseRecord } from '../../api/shop';
import { getFullImageUrl } from '../shop/_parts'; // ⭐ 수정: 아이템 image_url이 상대경로(/static/...)로 오므로 백엔드 base URL을 붙여야 함

// ⭐ 수정: 칭호 = Badge(is_owned) + 내 장착 상태(is_equipped) 병합
type BadgeVM = Badge & { is_equipped: boolean };

export default function ItemListScreen({ navigation, route }: any) {
  const insets = useSafeAreaInsets();
  const toast = useToast();
  // ⭐ 수정: 상점 "보유 아이템" 버튼이 initialTab: 'item' | 'title' 파라미터로 넘어온다
  const initialTab = route?.params?.initialTab === 'title' ? 1 : 0;
  const [tab, setTab] = useState(initialTab); // 0=아이템, 1=칭호

  // ⭐ 수정: 아이템 탭 상태 — 구매 내역(=보유 아이템)
  const [purchases, setPurchases] = useState<PurchaseRecord[]>([]);
  const [itemsLoading, setItemsLoading] = useState(true);
  const [itemsError, setItemsError] = useState(false);
  const [pendingItemId, setPendingItemId] = useState<number | null>(null);

  const loadPurchases = async (showSpinner = true) => {
    if (showSpinner) setItemsLoading(true);
    setItemsError(false);
    try {
      setPurchases(await getPurchaseHistory());
    } catch (err) {
      setItemsError(true);
    } finally {
      if (showSpinner) setItemsLoading(false);
    }
  };

  useEffect(() => {
    loadPurchases();
  }, []);

  const toggleItemEquip = async (purchase: PurchaseRecord) => {
    if (pendingItemId !== null) return;
    setPendingItemId(purchase.item_id);
    try {
      if (purchase.is_equipped) {
        await unequipShopItem(purchase.item_id);
        toast.show('아이템을 해제했어요.');
      } else {
        await equipShopItem(purchase.item_id);
        toast.show(`"${purchase.item.name}" 아이템을 장착했어요.`);
      }
      // ⭐ 수정: 서버가 유저당 1개만 장착되도록 보장하므로, 로컬 조작 없이 서버 상태를 그대로 재조회
      await loadPurchases(false);
    } catch (err) {
      toast.show('아이템 변경에 실패했어요.');
    } finally {
      setPendingItemId(null);
    }
  };

  // ⭐ 수정: 칭호 탭 상태
  const [badges, setBadges] = useState<BadgeVM[]>([]);
  const [badgesLoading, setBadgesLoading] = useState(true);
  const [badgesError, setBadgesError] = useState(false);
  const [pendingBadgeId, setPendingBadgeId] = useState<number | null>(null);

  // ⭐ 수정: showSpinner=false로 호출하면 전체 로딩 스피너 없이 조용히 최신 상태만 반영
  // (장착/해제 직후 재조회용 — 서버가 기본 칭호를 자동 재장착했을 수도 있으므로 로컬에서
  // 직접 상태를 조작하지 않고 항상 서버 응답을 그대로 반영한다)
  const loadBadges = async (showSpinner = true) => {
    if (showSpinner) setBadgesLoading(true);
    setBadgesError(false);
    try {
      const [all, mine] = await Promise.all([getAllBadges(), getMyBadges()]);
      const equippedIds = new Set(mine.filter((m) => m.is_equipped).map((m) => m.badge_id));
      setBadges(all.map((b) => ({ ...b, is_equipped: equippedIds.has(b.badge_id) })));
    } catch (err) {
      setBadgesError(true);
    } finally {
      if (showSpinner) setBadgesLoading(false);
    }
  };

  useEffect(() => {
    loadBadges();
  }, []);

  // ⭐ 수정: 카테고리(badge_category) 등장 순서대로 섹션 구성
  const badgeSections = useMemo(() => {
    const order: string[] = [];
    const map = new Map<string, BadgeVM[]>();
    for (const b of badges) {
      if (!map.has(b.badge_category)) {
        map.set(b.badge_category, []);
        order.push(b.badge_category);
      }
      map.get(b.badge_category)!.push(b);
    }
    return order.map((category) => ({ title: category, data: map.get(category)! }));
  }, [badges]);

  const toggleBadgeEquip = async (badge: BadgeVM) => {
    if (!badge.is_owned || pendingBadgeId !== null) return;
    setPendingBadgeId(badge.badge_id);
    try {
      if (badge.is_equipped) {
        await unequipBadge(badge.badge_id);
        toast.show('칭호를 해제했어요.');
      } else {
        await equipBadge(badge.badge_id);
        toast.show(`"${badge.name}" 칭호를 장착했어요.`);
      }
      // ⭐ 수정: 로컬에서 직접 상태를 조작하지 않고 서버에서 다시 받아온다 — 해제로
      // 장착중인 칭호가 하나도 안 남으면 서버가 기본 칭호를 자동 재장착하기 때문에,
      // 그 결과를 그대로 반영해야 화면과 서버 상태가 항상 일치한다.
      await loadBadges(false);
    } catch (err) {
      toast.show('칭호 변경에 실패했어요.');
    } finally {
      setPendingBadgeId(null);
    }
  };

  // ⭐ 수정: 아이템(프로필 테두리) 행 — 전부 보유 중인 것만 조회되므로 비활성화 케이스는 처리중일 때뿐
  const renderPurchaseRow = ({ item: p, index }: { item: PurchaseRecord; index: number }) => {
    const disabled = pendingItemId !== null;
    return (
      <Animated.View entering={FadeInDown.delay(Math.min(index, 6) * 55).duration(420)}>
        <View style={styles.itemRow}>
          <Image source={{ uri: getFullImageUrl(p.item.image_url) }} style={styles.itemImg} />
          <View style={styles.itemInfo}>
            <View style={styles.nameRow}>
              <Text style={styles.itemName}>{p.item.name}</Text>
              {p.is_equipped ? (
                <View style={styles.equippedBadge}>
                  <Text style={styles.equippedText}>장착중</Text>
                </View>
              ) : null}
            </View>
            <Text style={styles.itemDesc}>{p.item.description}</Text>
          </View>
          <SpringButton
            disabled={disabled}
            style={[styles.equipBtn, p.is_equipped && styles.unequipBtn]}
            onPress={() => toggleItemEquip(p)}
          >
            <Text style={[styles.equipText, p.is_equipped && styles.unequipText]}>
              {p.is_equipped ? '해제' : '장착'}
            </Text>
          </SpringButton>
        </View>
      </Animated.View>
    );
  };

  // ⭐ 수정: 칭호 행 — 미보유는 장착버튼 비활성화(선택 불가), 보유+장착중이면 해제 가능
  const renderBadgeRow = ({ item: b, index }: { item: BadgeVM; index: number }) => {
    const disabled = !b.is_owned || pendingBadgeId !== null;
    return (
      <Animated.View entering={FadeInDown.delay(Math.min(index, 6) * 55).duration(420)}>
        <View style={[styles.itemRow, !b.is_owned && styles.itemRowLocked]}>
          <Image source={{ uri: b.icon_url }} style={styles.itemImg} />
          <View style={styles.itemInfo}>
            <View style={styles.nameRow}>
              <Text style={[styles.itemName, !b.is_owned && styles.itemNameLocked]}>{b.name}</Text>
              {b.is_equipped ? (
                <View style={styles.equippedBadge}>
                  <Text style={styles.equippedText}>장착중</Text>
                </View>
              ) : null}
            </View>
            <Text style={styles.itemDesc}>{b.description}</Text>
          </View>
          <SpringButton
            disabled={disabled}
            style={[
              styles.equipBtn,
              b.is_equipped && styles.unequipBtn,
              !b.is_owned && styles.disabledBtn,
            ]}
            onPress={() => toggleBadgeEquip(b)}
          >
            <Text
              style={[
                styles.equipText,
                b.is_equipped && styles.unequipText,
                !b.is_owned && styles.disabledText,
              ]}
            >
              {b.is_equipped ? '해제' : '장착'}
            </Text>
          </SpringButton>
        </View>
      </Animated.View>
    );
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title="아이템 목록" onBack={() => navigation.goBack()} />

      <Text style={styles.sub}>포인트를 모아 아이템을 구매하세요</Text>
      <View style={styles.tabsWrap}>
        <SegmentedTabs tabs={['아이템', '칭호']} index={tab} onChange={setTab} />
      </View>

      {tab === 0 ? (
        itemsLoading ? (
          <View style={styles.stateBox}>
            <ActivityIndicator color={colors.primaryDark} />
          </View>
        ) : itemsError ? (
          <View style={styles.stateBox}>
            <Text style={styles.stateText}>아이템을 불러오지 못했어요</Text>
          </View>
        ) : purchases.length === 0 ? (
          <View style={styles.stateBox}>
            <Text style={styles.stateText}>보유한 아이템이 없습니다</Text>
          </View>
        ) : (
          <FlatList
            data={purchases}
            keyExtractor={(p) => String(p.purchase_id)}
            renderItem={renderPurchaseRow}
            contentContainerStyle={{ paddingBottom: insets.bottom + 24 }}
            showsVerticalScrollIndicator={false}
          />
        )
      ) : badgesLoading ? (
        <View style={styles.stateBox}>
          <ActivityIndicator color={colors.primaryDark} />
        </View>
      ) : badgesError ? (
        <View style={styles.stateBox}>
          <Text style={styles.stateText}>칭호를 불러오지 못했어요</Text>
        </View>
      ) : (
        <SectionList
          sections={badgeSections}
          keyExtractor={(b) => String(b.badge_id)}
          renderItem={renderBadgeRow}
          renderSectionHeader={({ section }) => (
            <Text style={styles.sectionHeader}>{section.title}</Text>
          )}
          contentContainerStyle={{ paddingBottom: insets.bottom + 24 }}
          showsVerticalScrollIndicator={false}
          stickySectionHeadersEnabled={false}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  sub: { fontSize: 13, fontFamily: fonts.bodyR, color: colors.textSecondary, paddingHorizontal: 16, paddingTop: 10 },
  tabsWrap: { paddingHorizontal: 16, paddingVertical: 12 },
  sectionHeader: {
    fontSize: 13,
    fontFamily: fonts.bodyB,
    color: colors.textSecondary,
    backgroundColor: colors.screenBg,
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 6,
  },
  itemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 14,
    backgroundColor: colors.white,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
  },
  itemRowLocked: { opacity: 0.55 },
  itemImg: { width: 56, height: 56, borderRadius: 10, backgroundColor: colors.inputBorder },
  itemInfo: { flex: 1, gap: 4 },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  itemName: { fontSize: 15, fontFamily: fonts.bodyM, color: colors.primaryDark },
  itemNameLocked: { color: colors.textSecondary },
  itemDesc: { fontSize: 12, fontFamily: fonts.bodyR, color: colors.textSecondary },
  equippedBadge: { backgroundColor: 'rgba(76,175,80,0.12)', borderRadius: 99, paddingHorizontal: 6, paddingVertical: 2 },
  equippedText: { fontSize: 10, color: colors.xpGreen, fontFamily: fonts.bodyM },
  equipBtn: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 8, backgroundColor: colors.primaryDark },
  equipText: { fontSize: 13, fontFamily: fonts.bodyM, color: colors.parchment },
  unequipBtn: { backgroundColor: colors.white, borderWidth: 1, borderColor: colors.primaryDark },
  unequipText: { color: colors.primaryDark },
  disabledBtn: { backgroundColor: colors.inputBorder, borderWidth: 0 },
  disabledText: { color: colors.textSecondary },
  loading: { textAlign: 'center', color: colors.textMuted, fontSize: 13, fontFamily: fonts.bodyR, paddingVertical: 16 },
  stateBox: { paddingTop: 60, alignItems: 'center' },
  stateText: { fontSize: 13, fontFamily: fonts.bodyR, color: colors.textSecondary },
});
