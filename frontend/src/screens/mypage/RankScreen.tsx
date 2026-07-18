/**
 * SCREEN 06-5 · 개인 레벨 랭킹 (route Rank, back) — 레벨/랭킹전 정렬 탭(SegmentedTabs,
 * 슬라이딩 골드 필) · 랭킹 테이블(순위·닉네임·레벨/점수, 스태거 등장) · 내 랭킹 하단 sticky
 * 골드 하이라이트. Matches 06_mypage_flow.dc.html screen 5.
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { colors, fonts } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SegmentedTabs from '../../components/SegmentedTabs';
import { RANKS_LEVEL, RANKS_BATTLE } from './_parts';

export default function RankScreen({ navigation, route }: any) {
  const [mode, setMode] = useState(0); // 0 레벨 · 1 랭킹전

  const list = mode === 0 ? RANKS_LEVEL : RANKS_BATTLE;
  const colLabel = mode === 0 ? '레벨' : '점수';
  const myVal = mode === 0 ? '79lv' : '1,980pt';

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title="개인 레벨 랭킹" />

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.body}
        showsVerticalScrollIndicator={false}
      >
        {/* sort tabs — 레벨 / 랭킹전 */}
        <View style={styles.tabs}>
          <SegmentedTabs tabs={['레벨', '랭킹전']} index={mode} onChange={setMode} />
        </View>

        {/* rank table */}
        <View style={styles.table}>
          <View style={styles.thead}>
            <Text style={[styles.thRank, styles.theadText]}>순위</Text>
            <Text style={[styles.thName, styles.theadText]}>닉네임</Text>
            <Text style={styles.theadText}>{colLabel}</Text>
          </View>

          {/* key on mode → remount so the stagger replays on tab switch */}
          <View key={mode}>
            {list.map((r, i) => (
              <Animated.View
                key={r.rank + r.name}
                entering={FadeInDown.delay(40 + i * 60).duration(400)}
                style={[styles.row, i === list.length - 1 && styles.rowLast]}
              >
                <Text style={styles.rowRank}>{r.rank}</Text>
                <Text style={styles.rowName}>{r.name}</Text>
                <Text style={styles.rowVal}>{r.val}</Text>
              </Animated.View>
            ))}
          </View>
        </View>
      </ScrollView>

      {/* my rank — sticky gold highlight */}
      <LinearGradient
        colors={['rgba(238,246,240,0)', colors.screenBg]}
        locations={[0, 0.4]}
        style={styles.stickyWrap}
      >
        <View style={styles.myRow}>
          <Text style={styles.myRank}>3위</Text>
          <Text style={styles.myName}>사용자 (나)</Text>
          <Text style={styles.myVal}>{myVal}</Text>
        </View>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  scroll: { flex: 1 },
  body: { padding: 16, paddingBottom: 96 },

  tabs: { marginBottom: 14 },

  table: {
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#033236',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.06,
    shadowRadius: 10,
    elevation: 2,
  },
  thead: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primaryDark,
    paddingVertical: 11,
    paddingHorizontal: 14,
  },
  theadText: { fontFamily: fonts.pixel, fontSize: 14, color: colors.white },
  thRank: { width: 56 },
  thName: { flex: 1 },

  row: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.white,
    paddingVertical: 11,
    paddingHorizontal: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#EEF1F0',
  },
  rowLast: { borderBottomWidth: 0 },
  rowRank: { width: 56, fontFamily: fonts.pixel, fontSize: 14, color: colors.primaryDark },
  rowName: { flex: 1, fontSize: 14, color: colors.textPrimary, fontFamily: fonts.bodyR },
  rowVal: { fontSize: 14, fontWeight: '700', color: colors.xpGreen, fontFamily: fonts.bodyB },

  // sticky my-rank
  stickyWrap: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 12,
  },
  myRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.parchment,
    borderWidth: 2,
    borderColor: colors.gold,
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 14,
    shadowColor: colors.gold,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 14,
    elevation: 3,
  },
  myRank: { width: 56, fontFamily: fonts.pixel, fontSize: 14, color: colors.gold },
  myName: { flex: 1, fontSize: 14, fontWeight: '700', color: colors.primaryDark, fontFamily: fonts.bodyB },
  myVal: { fontSize: 14, fontWeight: '700', color: colors.xpGreen, fontFamily: fonts.bodyB },
});
