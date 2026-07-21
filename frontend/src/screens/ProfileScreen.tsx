/**
 * SCREEN 4 · 프로필 입력 — 닉네임(중복확인 2~10자) · 생년월일 · 선호 카테고리(6종 토글)
 * · 활동가능 시간대(4종 토글). Category/time cells use the fixed pixel icon set and
 * toggle to the teal selected state. Grids stagger in (Fade List).
 */
import React, { useState } from 'react';
import { View, Text, Image, StyleSheet, ScrollView, Pressable, KeyboardAvoidingView, Platform } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeInDown } from 'react-native-reanimated';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../navigation/RootNavigator';
import { colors, fonts, radii, shadow, CATEGORY_DEFS, CATEGORY_ICONS, TIME_DEFS } from '../theme';
import HazeBackground from '../components/HazeBackground';
import { AppHeader } from '../components/Chrome';
import GdqInput from '../components/GdqInput';
import SpringButton from '../components/SpringButton';
import Shake from '../components/Shake';
import { CalIcon } from '../components/PixelIcons';
import { useSignup } from '../context/SignupContext';
import DateTimePicker from '@react-native-community/datetimepicker';
import { useToast } from '../components/Toast';
import { register } from '../api/auth';

type Props = NativeStackScreenProps<RootStackParamList, 'Profile'>;

