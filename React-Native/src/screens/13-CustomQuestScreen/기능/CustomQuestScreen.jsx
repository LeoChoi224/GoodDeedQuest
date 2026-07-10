// CustomQuestScreen.js — React Native (Expo) 커스텀 퀘스트 등록
// 선행퀘스트 / 스토리보드 13번 기준
// 경로: 메인페이지 -> 커스텀 퀘스트 등록 (직접 만들기)
// 등록된 퀘스트는 관리자 검토 후 게시됨 (Quest.생성자 = 'USER', status는 검토 후 결정)

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft } from 'lucide-react-native';
import Svg, { Path } from 'react-native-svg';

import { COLORS } from '../디자인/CustomQuestScreen.styles';
import { styles } from '../디자인/CustomQuestScreen.styles';

const CATEGORY_LABELS = ['봉사', '환경', '나눔', '동물', '지역사회', '기타'];
const REWARD_NOTICE_TEXT = '포인트 보상은 검토 후 난이도에 맞게 책정돼요';

function CareIcon({ size = 18 }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round">
      <Path d="M12 6.8c-.9-1.6-3-1.8-4.1-.4-.9 1.1-.7 2.7.4 3.7L12 13l3.7-2.9c1.1-1 1.3-2.6.4-3.7-1.1-1.4-3.2-1.2-4.1.4Z" />
      <Path d="M4.3 13.2c0 3.2 2.9 5.9 6.4 6.3" />
      <Path d="M19.7 13.2c0 3.2-2.9 5.9-6.4 6.3" />
    </Svg>
  );
}

export default function CustomQuestScreen({ navigation }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [category, setCategory] = useState(null);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const canSubmit =
    title.trim().length > 0 &&
    description.trim().length > 0 &&
    !!category;

  const onSubmit = () => {
    if (!canSubmit) return;
    // TODO: 실제 퀘스트 등록 API 연동 (Quest 생성, 생성자='USER')
    setIsSubmitted(true);
    setTimeout(() => navigation.navigate('Main'), 2000);
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} hitSlop={10}>
          <ChevronLeft size={22} color={COLORS.ink} />
        </TouchableOpacity>
        <View style={styles.logoBadge}>
          <CareIcon size={18} />
        </View>
        <Text style={styles.logo}>선·퀘</Text>
      </View>

      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View>
          <Text style={styles.title}>나만의 선행퀘스트를{'\n'}만들어 보세요</Text>
          <Text style={styles.subLabel}>등록한 퀘스트는 검토 후 게시돼요</Text>
        </View>

        <View style={{ gap: 8 }}>
          <Text style={styles.sectionLabel}>퀘스트 제목</Text>
          <TextInput
            style={styles.input}
            placeholder="예: 동네 어르신 짐 들어드리기"
            placeholderTextColor={COLORS.inkMuted48}
            value={title}
            onChangeText={setTitle}
          />
        </View>

        <View style={{ gap: 8 }}>
          <Text style={styles.sectionLabel}>퀘스트 설명</Text>
          <TextInput
            style={[styles.input, styles.textarea]}
            placeholder="어떤 선행인지, 어떻게 수행하면 되는지 설명해 주세요"
            placeholderTextColor={COLORS.inkMuted48}
            value={description}
            onChangeText={setDescription}
            multiline
            textAlignVertical="top"
          />
        </View>

        <View style={{ gap: 8 }}>
          <Text style={styles.sectionLabel}>장소 (선택)</Text>
          {/* TODO: 지도 API 연동 후 텍스트 입력 대신 지도에서 위치를 선택하는 UI로 교체 */}
          <TextInput
            style={styles.input}
            placeholder="예: 우리 동네, 특정 장소 없음"
            placeholderTextColor={COLORS.inkMuted48}
            value={location}
            onChangeText={setLocation}
          />
        </View>

        <View style={{ gap: 10 }}>
          <Text style={styles.sectionLabel}>카테고리</Text>
          <View style={styles.grid}>
            {CATEGORY_LABELS.map((label) => {
              const selected = category === label;
              return (
                <TouchableOpacity
                  key={label}
                  activeOpacity={0.9}
                  onPress={() => setCategory(label)}
                  style={[
                    styles.chip,
                    {
                      backgroundColor: selected ? COLORS.primary : COLORS.parchment,
                      borderColor: selected ? COLORS.primary : COLORS.hairline,
                    },
                  ]}
                >
                  <Text style={{ color: selected ? COLORS.canvas : COLORS.ink, fontSize: 15 }}>{label}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        <View style={styles.noticeCard}>
          <Text style={styles.noticeText}>{isSubmitted ? '보상 책정완료' : REWARD_NOTICE_TEXT}</Text>
          {isSubmitted && (
            <View style={{ flexDirection: 'row', gap: 8, marginTop: 10 }}>
              <View style={styles.rewardBadge}>
                <Text style={styles.rewardBadgeLabel}>EXP</Text>
                <Text style={styles.rewardBadgeValue}>+30</Text>
              </View>
              <View style={styles.rewardBadge}>
                <Text style={styles.rewardBadgeLabel}>포인트</Text>
                <Text style={styles.rewardBadgeValue}>+50</Text>
              </View>
            </View>
          )}
        </View>
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          disabled={!canSubmit}
          activeOpacity={0.95}
          onPress={onSubmit}
          style={[styles.submitButton, { backgroundColor: canSubmit ? COLORS.primary : COLORS.hairline }]}
        >
          <Text style={[styles.submitButtonText, { color: canSubmit ? COLORS.canvas : COLORS.inkMuted48 }]}>
            등록하기
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

