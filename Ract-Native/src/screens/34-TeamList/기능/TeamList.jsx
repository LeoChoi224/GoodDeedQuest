// 34-TeamList.js — React Native (Expo) 팀 목록 및 생성
// 선행퀘스트 / 스토리보드 34번 기준 — 내가 참여 중인 팀 목록 + 새 방 만들기/찾기

import React from 'react';
import { View, Text, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, Plus, ChevronRight, Search } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { CareIcon, GreenGradientBG } from '../../../shared/기능/components';
import { styles } from '../디자인/TeamList.styles';

const TEAMS = [
  { id: 't1', name: '저녁마다 산책 인증', category: '봉사', hostId: '@min_kindness', hostInitial: '민', hostColor: COLORS.mint, memberCount: 5, maxMembers: 8 },
  { id: 't2', name: '한 달 헌혈 챌린지', category: '나눔', hostId: '@haneul_92', hostInitial: '하', hostColor: COLORS.gold, memberCount: 3, maxMembers: 6 },
  { id: 't3', name: '동네 줍깅 모임', category: '환경', hostId: '@soo_bright', hostInitial: '수', hostColor: '#7AA9D1', memberCount: 4, maxMembers: 4 },
];

export default function TeamListScreen({ navigation }) {
  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate('Community')} hitSlop={10} style={{ padding: 4 }}>
            <ChevronLeft size={22} color={COLORS.ink} />
          </TouchableOpacity>
          <View style={styles.logoBadge}>
            <CareIcon size={18} />
          </View>
          <Text style={styles.logo}>선·퀘</Text>
          <View style={{ flex: 1 }} />
          <TouchableOpacity style={styles.addButton} onPress={() => navigation.navigate('RoomCreate')}>
            <Plus size={18} color={COLORS.ink} />
          </TouchableOpacity>
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <View>
            <Text style={styles.title}>내 팀</Text>
            <Text style={styles.subtitle}>참여 중인 팀 챌린지예요</Text>
          </View>

          <View style={{ gap: 12 }}>
            {TEAMS.map((team) => (
              <TouchableOpacity key={team.id} style={styles.teamCard} onPress={() => navigation.navigate('TeamDetail', { roomName: team.name, category: team.category })}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                  <View style={styles.categoryTag}>
                    <Text style={styles.categoryTagText}>{team.category}</Text>
                  </View>
                  <View style={{ flex: 1 }} />
                  <Text style={styles.memberCountText}>
                    {team.memberCount}/{team.maxMembers}명
                  </Text>
                  <ChevronRight size={16} color={COLORS.inkMuted48} />
                </View>
                <Text style={styles.teamName}>{team.name}</Text>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                  <View style={[styles.hostAvatar, { backgroundColor: team.hostColor }]}>
                    <Text style={styles.hostAvatarText}>{team.hostInitial}</Text>
                  </View>
                  <Text style={styles.hostText}>{team.hostId} 방장</Text>
                </View>
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity style={styles.findMoreButton} onPress={() => navigation.navigate('RoomFind')}>
            <Search size={16} color={COLORS.inkMuted48} />
            <Text style={styles.findMoreText}>새로운 방 찾아보기</Text>
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>
    </GreenGradientBG>
  );
}

