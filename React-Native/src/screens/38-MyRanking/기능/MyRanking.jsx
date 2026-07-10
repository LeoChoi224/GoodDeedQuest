// 38-MyRanking.js — React Native (Expo) 내 랭킹 확인 페이지
// 선행퀘스트 / 스토리보드 38번 기준 — 전체 유저 기준 개인 레벨/XP 랭킹(지역 대항전과 별개)

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft } from 'lucide-react-native';

import { COLORS, RANK_BADGE_COLOR } from '../../../shared/디자인/tokens';
import { GreenGradientBG, BottomNav, HamburgerMenu, HamburgerButton } from '../../../shared/기능/components';
import { styles } from '../디자인/MyRanking.styles';

const NAMES = ['김도윤', '이서준', '박하은', '최지우', '정민준', '강서윤', '조은우', '윤하린', '장시우', '임지호', '한소율', '오예준', '신다인', '권주원', '황시온', '안유나', '송태민', '류가온', '문서연', '배준서'];
const AVATAR_COLORS = [COLORS.mint, '#7AA9D1', '#D19A7A', '#B08BD1', '#D1C07A', '#7AD1C0'];

function seedNum(seed) {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) >>> 0;
  return h;
}

function buildList(range) {
  const list = NAMES.map((name) => {
    const base = seedNum(range + name);
    return { name, level: 6 + (base % 20), xp: 300 + (base % 3200), avatarColor: AVATAR_COLORS[base % AVATAR_COLORS.length], avatarInitial: name[0] };
  });
  list.push({ name: '민선행', level: 12, xp: 1240 + (seedNum(range + 'me') % 400), avatarColor: COLORS.mint, avatarInitial: '민', isMine: true });
  return list.sort((a, b) => b.xp - a.xp);
}

export default function MyRankingScreen({ navigation }) {
  const [menuVisible, setMenuVisible] = useState(false);
  const [range, setRange] = useState('total');
  const list = buildList(range);
  const myIndex = list.findIndex((r) => r.isMine);
  const me = list[myIndex];

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate('MyLevel')} hitSlop={10} style={{ padding: 4 }}>
            <ChevronLeft size={22} color={COLORS.ink} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>내 랭킹</Text>
          <View style={{ flex: 1 }} />
          <HamburgerButton onPress={() => setMenuVisible(true)} />
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <View>
            <Text style={styles.title}>전체 개인 레벨 랭킹</Text>
            <Text style={styles.subtitle}>지역 대항전과 별개로 전체 유저 기준 순위예요</Text>
          </View>

          <View style={styles.myRow}>
            <View style={styles.myBadge}>
              <Text style={styles.myBadgeText}>#{myIndex + 1}</Text>
            </View>
            <View style={{ flex: 1, minWidth: 0, gap: 3 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <Text style={styles.myName}>민선행</Text>
                <View style={styles.titleTag}>
                  <Text style={styles.titleTagText}>따뜻한 이웃</Text>
                </View>
              </View>
              <Text style={styles.mySub}>
                Lv.{me.level} · {me.xp.toLocaleString()} XP
              </Text>
            </View>
          </View>

          <View style={{ flexDirection: 'row', gap: 6 }}>
            {[
              ['total', '전체'],
              ['monthly', '월간'],
              ['weekly', '주간'],
            ].map(([key, label]) => (
              <TouchableOpacity key={key} style={[styles.tab, range === key && styles.tabActive]} onPress={() => setRange(key)}>
                <Text style={[styles.tabText, range === key && styles.tabTextActive]}>{label}</Text>
              </TouchableOpacity>
            ))}
          </View>

          <View style={{ gap: 8 }}>
            {list.map((r, i) => {
              const rank = i + 1;
              return (
                <TouchableOpacity
                  key={r.name}
                  style={[styles.rankRow, { backgroundColor: r.isMine ? COLORS.goldTint : '#fff', borderColor: r.isMine ? 'rgba(201,162,39,0.4)' : COLORS.hairline }]}
                  onPress={() => navigation.navigate('UserDetail', { userId: '@' + r.name.toLowerCase(), nickname: r.name, avatarInitial: r.avatarInitial, avatarColor: r.avatarColor })}
                >
                  <View style={[styles.rankBadge, { backgroundColor: RANK_BADGE_COLOR[rank] || COLORS.parchment }]}>
                    <Text style={[styles.rankBadgeText, { color: rank <= 3 ? '#fff' : COLORS.inkMuted48 }]}>{rank}</Text>
                  </View>
                  <View style={[styles.avatar, { backgroundColor: r.avatarColor }]}>
                    <Text style={styles.avatarText}>{r.avatarInitial}</Text>
                  </View>
                  <View style={{ flex: 1, minWidth: 0, gap: 1 }}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                      <Text style={styles.rowName}>{r.name}</Text>
                      {r.isMine && (
                        <View style={styles.mineTag}>
                          <Text style={styles.mineTagText}>나</Text>
                        </View>
                      )}
                    </View>
                    <Text style={styles.rowLevel}>Lv.{r.level}</Text>
                  </View>
                  <Text style={styles.rowScore}>{r.xp.toLocaleString()} XP</Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </ScrollView>

        <BottomNav navigation={navigation} active="mypage" translucent />
        <HamburgerMenu visible={menuVisible} onClose={() => setMenuVisible(false)} navigation={navigation} />
      </SafeAreaView>
    </GreenGradientBG>
  );
}

