// QuestDetailScreen.js — React Native (Expo) 퀘스트 상세 페이지
// 선행퀘스트 / 스토리보드 12번 기준 (최신 dc.html과 동기화 — 애니메이션/이펙트 포함)
//
// 경로: 메인페이지 -> 퀘스트 상세 페이지
// 진행중 퀘스트면 "퀘스트 인증하기" → 하단 시트 팝업(인증 제출) 오픈. 아니면 "퀘스트 시작하기".
// ⚠️ 14-QuestSubmissionScreen(단독 페이지)은 폐기되었습니다 — 인증 제출은 이 화면의
//    하단 시트 팝업으로 통합되었습니다 (dc.html 12번과 동일 구조).
//
// 추가 설치 필요: expo-linear-gradient
//   npx expo install expo-linear-gradient
//
// 반영된 애니메이션/이펙트:
// - 퀘스트 카드 플로팅(위아래 둥둥 + 살짝 확대) 루프
// - 카드 상단 배지 플로팅 + 회전 루프
// - 스파클(반짝이는 별) 여러 개, 서로 다른 딜레이로 트윈클 루프
// - 하단 시트 팝업: 슬라이드업으로 오픈, 인증 완료 시 체크마크 스프링 팝(check pop)

import React, { useState, useRef, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, Modal, Pressable, Animated, Easing } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, Check, Camera, X } from 'lucide-react-native';
import Svg, { Path, Circle } from 'react-native-svg';
import { LinearGradient } from 'expo-linear-gradient';

import { COLORS, RADIUS } from '../디자인/QuestDetailScreen.styles';
import { styles } from '../디자인/QuestDetailScreen.styles';

const MEDIA_LABEL = '사진'; // TODO: quest.verification_method 값에 따라 '영상'으로 분기

function CareIcon({ size = 18, color = '#fff' }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round">
      <Path d="M12 6.8c-.9-1.6-3-1.8-4.1-.4-.9 1.1-.7 2.7.4 3.7L12 13l3.7-2.9c1.1-1 1.3-2.6.4-3.7-1.1-1.4-3.2-1.2-4.1.4Z" />
      <Path d="M4.3 13.2c0 3.2 2.9 5.9 6.4 6.3" />
      <Path d="M19.7 13.2c0 3.2-2.9 5.9-6.4 6.3" />
    </Svg>
  );
}

function Sparkle({ size = 10, color = COLORS.gold, style, duration = 1600, delay = 0 }) {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: 1, duration, delay, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(anim, { toValue: 0, duration, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, []);
  const scale = anim.interpolate({ inputRange: [0, 1], outputRange: [0.3, 1.1] });
  const rotate = anim.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '20deg'] });
  return (
    <Animated.View style={[style, { opacity: anim, transform: [{ scale }, { rotate }] }]}>
      <Svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
        <Path d="M12 2l2 7 7 2-7 2-2 7-2-7-7-2 7-2z" />
      </Svg>
    </Animated.View>
  );
}

function statusCopy(status, mediaLabel) {
  if (status === 'reviewing') return `AI가 ${mediaLabel}을 확인하고 있어요`;
  if (status === 'approved') return '인증 완료 · 보상 지급 완료';
  return '제출하면 AI가 인증 내용을 검토해요';
}

// 데모용 목데이터. 실제로는 navigation params(questId)로 서버에서 조회.
const DEMO_QUEST = { title: '엄마한테 사과하기', description: '가족에게 마음을 담아 진심으로 사과해보세요. 대화를 나눈 사진이나 짧은 영상으로 인증할 수 있어요.', exp: 20, points: 30 };

