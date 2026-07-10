// 37-UserDetail.js — React Native (Expo) 유저 상세정보 (프로필 + 달성업적 타임라인)
// 선행퀘스트 / 스토리보드 37번 기준 — 페이지네이션 + 업적 상세 팝업

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView, Modal, Pressable, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, X, Coins } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { CareIcon, GreenGradientBG, BottomNav, HamburgerMenu, HamburgerButton } from '../../../shared/기능/components';
import { styles } from '../디자인/UserDetail.styles';

const TEMPLATES = [
  { name: '노약자 자리 양보하기', emoji: '❤️', bg: '#FDECEC', story: '지하철에서 어르신께 자리를 양보해드렸어요. 짧은 순간이지만 따뜻한 감사 인사를 받았습니다.', reward: 20 },
  { name: '헌혈하기', emoji: '💧', bg: '#EAF2FB', story: '오랜만에 헌혈의 집을 방문해 헌혈을 완료했어요. 몸도 마음도 뿌듯한 하루였습니다.', reward: 50 },
  { name: '유기동물 보호소 봉사', emoji: '🐾', bg: '#FBEFE9', story: '주말 오전, 보호소에서 강아지 산책과 목욕 봉사를 진행했어요.', reward: 40 },
  { name: '동네 쓰레기 줍기', emoji: '🍃', bg: '#EAF6EC', story: '아침 산책 겸 동네 한 바퀴를 돌며 쓰레기를 주웠어요.', reward: 15 },
  { name: '이웃 어르신 짐 들어드리기', emoji: '📦', bg: '#FBF3DC', story: '무거운 장바구니를 들고 계신 어르신을 집 앞까지 도와드렸어요.', reward: 15 },
];

function makeAchievements() {
  const all = [];
  for (let i = 0; i < 30; i++) {
    const t = TEMPLATES[i % TEMPLATES.length];
    const month = String(((i * 2) % 12) + 1).padStart(2, '0');
    const day = String(((i * 3) % 27) + 1).padStart(2, '0');
    all.push({ id: 'a' + i, ...t, date: '2026-' + month + '-' + day });
  }
  return all;
}
const ALL_ACHIEVEMENTS = makeAchievements();
const PAGE_SIZE = 3;
const TOTAL_PAGES = Math.ceil(ALL_ACHIEVEMENTS.length / PAGE_SIZE);

export default function UserDetailScreen({ navigation, route }) {
  const user = {
    userId: route?.params?.userId ?? '@min_kindness',
    nickname: route?.params?.nickname ?? '민선행',
    avatarInitial: route?.params?.avatarInitial ?? '민',
    avatarColor: route?.params?.avatarColor ?? COLORS.mint,
    title: '따뜻한 이웃',
    level: 12,
  };

  const [menuVisible, setMenuVisible] = useState(false);
  const [page, setPage] = useState(1);
  const [detailId, setDetailId] = useState(null);

  const start = (page - 1) * PAGE_SIZE;
  const pageItems = ALL_ACHIEVEMENTS.slice(start, start + PAGE_SIZE);
  const detail = detailId ? ALL_ACHIEVEMENTS.find((a) => a.id === detailId) : null;

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} hitSlop={10} style={{ padding: 4 }}>
            <ChevronLeft size={22} color={COLORS.ink} />
          </TouchableOpacity>
          <View style={styles.logoBadge}>
            <CareIcon size={18} />
          </View>
          <Text style={styles.logo}>선·퀘</Text>
          <View style={{ flex: 1 }} />
          <HamburgerButton onPress={() => setMenuVisible(true)} />
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.profileCard}>
            <View style={[styles.avatar, { backgroundColor: user.avatarColor }]}>
              <Text style={styles.avatarText}>{user.avatarInitial}</Text>
            </View>
            <View style={{ gap: 5, minWidth: 0 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 7, flexWrap: 'wrap' }}>
                <Text style={styles.nickname}>{user.nickname}</Text>
                <View style={styles.titleTag}>
                  <Text style={styles.titleTagText}>{user.title}</Text>
                </View>
              </View>
              <Text style={styles.userId}>{user.userId}</Text>
              <Text style={styles.level}>Lv. {user.level}</Text>
            </View>
          </View>

          <View style={styles.achievementCard}>
            <Text style={styles.achievementHeader}>퀘스트 달성업적 및 타임라인</Text>
            <View style={{ gap: 8 }}>
              {pageItems.map((a) => (
                <View key={a.id} style={styles.achievementRow}>
                  <View style={[styles.achievementIcon, { backgroundColor: a.bg }]}>
                    <Text style={{ fontSize: 20 }}>{a.emoji}</Text>
                  </View>
                  <View style={{ flex: 1, minWidth: 0, gap: 2 }}>
                    <Text style={styles.achievementName} numberOfLines={1}>
                      {a.name}
                    </Text>
                    <Text style={styles.achievementDate}>달성일자 {a.date}</Text>
                  </View>
                  <TouchableOpacity style={styles.viewButton} onPress={() => setDetailId(a.id)}>
                    <Text style={styles.viewButtonText}>달성 업적 보기</Text>
                  </TouchableOpacity>
                </View>
              ))}
            </View>

            <View style={styles.pagination}>
              {Array.from({ length: TOTAL_PAGES }, (_, i) => i + 1).map((p) => (
                <TouchableOpacity key={p} style={[styles.pageDot, p === page && { backgroundColor: COLORS.primary }]} onPress={() => setPage(p)}>
                  <Text style={[styles.pageDotText, p === page && { color: '#fff' }]}>{p}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        </ScrollView>

        <BottomNav navigation={navigation} active="community" />
        <HamburgerMenu visible={menuVisible} onClose={() => setMenuVisible(false)} navigation={navigation} />

        <Modal statusBarTranslucent visible={!!detail} transparent animationType="fade" onRequestClose={() => setDetailId(null)}>
          <View style={styles.detailOverlay}>
            <Pressable style={StyleSheet.absoluteFill} onPress={() => setDetailId(null)} />
            {detail && (
              <View style={styles.detailCard}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
                  <View style={[styles.achievementIcon, { backgroundColor: detail.bg, width: 52, height: 52 }]}>
                    <Text style={{ fontSize: 24 }}>{detail.emoji}</Text>
                  </View>
                  <View style={{ gap: 3, minWidth: 0, flex: 1 }}>
                    <Text style={styles.detailName}>{detail.name}</Text>
                    <Text style={styles.achievementDate}>달성일자 {detail.date}</Text>
                  </View>
                </View>
                <View style={styles.divider} />
                <Text style={styles.detailStory}>{detail.story}</Text>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                  <Coins size={13} color={COLORS.gold} />
                  <Text style={styles.detailReward}>보상 {detail.reward}P 획득</Text>
                </View>
                <TouchableOpacity style={styles.detailCloseButton} onPress={() => setDetailId(null)}>
                  <Text style={styles.detailCloseText}>닫기</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        </Modal>
      </SafeAreaView>
    </GreenGradientBG>
  );
}