function formatDate(d: Date) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export default function ProfileScreen({ navigation }: Props) {
  const insets = useSafeAreaInsets();
  const s = useSignup();
  const toast = useToast();
  const [nickShake, setNickShake] = useState(0);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const onCheckNick = () => {
    const ok = s.checkNick();
    if (!ok) setNickShake((v) => v + 1);
  };

  const onChangeBirthday = (_event: any, selectedDate?: Date) => {
    if (Platform.OS === 'android') setShowDatePicker(false);
    if (selectedDate) s.setBirthday(selectedDate);
  };

  const onNext = async () => {
    const ok = s.nickOk || s.checkNick();
    if (!ok) {
      setNickShake((v) => v + 1);
      return;
    }
    if (!s.birthday) {
      toast.show('생년월일을 선택해 주세요.');
      return;
    }

    const category = Object.keys(s.cats).filter((k) => s.cats[k]);
    const active_time = Object.keys(s.times).filter((k) => s.times[k]);

    setSubmitting(true);
    try {
      await register({
        email: s.email,
        password: s.password,
        nickname: s.nickname,
        birthday: formatDate(s.birthday),
        category,
        active_time,
      });
      navigation.navigate('Complete');
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      toast.show(typeof detail === 'string' ? detail : '회원가입에 실패했습니다. 다시 시도해 주세요.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <View style={styles.root}>
      <StatusBar style="dark" />
      <HazeBackground />

      <View style={{ paddingTop: insets.top, backgroundColor: colors.white }}>
        <AppHeader onBack={() => navigation.goBack()} />
      </View>

      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
          <Text style={styles.h1}>프로필을 입력해 주세요</Text>

          {/* nickname */}
          <Text style={styles.label}>닉네임</Text>
          <Shake trigger={nickShake}>
            <View style={styles.row}>
              <View style={{ flex: 1 }}>
                <GdqInput value={s.nickname} onChangeText={s.setNickname} placeholder="닉네임을 입력하세요" />
              </View>
              <SpringButton style={styles.dupBtn} onPress={onCheckNick}>
                <Text style={styles.dupText}>중복확인</Text>
              </SpringButton>
            </View>
            {s.nickMsg ? <Text style={[styles.fieldMsg, { color: s.nickMsg.color }]}>{s.nickMsg.text}</Text> : null}
          </Shake>

          {/* birth */}
          <Text style={[styles.label, { marginTop: 14 }]}>생년월일</Text>
          <Pressable onPress={() => setShowDatePicker(true)}>
            <GdqInput
              editable={false}
              placeholder="생년월일을 선택하세요"
              value={s.birthday ? formatDate(s.birthday) : ''}
              style={{ color: s.birthday ? colors.textPrimary : colors.textMuted }}
              rightAccessory={<CalIcon />}
            />
          </Pressable>
          {showDatePicker && (
            <DateTimePicker
              value={s.birthday ?? new Date(2000, 0, 1)}
              mode="date"
              display={Platform.OS === 'ios' ? 'spinner' : 'default'}
              maximumDate={new Date()}
              onChange={onChangeBirthday}
            />
          )}
          {Platform.OS === 'ios' && showDatePicker && (
            <SpringButton style={styles.dateDoneBtn} onPress={() => setShowDatePicker(false)}>
              <Text style={styles.dateDoneText}>완료</Text>
            </SpringButton>
          )}

          {/* categories */}
          <Text style={styles.section}>선호 카테고리</Text>
          <View style={styles.grid}>
            {CATEGORY_DEFS.map((c, i) => {
              const on = !!s.cats[c.key];
              return (
                <Animated.View key={c.key} entering={FadeInDown.delay(i * 60).duration(400)} style={styles.gridCell}>
                  <Pressable
                    onPress={() => s.toggleCat(c.key)}
                    style={[styles.catCell, on ? styles.cellOn : styles.cellOff]}
                  >
                    <Image source={CATEGORY_ICONS[c.key]} style={styles.catIcon} />
                    <Text style={[styles.catLabel, { color: on ? colors.white : colors.textPrimary }]}>{c.label}</Text>
                  </Pressable>
                </Animated.View>
              );
            })}
          </View>

          {/* times */}
          <Text style={styles.section}>활동가능 시간대</Text>
          <View style={styles.grid}>
            {TIME_DEFS.map((label, i) => {
              const on = !!s.times[label];
              return (
                <Animated.View key={label} entering={FadeInDown.delay(i * 60).duration(400)} style={styles.gridCell}>
                  <Pressable
                    onPress={() => s.toggleTime(label)}
                    style={[styles.timeCell, on ? styles.cellOn : styles.cellOff]}
                  >
                    <Text style={[styles.timeLabel, { color: on ? colors.white : colors.textPrimary }]}>{label}</Text>
                  </Pressable>
                </Animated.View>
              );
            })}
          </View>
        </ScrollView>
      </KeyboardAvoidingView>

      <LinearGradient
        colors={['rgba(238,246,240,0)', colors.screenBg]}
        locations={[0, 0.3]}
        style={[styles.footer, { paddingBottom: insets.bottom + 20 }]}
      >
        <SpringButton onPress={onNext} style={[styles.nextBtn, shadow.button]} disabled={submitting}>
          <Text style={styles.nextText}>{submitting ? '가입 처리 중...' : '다음'}</Text>
        </SpringButton>
      </LinearGradient>
    </View>
  );
}

const CELL_GAP = 10;

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 20, paddingTop: 26, paddingBottom: 130 },
  h1: { fontSize: 20, fontWeight: '700', color: colors.textPrimary, marginBottom: 22, fontFamily: fonts.bodyB },
  label: { fontSize: 12, fontWeight: '600', color: colors.textPrimary, marginBottom: 7, fontFamily: fonts.bodyM },
  row: { flexDirection: 'row', gap: 8 },
  dupBtn: { width: 80, height: 50, borderRadius: radii.input, backgroundColor: colors.primaryDark, alignItems: 'center', justifyContent: 'center' },
  dupText: { color: colors.white, fontSize: 13, fontWeight: '600', fontFamily: fonts.bodyM },
  fieldMsg: { marginTop: 8, marginLeft: 2, fontSize: 12, fontWeight: '600', fontFamily: fonts.bodyM },
  dateDoneBtn: { alignSelf: 'flex-end', marginTop: 6, paddingHorizontal: 16, paddingVertical: 8, borderRadius: radii.input, backgroundColor: colors.primaryDark },
  dateDoneText: { color: colors.white, fontSize: 13, fontWeight: '600', fontFamily: fonts.bodyM },
  section: { fontSize: 14, fontWeight: '700', color: colors.textPrimary, marginTop: 22, marginBottom: 12, fontFamily: fonts.bodyB },
  grid: { flexDirection: 'row', flexWrap: 'wrap', marginHorizontal: -CELL_GAP / 2 },
  gridCell: { width: '50%', paddingHorizontal: CELL_GAP / 2, marginBottom: CELL_GAP },
  catCell: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    height: 52,
    borderRadius: radii.chip,
    paddingHorizontal: 12,
  },
  timeCell: { alignItems: 'center', justifyContent: 'center', height: 48, borderRadius: radii.chip },
  cellOn: { backgroundColor: colors.primaryDark, borderWidth: 2, borderColor: colors.primaryDark },
  cellOff: { backgroundColor: colors.white, borderWidth: 1, borderColor: colors.inputBorder },
  catIcon: { width: 34, height: 34, borderRadius: 8 },
  catLabel: { fontSize: 14, fontWeight: '600', fontFamily: fonts.bodyM },
  timeLabel: { fontSize: 14, fontWeight: '600', fontFamily: fonts.bodyM },
  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, paddingHorizontal: 20, paddingTop: 16 },
  nextBtn: { height: 52, borderRadius: radii.button, backgroundColor: colors.primaryDark, alignItems: 'center', justifyContent: 'center' },
  nextText: { color: colors.white, fontSize: 16, fontWeight: '700', fontFamily: fonts.bodyB },
});
