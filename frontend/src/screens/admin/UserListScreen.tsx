import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';
import {
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { colors, fonts } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import EmptyState from '../../components/EmptyState';
import { useToast } from '../../components/Toast';
import {
  AD,
  Avatar,
  AVATARS,
  ChevronDown,
  LoadingDots,
  SearchIcon,
  SkeletonCard,
} from './_parts';
import {
  adminApi,
  AdminUser,
  AdminUserSort,
  getAdminErrorMessage,
} from './adminApi';

const LIMIT = 20;

type UserListOption = AdminUserSort | 'blocked';

const USER_LIST_OPTIONS: Array<{
  value: UserListOption;
  label: string;
}> = [
  { value: 'newest', label: '최신순' },
  { value: 'oldest', label: '오래된순' },
  { value: 'level', label: '레벨순' },
  { value: 'nickname', label: '닉네임순' },
  { value: 'trust', label: '신뢰도순' },
  { value: 'blocked', label: '차단 유저만 보기' },
];

export default function UserListScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const toast = useToast();

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [selectedOption, setSelectedOption] =
    useState<UserListOption>('newest');
  const [filterOpen, setFilterOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [more, setMore] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState('');

  const skipRef = useRef(0);
  const hasLoadedRef = useRef(false);
  const requestIdRef = useRef(0);
  const searchTimer =
    useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(
    async (reset = false) => {
      const requestId = ++requestIdRef.current;
      const nextSkip = reset ? 0 : skipRef.current;
      const blockedOnly = selectedOption === 'blocked';

      if (reset) {
        skipRef.current = 0;
        setMore(false);

        if (!hasLoadedRef.current) {
          setLoading(true);
        }
      } else {
        setMore(true);
      }

      setError('');

      try {
        const rows = await adminApi.getUsers({
          nickname: debouncedQuery || undefined,
          is_active: blockedOnly ? false : undefined,
          skip: nextSkip,
          limit: LIMIT,
          sort_by: blockedOnly ? 'newest' : selectedOption,
        });

        if (requestId !== requestIdRef.current) {
          return;
        }

        setUsers((previous) =>
          reset ? rows : [...previous, ...rows],
        );

        skipRef.current = nextSkip + rows.length;
        setHasMore(rows.length === LIMIT);
      } catch (loadError) {
        if (requestId === requestIdRef.current) {
          setError(getAdminErrorMessage(loadError));
        }
      } finally {
        if (requestId === requestIdRef.current) {
          hasLoadedRef.current = true;
          setLoading(false);
          setMore(false);
          setRefreshing(false);
        }
      }
    },
    [debouncedQuery, selectedOption],
  );

  useEffect(() => {
    if (searchTimer.current) {
      clearTimeout(searchTimer.current);
    }

    searchTimer.current = setTimeout(() => {
      setDebouncedQuery(query.trim());
    }, 400);

    return () => {
      if (searchTimer.current) {
        clearTimeout(searchTimer.current);
      }
    };
  }, [query]);

  useEffect(() => {
    void load(true);
  }, [load]);

  const toggle = async (user: AdminUser) => {
    setBusyId(user.user_id);

    try {
      const updated = await adminApi.updateUserActiveStatus(
        user.user_id,
        !user.is_active,
      );

      if (selectedOption === 'blocked' && updated.is_active) {
        setUsers((previous) =>
          previous.filter(
            (item) => item.user_id !== user.user_id,
          ),
        );

        skipRef.current = Math.max(0, skipRef.current - 1);
      } else {
        setUsers((previous) =>
          previous.map((item) =>
            item.user_id === user.user_id
              ? { ...item, ...updated }
              : item,
          ),
        );
      }

      toast.show(
        updated.is_active
          ? '사용자를 활성화했습니다'
          : '사용자를 비활성화했습니다',
      );
    } catch (toggleError) {
      toast.show(getAdminErrorMessage(toggleError));
    } finally {
      setBusyId(null);
    }
  };

  const selectedLabel =
    USER_LIST_OPTIONS.find(
      (option) => option.value === selectedOption,
    )?.label ?? '최신순';

  return (
    <View style={styles.root}>
      <StatusBar style="light" />

      <HazeBackground />

      <MainHeader
        showBack
        title="유저 목록"
        onBack={() => navigation.goBack()}
      />

      <View style={styles.toolbar}>
        <View style={styles.searchBox}>
          <SearchIcon />

          <TextInput
            value={query}
            onChangeText={setQuery}
            placeholder="닉네임 검색"
            placeholderTextColor={colors.textMuted}
            style={styles.input}
            autoCapitalize="none"
            returnKeyType="search"
          />
        </View>

        <View style={styles.filterWrap}>
          <SpringButton
            style={styles.filterButton}
            pressScale={0.97}
            onPress={() =>
              setFilterOpen((previous) => !previous)
            }
          >
            <Text
              numberOfLines={1}
              style={styles.filterButtonText}
            >
              {selectedLabel}
            </Text>

            <ChevronDown size={14} />
          </SpringButton>

          {filterOpen ? (
            <View style={styles.filterMenu}>
              {USER_LIST_OPTIONS.map((option) => {
                const active = selectedOption === option.value;

                return (
                  <SpringButton
                    key={option.value}
                    pressScale={0.98}
                    style={[
                      styles.filterOption,
                      active && styles.filterOptionActive,
                    ]}
                    onPress={() => {
                      setSelectedOption(option.value);
                      setFilterOpen(false);
                    }}
                  >
                    <Text
                      style={[
                        styles.filterOptionText,
                        active && styles.filterOptionTextActive,
                      ]}
                    >
                      {option.label}
                    </Text>
                  </SpringButton>
                );
              })}
            </View>
          ) : null}
        </View>
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      {loading ? (
        <View style={styles.pad}>
          <View style={styles.skeletonList}>
            {[0, 1, 2, 3, 4].map((item) => (
              <SkeletonCard key={item} />
            ))}
          </View>
        </View>
      ) : (
        <FlatList
          style={styles.list}
          data={users}
          keyExtractor={(user) => String(user.user_id)}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => {
                setRefreshing(true);
                setFilterOpen(false);
                void load(true);
              }}
            />
          }
          renderItem={({ item, index }) => (
            <Animated.View
              entering={FadeInDown.delay(
                Math.min(index, 6) * 45,
              ).duration(400)}
            >
              <SpringButton
                style={styles.card}
                onPress={() =>
                  navigation.navigate('UserDetail', {
                    userId: item.user_id,
                    user: item,
                    moderation: true,
                  })
                }
              >
                <Avatar
                  av={AVATARS[item.user_id % AVATARS.length]}
                />

                <View style={styles.info}>
                  <Text style={styles.name}>{item.nickname}</Text>

                  <Text style={styles.email}>{item.email}</Text>

                  <Text style={styles.lv}>
                    LV.{item.current_level} · 신뢰도{' '}
                    {item.trust_score}
                  </Text>
                </View>

                <SpringButton
                  disabled={busyId === item.user_id}
                  style={[
                    styles.statusBtn,
                    item.is_active
                      ? styles.activeBtn
                      : styles.inactiveBtn,
                  ]}
                  onPress={() => void toggle(item)}
                >
                  <Text style={styles.statusText}>
                    {busyId === item.user_id
                      ? '처리중'
                      : item.is_active
                        ? '활성'
                        : '비활성'}
                  </Text>
                </SpringButton>
              </SpringButton>
            </Animated.View>
          )}
          ItemSeparatorComponent={() => (
            <View style={styles.separator} />
          )}
          ListEmptyComponent={
            <EmptyState message="조회된 사용자가 없습니다" />
          }
          onScrollBeginDrag={() => setFilterOpen(false)}
          onEndReached={() => {
            if (!more && hasMore) {
              void load(false);
            }
          }}
          onEndReachedThreshold={0.4}
          ListFooterComponent={
            more ? (
              <LoadingDots />
            ) : (
              <View style={styles.footerSpace} />
            )
          }
          contentContainerStyle={[
            styles.pad,
            {
              paddingBottom: insets.bottom + 24,
            },
          ]}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.screenBg,
  },

  toolbar: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    paddingHorizontal: 16,
    paddingTop: 14,
    marginBottom: 14,
    zIndex: 20,
    elevation: 20,
  },

  searchBox: {
    flex: 3,
    minWidth: 0,
    height: 44,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.pixelBorder,
    borderRadius: 22,
    paddingHorizontal: 14,
  },

  input: {
    flex: 1,
    paddingVertical: 0,
    fontFamily: fonts.bodyR,
    color: colors.primaryDark,
  },

  filterWrap: {
    flex: 1,
    minWidth: 0,
    position: 'relative',
    zIndex: 30,
    elevation: 30,
  },

  filterButton: {
    height: 44,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 4,
    paddingHorizontal: 8,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.pixelBorder,
    borderRadius: 10,
  },

  filterButtonText: {
    flex: 1,
    color: colors.primaryDark,
    fontFamily: fonts.bodyM,
    fontSize: 11,
  },

  filterMenu: {
    position: 'absolute',
    top: 48,
    right: 0,
    width: 168,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.pixelBorder,
    borderRadius: 10,
    overflow: 'hidden',
    zIndex: 40,
    elevation: 40,
    shadowColor: '#033236',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.16,
    shadowRadius: 8,
  },

  filterOption: {
    minHeight: 42,
    justifyContent: 'center',
    paddingHorizontal: 13,
    borderBottomWidth: 1,
    borderBottomColor: colors.hairline,
    backgroundColor: colors.white,
  },

  filterOptionActive: {
    backgroundColor: colors.screenBg,
  },

  filterOptionText: {
    color: colors.primaryDark,
    fontFamily: fonts.bodyR,
    fontSize: 13,
  },

  filterOptionTextActive: {
    color: colors.gold,
    fontFamily: fonts.bodyB,
  },

  error: {
    marginHorizontal: 16,
    marginBottom: 10,
    color: AD.red,
    fontFamily: fonts.bodyM,
  },

  list: {
    zIndex: 0,
  },

  pad: {
    paddingHorizontal: 16,
  },

  skeletonList: {
    gap: 10,
  },

  card: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: AD.cardBorder,
    borderRadius: 12,
    padding: 12,
  },

  info: {
    flex: 1,
  },

  name: {
    fontSize: 15,
    fontFamily: fonts.bodyM,
    color: colors.primaryDark,
  },

  email: {
    marginTop: 2,
    fontSize: 12,
    fontFamily: fonts.bodyR,
    color: AD.muted,
  },

  lv: {
    marginTop: 2,
    fontSize: 12,
    fontFamily: fonts.pixel,
    color: colors.gold,
  },

  statusBtn: {
    minWidth: 62,
    borderRadius: 6,
    paddingVertical: 7,
    paddingHorizontal: 8,
    alignItems: 'center',
  },

  activeBtn: {
    backgroundColor: colors.primaryDark,
  },

  inactiveBtn: {
    backgroundColor: AD.red,
  },

  statusText: {
    color: colors.white,
    fontFamily: fonts.bodyB,
    fontSize: 12,
  },

  separator: {
    height: 10,
  },

  footerSpace: {
    height: 16,
  },
});