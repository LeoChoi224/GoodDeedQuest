/**
 * SCREEN 2 · 유저 목록 — route "UserList" (back). Search + 최신순 filter, infinite
 * scroll (onEndReached appends a page, dots loader), staggered card entrance, 차단유저
 * red label. Tapping a user opens the 차단 유저 팝업 (GamePopup + PopupButtons);
 * confirm (예 = 차단 해제) removes the label and fires a Toast.
 */
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { View, Text, StyleSheet, Pressable, FlatList } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { colors, fonts, radii } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import LightPopup from '../../components/LightPopup';
import EmptyState from '../../components/EmptyState';
import {
  AD, Avatar, SearchIcon, ChevronDown, LoadingDots, SkeletonCard, makeUsers, AdminUser,
} from './_parts';

const MAX_PAGES = 4;

type SortKey = 'recent' | 'name' | 'level';
const SORT_LABELS: Record<SortKey, string> = { recent: '최신순', name: '이름순', level: '레벨순' };
const SORT_ORDER: SortKey[] = ['recent', 'name', 'level'];

export default function UserListScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const [initialLoading, setInitialLoading] = useState(true);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loadingMore, setLoadingMore] = useState(false);
  const [sort, setSort] = useState<SortKey>('recent');
  const [sortOpen, setSortOpen] = useState(false);
  const pageRef = useRef(0);

  useEffect(() => {
    const t = setTimeout(() => {
      setUsers(makeUsers(0));
      setInitialLoading(false);
    }, 700);
    return () => clearTimeout(t);
  }, []);

  const loadMore = () => {
    if (initialLoading || loadingMore || pageRef.current >= MAX_PAGES) return;
    setLoadingMore(true);
    setTimeout(() => {
      pageRef.current += 1;
      setUsers((prev) => [...prev, ...makeUsers(pageRef.current)]);
      setLoadingMore(false);
    }, 900);
  };

  // 유저 정렬 — 최신순(입력순) / 이름순(가나다) / 레벨순(높은순)
  const sortedUsers = useMemo(() => {
    const arr = [...users];
    if (sort === 'name') arr.sort((a, b) => a.name.localeCompare(b.name, 'ko'));
    else if (sort === 'level') arr.sort((a, b) => b.lv - a.lv);
    return arr;
  }, [users, sort]);

  const renderUser = ({ item, index }: { item: AdminUser; index: number }) => (
    <Animated.View entering={FadeInDown.delay(Math.min(index, 6) * 55).duration(450)}>
      <SpringButton
        style={styles.userCard}
        pressScale={0.985}
        onPress={() => navigation.navigate('UserDetail', { user: item, moderation: true })}
      >
        <Avatar av={item.av} />
        <View style={styles.userInfo}>
          <Text style={styles.userName}>{item.name}</Text>
          <Text style={styles.userTitle}>{item.title}</Text>
          <Text style={styles.userLv}>LV.{item.lv}</Text>
        </View>
        {item.blocked ? (
          <View style={styles.blockLabel}>
            <Text style={styles.blockLabelText}>차단유저</Text>
          </View>
        ) : null}
      </SpringButton>
    </Animated.View>
  );

  const filterHeader = (
    <View style={styles.filterRow}>
      <View style={styles.searchBox}>
        <SearchIcon />
        <Text style={styles.searchPlaceholder}>유저 검색</Text>
      </View>
      <Pressable style={styles.filterChip} onPress={() => setSortOpen(true)}>
        <Text style={styles.filterText}>{SORT_LABELS[sort]}</Text>
        <ChevronDown />
      </Pressable>
    </View>
  );

  return (
    <View style={styles.root}>
      <StatusBar style="dark" />
      <HazeBackground />
      <MainHeader showBack title="유저 목록" onBack={() => navigation.goBack()} />

      {initialLoading ? (
        <View style={styles.listPad}>
          {filterHeader}
          <View style={{ gap: 10 }}>
            {[0, 1, 2, 3, 4].map((i) => <SkeletonCard key={i} />)}
          </View>
        </View>
      ) : (
        <FlatList
          data={sortedUsers}
          keyExtractor={(u) => u.id}
          renderItem={renderUser}
          ListHeaderComponent={filterHeader}
          ListEmptyComponent={<EmptyState message="등록된 유저가 없습니다" />}
          contentContainerStyle={[styles.listPad, { paddingBottom: insets.bottom + 24 }]}
          ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
          showsVerticalScrollIndicator={false}
          onEndReached={loadMore}
          onEndReachedThreshold={0.4}
          ListFooterComponent={
            loadingMore ? <LoadingDots /> : pageRef.current >= MAX_PAGES ? <View style={{ height: 8 }} /> : <View style={{ height: 20 }} />
          }
        />
      )}

      {/* 유저 정렬 메뉴 */}
      <LightPopup visible={sortOpen} onClose={() => setSortOpen(false)} width={260}>
        <View style={styles.sortWrap}>
          <Text style={styles.sortTitle}>정렬 기준</Text>
          {SORT_ORDER.map((k) => (
            <Pressable
              key={k}
              style={styles.sortOption}
              onPress={() => {
                setSort(k);
                setSortOpen(false);
              }}
            >
              <Text style={[styles.sortOptionText, k === sort && styles.sortOptionActive]}>{SORT_LABELS[k]}</Text>
              {k === sort ? <Text style={styles.sortCheck}>✓</Text> : null}
            </Pressable>
          ))}
        </View>
      </LightPopup>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  listPad: { paddingHorizontal: 16, paddingTop: 14 },

  // 정렬 메뉴
  sortWrap: { alignSelf: 'stretch', width: '100%', marginTop: 2 },
  sortTitle: { fontFamily: fonts.pixel, fontSize: 15, color: colors.primaryDark, textAlign: 'center', marginBottom: 8 },
  sortOption: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 6,
    borderTopWidth: 1,
    borderTopColor: 'rgba(92,61,30,0.15)',
  },
  sortOptionText: { fontSize: 14, color: colors.textSecondary, fontFamily: fonts.bodyM },
  sortOptionActive: { color: colors.primaryDark, fontFamily: fonts.bodyB, fontWeight: '700' },
  sortCheck: { color: colors.gold, fontSize: 14, fontFamily: fonts.bodyB },

  filterRow: { flexDirection: 'row', gap: 8, marginBottom: 14 },
  searchBox: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.pixelBorder,
    borderRadius: 24,
    paddingVertical: 10,
    paddingHorizontal: 14,
  },
  searchPlaceholder: { fontSize: 13, color: colors.textMuted, fontFamily: fonts.bodyR },
  filterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.pixelBorder,
    borderRadius: 8,
    paddingHorizontal: 10,
  },
  filterText: { fontSize: 12, fontWeight: '700', color: colors.primaryDark, fontFamily: fonts.bodyB },

  userCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: AD.cardBorder,
    borderRadius: 12,
    padding: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  userInfo: { flex: 1, minWidth: 0 },
  userName: { fontSize: 15, fontWeight: '600', color: colors.primaryDark, fontFamily: fonts.bodyM },
  userTitle: { fontSize: 13, color: colors.gold, fontFamily: fonts.bodyR, marginTop: 1 },
  userLv: { fontFamily: fonts.pixel, fontSize: 12, color: AD.muted, marginTop: 1 },
  blockLabel: { backgroundColor: AD.red, borderRadius: 4, paddingHorizontal: 8, paddingVertical: 3 },
  blockLabelText: { color: colors.white, fontSize: 12, fontFamily: fonts.bodyM },

  popupBody: { alignSelf: 'stretch' },
  popupUserRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: AD.popupUserBg,
    borderRadius: 8,
    padding: 12,
    marginBottom: 14,
  },
  popupUserName: { fontSize: 15, fontWeight: '600', color: AD.popupCream, fontFamily: fonts.bodyM },
  popupUserSub: { fontSize: 13, color: colors.gold, fontFamily: fonts.bodyR, marginTop: 1 },
  popupInfoBox: { backgroundColor: AD.popupInfoBg, borderRadius: 8, padding: 12, marginBottom: 12 },
  popupInfoText: { fontSize: 14, color: AD.popupInfoText, fontFamily: fonts.bodyR, lineHeight: 24 },
  detailLinkWrap: { alignItems: 'center', marginBottom: 16 },
  detailLink: { fontSize: 14, color: colors.gold, textDecorationLine: 'underline', fontFamily: fonts.bodyR },
  popupQuestion: { textAlign: 'center', fontFamily: fonts.pixel, fontSize: 15, color: AD.popupCream, marginBottom: 2 },
});
