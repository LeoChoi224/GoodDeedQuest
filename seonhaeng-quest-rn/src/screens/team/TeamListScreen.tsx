/**
 * SCREEN 5 · 팀 목록 및 생성 (route: TeamList).
 * 팀 카드(스태거) → TeamDetail. 하단 sticky "방만들기" → 팀 생성 폼(BottomSheet).
 * 생성 폼: 팀 이름 · 카테고리 · 공개/비공개(SegmentedTabs) → 비공개 시 비밀번호 필드.
 * 빈 상태: "함께할 팀 유저를 찾아보세요."
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import Animated, { FadeInDown } from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import GdqInput from '../../components/GdqInput';
import BottomSheet from '../../components/BottomSheet';
import SegmentedTabs from '../../components/SegmentedTabs';
import Shake from '../../components/Shake';
import EmptyState from '../../components/EmptyState';
import { colors, fonts, CATEGORY_DEFS } from '../../theme';
import {
  TEAMS,
  PixelTitle,
  CatIcon,
  IconChevRight,
  StickyFooter,
  INFO,
  staggerDelay,
} from './_parts';

export default function TeamListScreen({ navigation }: any) {
  const [sheet, setSheet] = useState(false);
  const [name, setName] = useState('');
  const [catKey, setCatKey] = useState<string>('environment');
  const [vis, setVis] = useState(0); // 0=공개 1=비공개
  const [pw, setPw] = useState('');
  const [nameShake, setNameShake] = useState(0);

  const resetForm = () => {
    setName('');
    setCatKey('environment');
    setVis(0);
    setPw('');
  };

  const onCreate = () => {
    if (!name.trim()) {
      setNameShake((s) => s + 1);
      return;
    }
    const label = CATEGORY_DEFS.find((c) => c.key === catKey)?.label ?? '기타';
    const room = { name: name.trim(), info: `${label} · 새 팀`, category: catKey, locked: vis === 1 };
    setSheet(false);
    resetForm();
    navigation.navigate('TeamDetail', { room });
  };

  return (
    <View style={styles.root}>
      <StatusBar style="dark" />
      <HazeBackground />
      <MainHeader showBack title="팀 목록" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
        <PixelTitle size={18} style={{ marginBottom: 12 }}>
          팀 목록
        </PixelTitle>

        {TEAMS.length === 0 ? (
          <EmptyState icon="🧭" message="함께할 팀 유저를 찾아보세요" />
        ) : (
          <View style={{ gap: 10 }}>
            {TEAMS.map((t, i) => (
              <Animated.View key={t.name} entering={FadeInDown.delay(staggerDelay(i)).duration(450)}>
                <SpringButton
                  pressScale={0.98}
                  style={styles.card}
                  onPress={() => navigation.navigate('TeamDetail', { room: t })}
                >
                  <CatIcon category={t.category} />
                  <View style={{ flex: 1, minWidth: 0 }}>
                    <Text style={styles.name}>{t.name}</Text>
                    <Text style={styles.info}>{t.info}</Text>
                  </View>
                  <IconChevRight />
                </SpringButton>
              </Animated.View>
            ))}
          </View>
        )}
      </ScrollView>

      <StickyFooter>
        <SpringButton style={styles.makeBtn} onPress={() => setSheet(true)}>
          <Text style={styles.makeText}>방만들기</Text>
        </SpringButton>
      </StickyFooter>

      {/* 팀 생성 폼 */}
      <BottomSheet visible={sheet} onClose={() => setSheet(false)} title="팀 만들기">
        <Text style={styles.formLabel}>팀 이름</Text>
        <Shake trigger={nameShake}>
          <GdqInput value={name} onChangeText={setName} placeholder="팀 이름을 입력하세요" maxLength={20} />
        </Shake>

        <Text style={[styles.formLabel, { marginTop: 16 }]}>카테고리</Text>
        <View style={styles.chipWrap}>
          {CATEGORY_DEFS.map((c) => {
            const on = catKey === c.key;
            return (
              <SpringButton
                key={c.key}
                pressScale={0.94}
                onPress={() => setCatKey(c.key)}
                style={[styles.chip, on ? styles.chipOn : styles.chipOff]}
              >
                <CatIcon category={c.key} size={20} />
                <Text style={[styles.chipText, { color: on ? colors.white : colors.textPrimary }]}>{c.label}</Text>
              </SpringButton>
            );
          })}
        </View>

        <Text style={[styles.formLabel, { marginTop: 16 }]}>공개 설정</Text>
        <SegmentedTabs tabs={['공개', '비공개']} index={vis} onChange={setVis} />

        {vis === 1 ? (
          <Animated.View entering={FadeInDown.duration(260)} style={{ marginTop: 12 }}>
            <Text style={styles.formLabel}>비밀번호</Text>
            <GdqInput
              value={pw}
              onChangeText={setPw}
              placeholder="숫자 4자리"
              secureTextEntry
              keyboardType="number-pad"
              maxLength={4}
            />
          </Animated.View>
        ) : null}

        <SpringButton style={styles.createBtn} onPress={onCreate}>
          <Text style={styles.createText}>만들기</Text>
        </SpringButton>
      </BottomSheet>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 16, paddingTop: 14, paddingBottom: 130 },
  empty: { textAlign: 'center', color: colors.textSecondary, fontSize: 14, marginTop: 40, fontFamily: fonts.bodyR },
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
  name: { fontSize: 15, fontWeight: '600', color: colors.primaryDark, fontFamily: fonts.bodyM },
  info: { fontSize: 13, color: INFO, fontFamily: fonts.bodyR },
  makeBtn: { height: 52, borderRadius: 8, backgroundColor: colors.gold, alignItems: 'center', justifyContent: 'center' },
  makeText: { fontFamily: fonts.pixel, fontSize: 18, color: colors.primaryDark },
  // create form
  formLabel: { fontSize: 12, fontWeight: '600', color: colors.textPrimary, marginBottom: 7, fontFamily: fonts.bodyM },
  chipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    height: 40,
    borderRadius: 12,
    paddingHorizontal: 12,
  },
  chipOn: { backgroundColor: colors.primaryDark, borderWidth: 2, borderColor: colors.primaryDark },
  chipOff: { backgroundColor: colors.white, borderWidth: 1, borderColor: colors.inputBorder },
  chipText: { fontSize: 13, fontWeight: '600', fontFamily: fonts.bodyM },
  createBtn: {
    height: 52,
    borderRadius: 8,
    backgroundColor: colors.gold,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 22,
  },
  createText: { fontFamily: fonts.pixel, fontSize: 18, color: colors.primaryDark },
});
