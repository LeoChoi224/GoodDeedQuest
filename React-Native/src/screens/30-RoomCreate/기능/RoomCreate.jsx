// 30-RoomCreate.js — React Native (Expo) 방 만들기 (팀 퀘스트 등록 폼)
// 선행퀘스트 / 스토리보드 30번 기준 — 최대 인원 4~10명(경계에서 +/- 버튼 비활성), 공개설정 공개/비공개

import React, { useState, useRef, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, Minus, Plus, Check } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { CareIcon, GreenGradientBG } from '../../../shared/기능/components';
import { styles } from '../디자인/RoomCreate.styles';

const CATEGORY_LABELS = ['봉사', '환경', '나눔', '동물', '지역사회', '기타'];
const VISIBILITY_OPTIONS = ['공개', '비공개'];
const SIZE_MIN = 4;
const SIZE_MAX = 10;

export default function RoomCreateScreen({ navigation }) {
  const [roomName, setRoomName] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState(null);
  const [size, setSize] = useState(4);
  const [visibility, setVisibility] = useState(null);
  const [showToast, setShowToast] = useState(false);
  const navTimer = useRef(null);

  useEffect(() => () => clearTimeout(navTimer.current), []);

  const canSubmit = roomName.trim().length > 0 && !!category && !!visibility && !showToast;

  const onSubmit = () => {
    if (!canSubmit) return;
    setShowToast(true);
    navTimer.current = setTimeout(() => navigation.navigate('Community'), 1800);
  };

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate('TeamChallenge')} hitSlop={10} style={{ padding: 4 }}>
            <ChevronLeft size={22} color={COLORS.ink} />
          </TouchableOpacity>
          <View style={styles.logoBadge}>
            <CareIcon size={18} />
          </View>
          <Text style={styles.logo}>선·퀘</Text>
        </View>

        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <View>
            <Text style={styles.title}>팀 챌린지 방을{'\n'}만들어 보세요</Text>
            <Text style={styles.subtitle}>함께할 팀원을 모아 선행 퀘스트를 완료해보세요</Text>
          </View>

          <View style={{ gap: 8 }}>
            <Text style={styles.label}>방 이름</Text>
            <TextInput style={styles.input} placeholder="예: 저녁마다 산책 인증" placeholderTextColor={COLORS.inkMuted48} value={roomName} onChangeText={setRoomName} />
          </View>

          <View style={{ gap: 8 }}>
            <Text style={styles.label}>방 소개 (선택)</Text>
            <TextInput
              style={[styles.input, styles.textarea]}
              placeholder="어떤 팀 챌린지를 함께 하고 싶은지 소개해 주세요"
              placeholderTextColor={COLORS.inkMuted48}
              value={description}
              onChangeText={setDescription}
              multiline
              textAlignVertical="top"
            />
          </View>

          <View style={{ gap: 10 }}>
            <Text style={styles.label}>챌린지 카테고리</Text>
            <View style={styles.grid}>
              {CATEGORY_LABELS.map((label) => {
                const selected = category === label;
                return (
                  <TouchableOpacity key={label} style={[styles.chip, selected && styles.chipSelected]} onPress={() => setCategory(label)}>
                    <Text style={[styles.chipText, selected && styles.chipTextSelected]}>{label}</Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>

          <View style={{ gap: 10 }}>
            <Text style={styles.label}>최대 인원 (4~10명)</Text>
            <View style={styles.stepperRow}>
              {size > SIZE_MIN ? (
                <TouchableOpacity style={styles.stepBtn} onPress={() => setSize((s) => Math.max(SIZE_MIN, s - 1))}>
                  <Minus size={16} color={COLORS.ink} strokeWidth={2.2} />
                </TouchableOpacity>
              ) : (
                <View style={styles.stepBtn} />
              )}
              <Text style={styles.stepperValue}>{size}명</Text>
              {size < SIZE_MAX ? (
                <TouchableOpacity style={styles.stepBtn} onPress={() => setSize((s) => Math.min(SIZE_MAX, s + 1))}>
                  <Plus size={16} color={COLORS.ink} strokeWidth={2.2} />
                </TouchableOpacity>
              ) : (
                <View style={styles.stepBtn} />
              )}
            </View>
          </View>

          <View style={{ gap: 10 }}>
            <Text style={styles.label}>공개 설정</Text>
            <View style={styles.grid}>
              {VISIBILITY_OPTIONS.map((label) => {
                const selected = visibility === label;
                return (
                  <TouchableOpacity key={label} style={[styles.chip, selected && styles.chipSelected]} onPress={() => setVisibility(label)}>
                    <Text style={[styles.chipText, selected && styles.chipTextSelected]}>{label}</Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>

          {showToast && (
            <View style={styles.noticeCard}>
              <Check size={18} color={COLORS.gold} />
              <Text style={styles.noticeText}>방이 만들어졌어요!</Text>
            </View>
          )}
        </ScrollView>

        <View style={styles.footer}>
          <TouchableOpacity
            disabled={!canSubmit}
            style={[styles.submitButton, { backgroundColor: canSubmit ? COLORS.primary : COLORS.hairline }]}
            onPress={onSubmit}
          >
            <Text style={[styles.submitButtonText, { color: canSubmit ? '#fff' : COLORS.inkMuted48 }]}>{showToast ? '완료' : '방 만들기'}</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    </GreenGradientBG>
  );
}

