/**
 * SCREEN 1 · 팀챌린지 팝업 (route: TeamHome — team stack root, reached from drawer).
 * 커뮤니티 피드 위에 뜬 중앙 소개 카드(dim 없음). MainHeader = 뒤로가기 없음 + 햄버거.
 * "방 찾기" → RoomFind · "방 만들기" → TeamList. 카드 스프링 팝인.
 */
import React from 'react';
import { View, StyleSheet } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import Animated, { ZoomIn } from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import { colors } from '../../theme';
import { PopupTealBtn, PopupGoldBtn, PixelTitle } from './_parts';

export default function TeamHomeScreen({ navigation }: any) {
  // 팀 챌린지 하위(방 찾기/방 만들기)로 이동. 드로어(TeamStack)·커뮤니티(CommunityStack)
  // 어느 진입점에서든 해결되도록 드로어의 TeamChallenge 플로우를 지정한다.
  const goTeam = (screen: string) => navigation.navigate('TeamChallenge', { screen });
  return (
    <View style={styles.root}>
      <StatusBar style="dark" />
      <HazeBackground />
      {/* 커뮤니티에서 진입하면 뒤로가기(→Feed), 드로어 루트에선 햄버거만 */}
      <MainHeader showBack={navigation.canGoBack()} />

      {/* faded community feed behind the intro card (placeholder, opacity .5) */}
      <View style={styles.feed} pointerEvents="none">
        <View style={[styles.feedCard, { height: 120 }]} />
        <View style={[styles.feedCard, { height: 200 }]} />
      </View>

      {/* centered intro card — no dim backdrop */}
      <View style={styles.center} pointerEvents="box-none">
        <Animated.View entering={ZoomIn.duration(220)} style={styles.panelWrap}>
          <View style={styles.panel}>
            <PixelTitle size={18} color={colors.primaryDark} style={styles.title}>
              새로운 팀을 찾습니다.
            </PixelTitle>
            <View style={styles.btnRow}>
              <PopupTealBtn label="방 찾기" onPress={() => goTeam('RoomFind')} />
              <PopupGoldBtn label="방 만들기" onPress={() => goTeam('TeamList')} />
            </View>
          </View>
        </Animated.View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  feed: { paddingHorizontal: 16, paddingTop: 14, opacity: 0.5 },
  feedCard: { backgroundColor: colors.white, borderRadius: 12, marginBottom: 10 },
  center: { ...StyleSheet.absoluteFillObject, alignItems: 'stretch', justifyContent: 'center', paddingHorizontal: 20 },
  panelWrap: { marginTop: -40 },
  panel: {
    backgroundColor: colors.parchment,
    borderWidth: 1.5,
    borderColor: colors.pixelBorder,
    borderRadius: 16,
    paddingHorizontal: 22,
    paddingVertical: 24,
  },
  title: { textAlign: 'center', marginBottom: 20 },
  btnRow: { flexDirection: 'row', gap: 10 },
});
