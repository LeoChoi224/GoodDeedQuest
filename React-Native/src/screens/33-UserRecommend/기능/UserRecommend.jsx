// 33-UserRecommend.js — React Native (Expo) 챌린지팀 유저 추천 리스트 (초대하기)
// 선행퀘스트 / 스토리보드 33번 기준 — AI 기반(LangGraph/Vector Search) 추천, "팔로우" 대신 "초대하기"

import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, Search, Check } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { CareIcon, GreenGradientBG } from '../../../shared/기능/components';
import { styles } from '../디자인/UserRecommend.styles';

const USERS = [
  { id: 'u1', userId: '@bomi_lee', initial: '보', color: '#9B8BD1', bio: '완료한 퀘스트 24개 · 나눔 관심' },
  { id: 'u2', userId: '@jiwoo_k', initial: '지', color: '#D18F7A', bio: '완료한 퀘스트 31개 · 동물 관심' },
  { id: 'u3', userId: '@soo_bright', initial: '수', color: '#7AA9D1', bio: '완료한 퀘스트 18개 · 환경 관심' },
  { id: 'u4', userId: '@haneul_92', initial: '하', color: COLORS.gold, bio: '완료한 퀘스트 27개 · 나눔 관심' },
  { id: 'u5', userId: '@doyoon_j', initial: '도', color: COLORS.primary, bio: '완료한 퀘스트 9개 · 지역사회 관심' },
  { id: 'u6', userId: '@min_kindness', initial: '민', color: COLORS.mint, bio: '완료한 퀘스트 42개 · 봉사 관심' },
];

export default function UserRecommendScreen({ navigation }) {
  const [query, setQuery] = useState('');
  const [invited, setInvited] = useState({});

  const toggleInvite = (id) => setInvited((s) => ({ ...s, [id]: !s[id] }));

  const q = query.trim().toLowerCase();
  const filtered = USERS.filter((u) => !q || u.userId.toLowerCase().includes(q));

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate('TeamDetail')} hitSlop={10} style={{ padding: 4 }}>
            <ChevronLeft size={22} color={COLORS.ink} />
          </TouchableOpacity>
          <View style={styles.logoBadge}>
            <CareIcon size={18} />
          </View>
          <Text style={styles.logo}>선·퀘</Text>
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <View>
            <Text style={styles.title}>함께할 유저를{'\n'}찾아보세요</Text>
            <Text style={styles.subtitle}>관심사가 비슷한 유저를 추천해드려요</Text>
          </View>

          <View style={styles.searchBar}>
            <Search size={17} color={COLORS.inkMuted48} />
            <TextInput style={styles.searchInput} placeholder="아이디로 검색" placeholderTextColor={COLORS.inkMuted48} value={query} onChangeText={setQuery} />
          </View>

          {filtered.length === 0 && (
            <View style={{ alignItems: 'center', paddingVertical: 40 }}>
              <Text style={{ fontSize: 14, fontWeight: '600', color: COLORS.inkMuted48 }}>검색 결과가 없어요</Text>
            </View>
          )}

          <View>
            {filtered.map((u) => {
              const isInvited = !!invited[u.id];
              return (
                <View key={u.id} style={styles.userRow}>
                  <View style={[styles.avatar, { backgroundColor: u.color }]}>
                    <Text style={styles.avatarText}>{u.initial}</Text>
                  </View>
                  <View style={{ flex: 1, minWidth: 0, gap: 2 }}>
                    <Text style={styles.userId}>{u.userId}</Text>
                    <Text style={styles.userBio} numberOfLines={1}>
                      {u.bio}
                    </Text>
                  </View>
                  <TouchableOpacity style={[styles.inviteButton, isInvited && styles.inviteButtonActive]} onPress={() => toggleInvite(u.id)}>
                    {isInvited && <Check size={13} color="#fff" />}
                    <Text style={[styles.inviteButtonText, isInvited && { color: '#fff' }]}>{isInvited ? '초대 완료' : '초대하기'}</Text>
                  </TouchableOpacity>
                </View>
              );
            })}
          </View>
        </ScrollView>
      </SafeAreaView>
    </GreenGradientBG>
  );
}

