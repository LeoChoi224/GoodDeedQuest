/**
 * SCREEN 2 · 방 찾기 (route: RoomFind). 검색바 + 정렬 · 방 목록(스태거).
 * 공개방 tap → TeamDetail · 비공개(자물쇠) tap → 비밀번호 팝업(2A).
 * 비밀번호 팝업: GdqInput + Error Shake(#17). 데모 정답 '1234' → TeamDetail.
 * 하단 sticky "방 만들기" → TeamList.
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, useWindowDimensions } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import Animated, { FadeInDown } from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import GdqInput from '../../components/GdqInput';
import LightPopup from '../../components/LightPopup';
import Shake from '../../components/Shake';
import EmptyState from '../../components/EmptyState';
import { colors, fonts } from '../../theme';
import {
  ROOMS,
  Room,
  SearchSortBar,
  PixelTitle,
  CatIcon,
  IconLock,
  StickyFooter,
  PopupTealBtn,
  ERR_TEXT,
  ERR_BORDER,
  INFO,
  staggerDelay,
} from './_parts';

const CORRECT_PW = '1234'; // demo 비공개방 비밀번호

function RoomCard({ room, index, onPress }: { room: Room; index: number; onPress: () => void }) {
  return (
    <Animated.View entering={FadeInDown.delay(staggerDelay(index)).duration(450)}>
      <SpringButton onPress={onPress} pressScale={0.98} style={styles.card}>
        <CatIcon category={room.category} />
        <View style={styles.cardBody}>
          <Text style={styles.roomName}>{room.name}</Text>
          <Text style={styles.roomInfo}>{room.info}</Text>
          <Text style={styles.roomCount}>{room.count}</Text>
        </View>
        {room.locked ? (
          <View style={styles.lock}>
            <IconLock />
          </View>
        ) : null}
      </SpringButton>
    </Animated.View>
  );
}

export default function RoomFindScreen({ navigation }: any) {
  const { width } = useWindowDimensions();
  const [pwRoom, setPwRoom] = useState<Room | null>(null);
  const [pw, setPw] = useState('');
  const [err, setErr] = useState(false);
  const [shake, setShake] = useState(0);

  const openRoom = (room: Room) => {
    if (room.locked) {
      setPw('');
      setErr(false);
      setPwRoom(room);
    } else {
      navigation.navigate('TeamDetail', { room });
    }
  };

  const submitPw = () => {
    if (pw.trim() === CORRECT_PW) {
      const room = pwRoom;
      setPwRoom(null);
      navigation.navigate('TeamDetail', { room });
    } else {
      setErr(true);
      setShake((s) => s + 1);
    }
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title="방 찾기" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
        <SearchSortBar placeholder="방 이름 또는 카테고리" sortLabel="최신순" />
        <PixelTitle size={16} style={{ marginBottom: 12 }}>
          방 목록
        </PixelTitle>
        {ROOMS.length === 0 ? (
          <EmptyState
            icon="📜"
            message="현재 참여 가능한 방이 없어요"
            subMessage="방 만들기로 새 팀을 시작해보세요"
          />
        ) : (
          <View style={{ gap: 10 }}>
            {ROOMS.map((room, i) => (
              <RoomCard key={room.name} room={room} index={i} onPress={() => openRoom(room)} />
            ))}
          </View>
        )}
      </ScrollView>

      <StickyFooter>
        <SpringButton style={styles.makeBtn} onPress={() => navigation.navigate('TeamList')}>
          <Text style={styles.makeText}>방 만들기</Text>
        </SpringButton>
      </StickyFooter>

      {/* SCREEN 2-A · 비밀번호 팝업 (라이트 팝업 — 기능성 대화상자) */}
      <LightPopup visible={!!pwRoom} onClose={() => setPwRoom(null)} width={Math.min(360, width - 48)}>
        <View style={styles.pwContent}>
          {err ? <Text style={styles.pwErr}>비밀번호가 맞지 않습니다. 다시 입력해주세요.</Text> : null}
          <PixelTitle size={16} color={colors.primaryDark} style={styles.pwTitle}>
            비밀번호를 입력하시오
          </PixelTitle>
          <Shake trigger={shake}>
            <View style={[styles.pwRing, err && { borderColor: ERR_BORDER }]}>
              <GdqInput
                value={pw}
                onChangeText={(t) => {
                  setPw(t);
                  if (err) setErr(false);
                }}
                secureTextEntry
                keyboardType="number-pad"
                autoFocus
                placeholder="••••"
                style={styles.pwInput}
              />
            </View>
          </Shake>
          <View style={styles.pwBtnRow}>
            <PopupTealBtn label="입력완료" onPress={submitPw} />
          </View>
        </View>
      </LightPopup>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 16, paddingTop: 14, paddingBottom: 130 },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.pixelBorder,
    borderRadius: 12,
    padding: 12,
    shadowColor: colors.pixelBorder,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 2,
  },
  cardBody: { flex: 1, minWidth: 0 },
  roomName: { fontSize: 15, fontWeight: '600', color: colors.primaryDark, fontFamily: fonts.bodyM },
  roomInfo: { fontSize: 13, color: INFO, marginTop: 1, marginBottom: 3, fontFamily: fonts.bodyR },
  roomCount: { fontFamily: fonts.pixel, fontSize: 12, color: colors.gold },
  lock: { position: 'absolute', top: 10, right: 10 },
  makeBtn: {
    height: 52,
    borderRadius: 8,
    backgroundColor: colors.gold,
    alignItems: 'center',
    justifyContent: 'center',
  },
  makeText: { fontFamily: fonts.pixel, fontSize: 18, color: colors.primaryDark },
  // password popup
  pwContent: { alignSelf: 'stretch', width: '100%' },
  pwErr: { textAlign: 'center', fontSize: 13, color: ERR_TEXT, marginBottom: 8, fontFamily: fonts.bodyR },
  pwTitle: { textAlign: 'center', marginBottom: 16 },
  pwRing: { borderWidth: 1.5, borderColor: 'transparent', borderRadius: 14, padding: 3 },
  pwInput: { textAlign: 'center', letterSpacing: 6 },
  pwBtnRow: { flexDirection: 'row', marginTop: 16 },
});
