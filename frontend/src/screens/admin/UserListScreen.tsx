import React, { useCallback, useEffect, useRef, useState } from 'react';
import { FlatList, RefreshControl, StyleSheet, Text, TextInput, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { colors, fonts } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import EmptyState from '../../components/EmptyState';
import { useToast } from '../../components/Toast';
import { AD, Avatar, AVATARS, LoadingDots, SearchIcon, SkeletonCard } from './_parts';
import { adminApi, AdminUser, getAdminErrorMessage } from './adminApi';

const LIMIT = 20;
export default function UserListScreen({ navigation }: any) {
  const insets = useSafeAreaInsets(); const toast = useToast();
  const [users, setUsers] = useState<AdminUser[]>([]); const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true); const [more, setMore] = useState(false); const [refreshing, setRefreshing] = useState(false); const [hasMore, setHasMore] = useState(true); const [busyId, setBusyId] = useState<number | null>(null); const [error, setError] = useState('');
  const skipRef = useRef(0); const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(async (reset = false, nickname = query) => {
    if (reset) { setLoading(true); skipRef.current = 0; } else setMore(true);
    setError('');
    try {
      const rows = await adminApi.getUsers({ nickname: nickname.trim() || undefined, skip: skipRef.current, limit: LIMIT, newest_first: true });
      setUsers((prev) => reset ? rows : [...prev, ...rows]); skipRef.current += rows.length; setHasMore(rows.length === LIMIT);
    } catch (e) { setError(getAdminErrorMessage(e)); }
    finally { setLoading(false); setMore(false); setRefreshing(false); }
  }, [query]);

  useEffect(() => { void load(true, ''); }, []);
  useEffect(() => { if (searchTimer.current) clearTimeout(searchTimer.current); searchTimer.current = setTimeout(() => void load(true, query), 400); return () => { if (searchTimer.current) clearTimeout(searchTimer.current); }; }, [query]);

  const toggle = async (user: AdminUser) => {
    setBusyId(user.user_id);
    try {
      const updated = await adminApi.updateUserActiveStatus(user.user_id, !user.is_active);
      setUsers((prev) => prev.map((item) => item.user_id === user.user_id ? { ...item, ...updated } : item));
      toast.show(updated.is_active ? '사용자를 활성화했습니다' : '사용자를 비활성화했습니다');
    } catch (e) { toast.show(getAdminErrorMessage(e)); } finally { setBusyId(null); }
  };

  return <View style={styles.root}><StatusBar style="light" /><HazeBackground /><MainHeader showBack title="유저 목록" onBack={() => navigation.goBack()} />
    {loading ? <View style={styles.pad}><View style={{ gap: 10 }}>{[0,1,2,3,4].map(i => <SkeletonCard key={i} />)}</View></View> :
      <FlatList data={users} keyExtractor={(u) => String(u.user_id)}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); void load(true); }} />}
        ListHeaderComponent={<View><View style={styles.searchBox}><SearchIcon /><TextInput value={query} onChangeText={setQuery} placeholder="닉네임 검색" placeholderTextColor={colors.textMuted} style={styles.input} autoCapitalize="none" /></View>{error ? <Text style={styles.error}>{error}</Text> : null}</View>}
        renderItem={({ item, index }) => <Animated.View entering={FadeInDown.delay(Math.min(index,6)*45).duration(400)}><SpringButton style={styles.card} onPress={() => navigation.navigate('UserDetail', { userId: item.user_id, user: item, moderation: true })}>
          <Avatar av={AVATARS[item.user_id % AVATARS.length]} /><View style={styles.info}><Text style={styles.name}>{item.nickname}</Text><Text style={styles.email}>{item.email}</Text><Text style={styles.lv}>LV.{item.current_level} · 신뢰도 {item.trust_score}</Text></View>
          <SpringButton disabled={busyId === item.user_id} style={[styles.statusBtn, item.is_active ? styles.activeBtn : styles.inactiveBtn]} onPress={() => void toggle(item)}><Text style={styles.statusText}>{busyId === item.user_id ? '처리중' : item.is_active ? '활성' : '비활성'}</Text></SpringButton>
        </SpringButton></Animated.View>}
        ItemSeparatorComponent={() => <View style={{ height: 10 }} />} ListEmptyComponent={<EmptyState message="조회된 사용자가 없습니다" />}
        onEndReached={() => { if (!more && hasMore) void load(false); }} onEndReachedThreshold={0.4} ListFooterComponent={more ? <LoadingDots /> : <View style={{ height: 16 }} />}
        contentContainerStyle={[styles.pad, { paddingBottom: insets.bottom + 24 }]} />}
  </View>;
}
const styles = StyleSheet.create({ root:{flex:1,backgroundColor:colors.screenBg}, pad:{paddingHorizontal:16,paddingTop:14}, searchBox:{flexDirection:'row',alignItems:'center',gap:8,backgroundColor:colors.white,borderWidth:1,borderColor:colors.pixelBorder,borderRadius:24,paddingHorizontal:14,marginBottom:14}, input:{flex:1,paddingVertical:10,fontFamily:fonts.bodyR,color:colors.primaryDark}, error:{color:AD.red,fontFamily:fonts.bodyM,marginBottom:10}, card:{flexDirection:'row',alignItems:'center',gap:12,backgroundColor:colors.white,borderWidth:1,borderColor:AD.cardBorder,borderRadius:12,padding:12}, info:{flex:1}, name:{fontSize:15,fontFamily:fonts.bodyM,color:colors.primaryDark}, email:{fontSize:12,fontFamily:fonts.bodyR,color:AD.muted,marginTop:2}, lv:{fontSize:12,fontFamily:fonts.pixel,color:colors.gold,marginTop:2}, statusBtn:{minWidth:62,borderRadius:6,paddingVertical:7,paddingHorizontal:8,alignItems:'center'}, activeBtn:{backgroundColor:colors.primaryDark}, inactiveBtn:{backgroundColor:AD.red}, statusText:{color:colors.white,fontFamily:fonts.bodyB,fontSize:12} });