export default function QuestDetailScreen({ navigation, route }) {
  const questParam = route?.params?.quest ?? DEMO_QUEST;
  const quest = { ...DEMO_QUEST, ...questParam };
  const [started, setStarted] = useState(!!route?.params?.inProgress);
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const [hasMedia, setHasMedia] = useState(false);
  const [caption, setCaption] = useState('');
  const [submitStatus, setSubmitStatus] = useState('idle'); // idle | reviewing | approved

  const reviewTimer = useRef(null);
  const closeTimer = useRef(null);
  useEffect(
    () => () => {
      clearTimeout(reviewTimer.current);
      clearTimeout(closeTimer.current);
    },
    []
  );

  // 카드 플로팅 (위아래 + 살짝 확대), 3.2s 왕복
  const cardFloat = useRef(new Animated.Value(0)).current;
  // 배지 플로팅 (위아래 + 회전), 3.2s 왕복
  const badgeFloat = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const loop1 = Animated.loop(
      Animated.sequence([
        Animated.timing(cardFloat, { toValue: 1, duration: 1600, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(cardFloat, { toValue: 0, duration: 1600, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    );
    const loop2 = Animated.loop(
      Animated.sequence([
        Animated.timing(badgeFloat, { toValue: 1, duration: 1600, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(badgeFloat, { toValue: 0, duration: 1600, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    );
    loop1.start();
    loop2.start();
    return () => {
      loop1.stop();
      loop2.stop();
    };
  }, []);

  const cardTranslateY = cardFloat.interpolate({ inputRange: [0, 1], outputRange: [0, -12] });
  const cardScale = cardFloat.interpolate({ inputRange: [0, 1], outputRange: [1, 1.02] });
  const badgeTranslateY = badgeFloat.interpolate({ inputRange: [0, 1], outputRange: [0, -12] });
  const badgeRotate = badgeFloat.interpolate({ inputRange: [0, 1], outputRange: ['-4deg', '4deg'] });

  // 인증 완료 체크마크 스프링 팝
  const checkPop = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    if (submitStatus === 'approved') {
      checkPop.setValue(0);
      Animated.spring(checkPop, { toValue: 1, friction: 5, tension: 140, useNativeDriver: true }).start();
    }
  }, [submitStatus]);

  const startButtonLabel = started ? '퀘스트 인증하기' : '퀘스트 시작하기';

  const onStart = () => {
    if (started) setShowSubmitModal(true);
    else setStarted(true);
  };

  const closeSubmitModal = () => {
    if (submitStatus === 'reviewing') return;
    clearTimeout(reviewTimer.current);
    clearTimeout(closeTimer.current);
    setShowSubmitModal(false);
    setHasMedia(false);
    setCaption('');
    setSubmitStatus('idle');
  };

  const onToggleMedia = () => {
    if (submitStatus !== 'idle') return;
    setHasMedia((v) => !v);
  };

  const canSubmit = hasMedia && submitStatus === 'idle';

  const onSubmit = () => {
    if (!canSubmit) return;
    // TODO: 실제 인증 제출 API 연동 (QuestSubmission 생성, media 업로드)
    setSubmitStatus('reviewing');
    reviewTimer.current = setTimeout(() => {
      setSubmitStatus('approved');
    }, 1600);
  };

  const onFinishQuest = () => {
    navigation.navigate('Main');
  };

  let submitLabel = '인증 제출하기';
  if (submitStatus === 'reviewing') submitLabel = '검토 중...';
  if (submitStatus === 'approved') submitLabel = '완료';

  return (
    <LinearGradient colors={['#E8F7EA', '#F3FBF4', '#FFFFFF']} locations={[0, 0.45, 1]} style={{ flex: 1 }}>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate('Main')} hitSlop={10} style={{ padding: 4 }}>
            <ChevronLeft size={22} color={COLORS.ink} />
          </TouchableOpacity>
          <View style={styles.logoBadge}>
            <CareIcon size={18} />
          </View>
          <Text style={styles.logo}>선·퀘</Text>
        </View>

        <View style={styles.content}>
          {/* 퀘스트 정보 카드 (플로팅 + 스파클) */}
          <Animated.View style={{ alignItems: 'center', transform: [{ translateY: cardTranslateY }, { scale: cardScale }] }}>
            <Sparkle size={14} color={COLORS.gold} style={{ position: 'absolute', top: 2, left: '24%', zIndex: 3 }} duration={1600} />
            <Sparkle size={12} color={COLORS.mint} style={{ position: 'absolute', top: -6, left: '46%', zIndex: 3 }} duration={1600} delay={1070} />
            <Sparkle size={10} color={COLORS.gold} style={{ position: 'absolute', top: 4, right: '22%', zIndex: 3 }} duration={1600} delay={2130} />

            <Animated.View style={[styles.badgeCircle, { transform: [{ translateY: badgeTranslateY }, { rotate: badgeRotate }] }]}>
              <LinearGradient colors={['#044951', COLORS.primary]} style={styles.badgeCircleGradient}>
                <CareIcon size={28} color={COLORS.mint} />
              </LinearGradient>
            </Animated.View>

            <LinearGradient colors={[COLORS.gold, COLORS.mint, COLORS.gold]} style={styles.questCardBorder}>
              <LinearGradient colors={['#0c4a50', COLORS.primary, '#052024']} locations={[0, 0.55, 1]} style={styles.questCard}>
                <Sparkle size={9} color={COLORS.mint} style={{ position: 'absolute', top: 64, left: 22 }} duration={1600} delay={550} />
                <Sparkle size={8} color={COLORS.gold} style={{ position: 'absolute', bottom: 54, right: 26 }} duration={1600} delay={1900} />

                <Text style={styles.questTitle}>{quest.title}</Text>
                <View style={styles.rewardRow}>
                  <RewardBadge label="EXP" value={quest.exp} />
                  <RewardBadge label="포인트" value={quest.points} />
                </View>
              </LinearGradient>
            </LinearGradient>
          </Animated.View>

          <View style={{ gap: 6, marginTop: 8 }}>
            <Text style={styles.sectionLabel}>퀘스트 설명</Text>
            <Text style={styles.description}>{quest.description}</Text>
          </View>

          <View style={{ flex: 1 }} />

          <TouchableOpacity style={styles.startButton} activeOpacity={0.9} onPress={onStart}>
            <Text style={styles.startButtonText}>{startButtonLabel}</Text>
          </TouchableOpacity>
        </View>

        {/* 인증 제출 팝업 (하단 시트) */}
        <Modal statusBarTranslucent visible={showSubmitModal} transparent animationType="slide" onRequestClose={closeSubmitModal}>
          <View style={styles.sheetOverlay}>
            <Pressable style={{ flex: 1 }} onPress={closeSubmitModal} />
            <View style={styles.sheet}>
              <View style={styles.sheetHandle} />

              {submitStatus === 'approved' ? (
                <View style={{ alignItems: 'center', gap: 16, paddingVertical: 12 }}>
                  <View style={{ width: 76, height: 76, alignItems: 'center', justifyContent: 'center' }}>
                    <Sparkle size={12} color={COLORS.gold} style={{ position: 'absolute', top: -6, left: 2 }} duration={1300} />
                    <Sparkle size={10} color={COLORS.mint} style={{ position: 'absolute', bottom: -4, right: 0 }} duration={1300} delay={900} />
                    <Animated.View style={{ transform: [{ scale: checkPop }] }}>
                      <LinearGradient colors={[COLORS.mint, COLORS.gold]} style={styles.approvedCheckCircle}>
                        <Check size={34} color={COLORS.primary} strokeWidth={2.6} />
                      </LinearGradient>
                    </Animated.View>
                  </View>
                  <View style={{ alignItems: 'center', gap: 4 }}>
                    <Text style={styles.approvedTitle}>인증 완료!</Text>
                    <Text style={styles.approvedSubtitle}>{quest.title} 미션을 달성했어요</Text>
                  </View>
                  <View style={{ flexDirection: 'row', gap: 8 }}>
                    <RewardBadge label="EXP" value={quest.exp} big />
                    <RewardBadge label="포인트" value={quest.points} big />
                  </View>
                  <TouchableOpacity style={[styles.startButton, { marginTop: 4 }]} activeOpacity={0.9} onPress={onFinishQuest}>
                    <Text style={styles.startButtonText}>확인</Text>
                  </TouchableOpacity>
                </View>
              ) : (
                <ScrollView keyboardShouldPersistTaps="handled">
                  <View style={styles.sheetHeaderRow}>
                    <Text style={styles.sheetTitle}>인증하고 보상을 받아보세요</Text>
                    <TouchableOpacity onPress={closeSubmitModal} hitSlop={8}>
                      <X size={20} color={COLORS.inkMuted48} />
                    </TouchableOpacity>
                  </View>

                  <View style={styles.questSummaryRow}>
                    <View style={styles.questSummaryIcon}>
                      <Check size={18} color={COLORS.canvas} />
                    </View>
                    <View style={{ minWidth: 0, flex: 1 }}>
                      <Text style={styles.questSummaryTitle} numberOfLines={1}>
                        {quest.title}
                      </Text>
                      <Text style={styles.questSummaryReward}>
                        보상 · EXP +{quest.exp} · 포인트 +{quest.points}
                      </Text>
                    </View>
                  </View>

                  <View style={{ gap: 8, marginTop: 16 }}>
                    <Text style={styles.sectionLabel}>인증 {MEDIA_LABEL}</Text>
                    <TouchableOpacity
                      activeOpacity={0.9}
                      onPress={onToggleMedia}
                      style={[
                        styles.uploadBox,
                        hasMedia
                          ? { backgroundColor: '#F0FAF2', borderColor: 'rgba(3,50,54,0.25)', borderStyle: 'solid' }
                          : { backgroundColor: COLORS.parchment, borderColor: COLORS.hairlineSolid, borderStyle: 'dashed' },
                      ]}
                    >
                      {hasMedia ? (
                        <View style={{ alignItems: 'center', gap: 8 }}>
                          <View style={styles.uploadCheckBadge}>
                            <Check size={22} color={COLORS.canvas} strokeWidth={2.4} />
                          </View>
                          <Text style={styles.uploadTitle}>{MEDIA_LABEL} 첨부 완료</Text>
                          <Text style={styles.uploadHint}>다시 탭하면 선택을 취소해요</Text>
                        </View>
                      ) : (
                        <View style={{ alignItems: 'center', gap: 8 }}>
                          <Camera size={28} color={COLORS.inkMuted48} strokeWidth={1.6} />
                          <Text style={styles.uploadTitle}>탭하여 자료 첨부</Text>
                          <Text style={styles.uploadHint}>JPG, PNG, MP4 지원</Text>
                        </View>
                      )}
                    </TouchableOpacity>
                  </View>

                  <View style={{ gap: 8, marginTop: 16 }}>
                    <Text style={styles.sectionLabel}>설명 (선택)</Text>
                    <TextInput
                      style={[styles.input, styles.textarea]}
                      placeholder="인증 상황을 간단히 설명해 주세요"
                      placeholderTextColor={COLORS.inkMuted48}
                      value={caption}
                      onChangeText={setCaption}
                      multiline
                      textAlignVertical="top"
                    />
                  </View>

                  <View style={[styles.noticeCard, { marginTop: 16 }]}>
                    <Text style={styles.noticeText}>{statusCopy(submitStatus, MEDIA_LABEL)}</Text>
                  </View>

                  <TouchableOpacity
                    disabled={!canSubmit}
                    activeOpacity={0.95}
                    onPress={onSubmit}
                    style={[styles.submitButton, { backgroundColor: canSubmit ? COLORS.primary : COLORS.hairline, marginTop: 16 }]}
                  >
                    <Text style={[styles.submitButtonText, { color: canSubmit ? COLORS.canvas : COLORS.inkMuted48 }]}>{submitLabel}</Text>
                  </TouchableOpacity>
                </ScrollView>
              )}
            </View>
          </View>
        </Modal>
      </SafeAreaView>
    </LinearGradient>
  );
}

function RewardBadge({ label, value, big }) {
  return (
    <View style={[styles.rewardBadge, big && { paddingVertical: 8, paddingHorizontal: 16 }]}>
      <Text style={[styles.rewardBadgeLabel, big && { fontSize: 14 }]}>{label}</Text>
      <Text style={[styles.rewardBadgeValue, big && { fontSize: 14 }]}>+{value}</Text>
    </View>
  );
}

