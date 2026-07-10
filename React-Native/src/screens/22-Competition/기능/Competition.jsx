// 22-Competition.js — React Native (Expo) 대항전 메인페이지
// 선행퀘스트 / 스토리보드 22번 기준 — 전국 지도 + 전체 순위 (시·도 클릭 -> 시군구 랭킹)

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, Trophy } from 'lucide-react-native';

import { COLORS, RANK_BADGE_COLOR } from '../../../shared/디자인/tokens';
import { CareIcon, GreenGradientBG, BottomNav, HamburgerMenu, HamburgerButton, KoreaMap } from '../../../shared/기능/components';
import { styles } from '../디자인/Competition.styles';

const REGIONS = [
  { id: 'gg', name: '수도권', score: 7640 },
  { id: 'gw', name: '강원', score: 5240 },
  { id: 'cc', name: '충청', score: 5680 },
  { id: 'gb', name: '경북', score: 4900 },
  { id: 'jb', name: '전북', score: 4600 },
  { id: 'gn', name: '경남', score: 5320 },
  { id: 'jn', name: '전남', score: 4380 },
  { id: 'jj', name: '제주', score: 3040 },
];
const MY_REGION_ID = 'gg';

export default function CompetitionScreen({ navigation }) {
  const [menuVisible, setMenuVisible] = useState(false);
  const ranked = [...REGIONS].sort((a, b) => b.score - a.score);
  const myIndex = ranked.findIndex((r) => r.id === MY_REGION_ID);
  const my = ranked[myIndex];

  const regionStyles = { [MY_REGION_ID]: { fill: COLORS.primary, labelColor: '#fff' } };
  const goRegion = (id) => navigation.navigate('DistrictRanking', { regionId: id });

  const podiumOrder = [1, 0, 2]; // 2등-1등-3등 순서로 배치(가운데가 1등)

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate('MapMain')} hitSlop={10} style={{ padding: 4 }}>
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
          <View>
            <Text style={styles.title}>대항전</Text>
            <Text style={styles.subtitle}>전국 시·도가 봉사 활동으로 겨루는 랭킹이에요</Text>
          </View>

          <View style={styles.mapCard}>
            <Text style={styles.cardHeader}>전국 지도</Text>
            <KoreaMap size={210} regionStyles={regionStyles} onPressRegion={goRegion} />
            <Text style={styles.mapHint}>지역을 눌러 시·군·구 랭킹을 확인해보세요</Text>
          </View>

          <View style={styles.podiumCard}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <Trophy size={16} color={COLORS.gold} />
              <Text style={styles.podiumHeader}>전체 랭킹 TOP 3</Text>
            </View>
            <View style={styles.podiumRow}>
              {podiumOrder.map((i) => {
                const r = ranked[i];
                const barHeight = i === 0 ? 56 : i === 1 ? 40 : 28;
                return (
                  <View key={r.id} style={{ alignItems: 'center', gap: 6 }}>
                    <View style={[styles.podiumBadge, { backgroundColor: RANK_BADGE_COLOR[i + 1] }]}>
                      <Text style={styles.podiumBadgeText}>{i + 1}</Text>
                    </View>
                    <Text style={styles.podiumName}>{r.name}</Text>
                    <Text style={styles.podiumScore}>{r.score.toLocaleString()}P</Text>
                    <View style={[styles.podiumBar, { height: barHeight, backgroundColor: RANK_BADGE_COLOR[i + 1] }]} />
                  </View>
                );
              })}
            </View>
          </View>

          <View style={styles.myRegionRow}>
            <View style={styles.myRegionBadge}>
              <Text style={styles.myRegionBadgeText}>{myIndex + 1}</Text>
            </View>
            <View style={{ flex: 1, minWidth: 0 }}>
              <Text style={styles.myRegionLabel}>내 지역 순위</Text>
              <Text style={styles.myRegionName}>{my.name}</Text>
            </View>
            <Text style={styles.myRegionScore}>{my.score.toLocaleString()}P</Text>
          </View>

          <View style={{ gap: 8 }}>
            <Text style={styles.listHeader}>시·도별 랭킹</Text>
            {ranked.map((r, i) => {
              const rank = i + 1;
              const isMine = r.id === MY_REGION_ID;
              return (
                <TouchableOpacity
                  key={r.id}
                  style={[styles.rankRow, { backgroundColor: isMine ? COLORS.goldTint : COLORS.parchment, borderColor: isMine ? 'rgba(201,162,39,0.35)' : 'transparent' }]}
                  onPress={() => goRegion(r.id)}
                >
                  <View style={[styles.rankBadge, { backgroundColor: RANK_BADGE_COLOR[rank] || '#E5E5E5' }]}>
                    <Text style={[styles.rankBadgeText, { color: rank <= 3 ? '#fff' : COLORS.inkMuted48 }]}>{rank}</Text>
                  </View>
                  <View style={{ flex: 1, flexDirection: 'row', alignItems: 'center', gap: 6, minWidth: 0 }}>
                    <Text style={styles.rankName}>{r.name}</Text>
                    {isMine && (
                      <View style={styles.mineTag}>
                        <Text style={styles.mineTagText}>내 지역</Text>
                      </View>
                    )}
                  </View>
                  <Text style={styles.rankScore}>{r.score.toLocaleString()}P</Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </ScrollView>

        <BottomNav navigation={navigation} active="map" translucent />
        <HamburgerMenu visible={menuVisible} onClose={() => setMenuVisible(false)} navigation={navigation} />
      </SafeAreaView>
    </GreenGradientBG>
  );
}

