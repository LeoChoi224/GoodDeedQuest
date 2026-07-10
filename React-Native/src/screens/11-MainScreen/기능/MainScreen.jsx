// MainScreen.js — React Native (Expo) 메인 페이지 (홈 탭)
// 선행퀘스트 / 스토리보드 11번 기준 (최신 dc.html과 동기화 — 애니메이션/이펙트 포함)
//
// 추가 설치 필요: expo-linear-gradient
//   npx expo install expo-linear-gradient
//
// 반영된 애니메이션/이펙트:
// - 진행중 퀘스트 카드: 좌/우 이동 시 옆에서 슬라이드 + 페이드인 (1s, ease-out 계열)
// - 진행중 퀘스트 카드의 골드→그린 그라디언트 테두리 + 우측 상단 스파클 반짝임
// - 햄버거 메뉴: 아코디언(대카테고리 클릭 시 하위 목록 펼침/접힘, LayoutAnimation으로 부드럽게 + 화살표 회전 애니메이션)
// - 배경: 연두 톤 그라디언트(웰니스 앱 참고 팔레트)

import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  Modal,
  Pressable,
  Animated,
  Easing,
  LayoutAnimation,
  Platform,
  UIManager,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Users, MapPin, Home, Coins, User, ChevronLeft, ChevronRight, X } from 'lucide-react-native';
import Svg, { Path } from 'react-native-svg';
import { LinearGradient } from 'expo-linear-gradient';

import { COLORS, RADIUS, TYPE } from '../디자인/MainScreen.styles';
import { styles } from '../디자인/MainScreen.styles';

if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

function CareIcon({ size = 18, color = '#fff' }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round">
      <Path d="M12 6.8c-.9-1.6-3-1.8-4.1-.4-.9 1.1-.7 2.7.4 3.7L12 13l3.7-2.9c1.1-1 1.3-2.6.4-3.7-1.1-1.4-3.2-1.2-4.1.4Z" />
      <Path d="M4.3 13.2c0 3.2 2.9 5.9 6.4 6.3" />
      <Path d="M19.7 13.2c0 3.2-2.9 5.9-6.4 6.3" />
    </Svg>
  );
}

// 별 모양 스파클 — opacity/scale/rotate가 0→1→0 삼각파로 반복 (dc.html의 sparkleTwinkle 근사)
function Sparkle({ size = 10, color = COLORS.gold, style, duration = 1600 }) {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: 1, duration, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
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

// 데모용 목데이터. 실 서비스에서는 오늘 자정 기준 서버가 갱신.
const IN_PROGRESS_QUESTS = [
  { id: 'p1', title: '헌혈하기' },
  { id: 'p2', title: '노약자 자리 양보하기' },
];

const RECOMMENDED_QUESTS = [
  { id: 'r1', title: '선행 1' },
  { id: 'r2', title: '선행 2' },
  { id: 'r3', title: '선행 3' },
];

const MENU_LABELS = ['공지사항', '설정', '이용약관', '로그아웃'];

// 햄버거 메뉴 맨 아래 — 실제 화면으로 이동하는 항목(관리자/로그인)
const MENU_NAV_ITEMS = [
  { label: '관리자 페이지', screen: 'AdminDashboard' },
  { label: '로그인 페이지', screen: 'Login' },
];

// 대표페이지(하단 5탭) 별 하위 화면 — dc.html의 NAV_SECTIONS과 동일 구조.
// screen: App.js에 등록된 실제 RN 라우트명. 없으면 Placeholder로 이동.
const NAV_SECTIONS = [
  {
    title: '홈',
    items: [
      { label: '메인', screen: 'Main' },
      { label: '퀘스트 상세', screen: 'QuestDetail' },
      { label: '커스텀 퀘스트 등록', screen: 'QuestRegister' },
    ],
  },
  {
    title: '지도',
    items: [
      { label: '지도 메인' },
      { label: '내 주변' },
      { label: '봉사센터 상세' },
      { label: '지역 검색' },
      { label: '대항전' },
      { label: '시군구 랭킹' },
    ],
  },
  {
    title: '상점',
    items: [
      { label: '상점', screen: 'Store' },
      { label: '아이템 상세' },
      { label: '구매 목록' },
    ],
  },
  {
    title: '커뮤니티',
    items: [
      { label: '커뮤니티 메인', screen: 'Community' },
      { label: '팀 챌린지' },
      { label: '방 찾기' },
      { label: '방 만들기' },
      { label: '팀 상세' },
      { label: '유저 추천' },
      { label: '팀 목록' },
      { label: '유저 상세정보' },
      { label: '숏폼 제작' },
    ],
  },
  {
    title: '마이페이지',
    items: [
      { label: '마이페이지', screen: 'MyPage' },
      { label: '마이 레벨' },
      { label: '내 랭킹' },
    ],
  },
];

function AccordionSection({ section, expanded, onToggle, navigation }) {
  const chevronAnim = useRef(new Animated.Value(expanded ? 1 : 0)).current;

  useEffect(() => {
    Animated.timing(chevronAnim, { toValue: expanded ? 1 : 0, duration: 200, easing: Easing.inOut(Easing.ease), useNativeDriver: true }).start();
  }, [expanded]);

  const rotate = chevronAnim.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '90deg'] });

  return (
    <View style={{ gap: 1 }}>
      <TouchableOpacity style={styles.sectionHeader} onPress={onToggle} activeOpacity={0.8}>
        <Text style={styles.sectionTitle}>{section.title}</Text>
        <Animated.View style={{ transform: [{ rotate }] }}>
          <ChevronRight size={13} color="rgba(255,255,255,0.5)" />
        </Animated.View>
      </TouchableOpacity>
      {expanded && (
        <View style={{ paddingBottom: 6 }}>
          {section.items.map((item) => (
            <TouchableOpacity
              key={item.label}
              style={styles.menuItemRow}
              onPress={() => {
                if (item.screen) navigation.navigate(item.screen);
                else navigation.navigate('Placeholder', { title: item.label });
              }}
            >
              <Text style={styles.menuItemRowText}>{item.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
}

export default function MainScreen({ navigation }) {
  const [menuVisible, setMenuVisible] = useState(false);
  const [expandedSection, setExpandedSection] = useState(null);
  const [carouselIndex, setCarouselIndex] = useState(0);
  const [slideDir, setSlideDir] = useState('next');

  const hasActiveQuest = IN_PROGRESS_QUESTS.length > 0;
  const activeTitle = IN_PROGRESS_QUESTS[carouselIndex]?.title ?? '없음';

  // 카드 슬라이드 애니메이션 — carouselIndex가 바뀔 때마다 방향에 맞춰 옆에서 밀려들어옴 (1s)
  const slideX = useRef(new Animated.Value(0)).current;
  const slideOpacity = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    slideX.setValue(slideDir === 'next' ? 16 : -16);
    slideOpacity.setValue(0);
    Animated.parallel([
      Animated.timing(slideX, { toValue: 0, duration: 1000, easing: Easing.bezier(0.16, 1, 0.3, 1), useNativeDriver: true }),
      Animated.timing(slideOpacity, { toValue: 1, duration: 1000, easing: Easing.bezier(0.16, 1, 0.3, 1), useNativeDriver: true }),
    ]).start();
  }, [carouselIndex]);

  const goPrev = () => {
    if (!hasActiveQuest || carouselIndex === 0) return;
    setSlideDir('prev');
    setCarouselIndex((i) => Math.max(0, i - 1));
  };
  const goNext = () => {
    if (!hasActiveQuest || carouselIndex === IN_PROGRESS_QUESTS.length - 1) return;
    setSlideDir('next');
    setCarouselIndex((i) => Math.min(IN_PROGRESS_QUESTS.length - 1, i + 1));
  };

  const toggleSection = (title) => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpandedSection((prev) => (prev === title ? null : title));
  };

  const goToQuestDetail = (title, inProgress) => {
    navigation.navigate('QuestDetail', { quest: { title, exp: 20, points: 30 }, inProgress });
  };

  return (
    <LinearGradient colors={['#E8F7EA', '#F3FBF4', '#FFFFFF']} locations={[0, 0.45, 1]} style={{ flex: 1 }}>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <View style={styles.logoBadge}>
            <CareIcon size={18} />
          </View>
          <Text style={styles.logo}>선·퀘</Text>
          <View style={{ flex: 1 }} />
          <TouchableOpacity onPress={() => setMenuVisible(true)} hitSlop={10}>
            <View style={{ gap: 5 }}>
              <View style={styles.burgerLine} />
              <View style={styles.burgerLine} />
              <View style={styles.burgerLine} />
            </View>
          </TouchableOpacity>
        </View>

        <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
          {/* 진행중 퀘스트 캐러셀 */}
          <View style={{ gap: 10 }}>
            <Text style={styles.rowSectionTitle}>진행중인 퀘스트</Text>
            <View style={styles.carouselRow}>
              <TouchableOpacity onPress={goPrev} disabled={carouselIndex === 0} hitSlop={8}>
                <ChevronLeft size={20} color={carouselIndex === 0 ? COLORS.hairline : COLORS.inkMuted48} />
              </TouchableOpacity>

              <TouchableOpacity
                activeOpacity={hasActiveQuest ? 0.85 : 1}
                onPress={hasActiveQuest ? () => goToQuestDetail(activeTitle, true) : undefined}
                style={{ flex: 1 }}
              >
                <LinearGradient
                  colors={hasActiveQuest ? [COLORS.gold, COLORS.mint] : ['rgba(0,0,0,0.06)', 'rgba(0,0,0,0.06)']}
                  style={styles.activeCardOuter}
                >
                  <LinearGradient
                    colors={hasActiveQuest ? ['#0c4a50', COLORS.primary] : ['#5b6a6b', '#46504f']}
                    style={styles.activeCardShell}
                  >
                    <Animated.View style={[styles.activeCardContent, { transform: [{ translateX: slideX }], opacity: slideOpacity }]}>
                      {hasActiveQuest && <Sparkle size={9} color={COLORS.gold} style={{ position: 'absolute', top: 4, right: 34 }} duration={1400} />}
                      <View style={styles.activeCardIconBadge}>
                        <CareIcon size={16} color={hasActiveQuest ? COLORS.mint : 'rgba(255,255,255,0.4)'} />
                      </View>
                      <View style={{ flex: 1, minWidth: 0, gap: 1 }}>
                        <Text style={[styles.activeStatusLabel, { color: hasActiveQuest ? COLORS.mint : 'rgba(255,255,255,0.4)' }]}>
                          {hasActiveQuest ? '진행중' : '대기중'}
                        </Text>
                        <Text
                          style={[styles.activeCardTitle, { color: hasActiveQuest ? COLORS.goldTint : 'rgba(255,255,255,0.5)' }]}
                          numberOfLines={1}
                        >
                          {hasActiveQuest ? activeTitle : '진행중인 퀘스트가 없어요'}
                        </Text>
                      </View>
                      {hasActiveQuest && <ChevronRight size={16} color="rgba(253,246,227,0.7)" />}
                    </Animated.View>
                  </LinearGradient>
                </LinearGradient>
              </TouchableOpacity>

              <TouchableOpacity onPress={goNext} disabled={carouselIndex === IN_PROGRESS_QUESTS.length - 1} hitSlop={8}>
                <ChevronRight size={20} color={carouselIndex === IN_PROGRESS_QUESTS.length - 1 ? COLORS.hairline : COLORS.inkMuted48} />
              </TouchableOpacity>
            </View>
          </View>

          {/* 오늘의 추천 퀘스트 */}
          <View style={{ gap: 12 }}>
            <Text style={styles.sectionTitleLg}>오늘의 추천 퀘스트</Text>
            <View style={{ gap: 10 }}>
              {RECOMMENDED_QUESTS.map((q) => (
                <View key={q.id} style={styles.questRow}>
                  <View style={styles.questRowIconBadge}>
                    <CareIcon size={17} color={COLORS.primary} />
                  </View>
                  <Text style={styles.questRowTitle} numberOfLines={1}>
                    {q.title}
                  </Text>
                  <TouchableOpacity style={styles.detailButton} activeOpacity={0.85} onPress={() => goToQuestDetail(q.title, false)}>
                    <Text style={styles.detailButtonText}>상세보기</Text>
                  </TouchableOpacity>
                </View>
              ))}
              <TouchableOpacity style={styles.reRollButton} activeOpacity={0.85}>
                <Text style={styles.reRollButtonText}>다시 추천 받기</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* 하단 액션 */}
          <View style={styles.actionRow}>
            <TouchableOpacity style={styles.actionButton} activeOpacity={0.9} onPress={() => navigation.navigate('QuestRegister')}>
              <Text style={styles.actionButtonText}>퀘스트 등록</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.actionButton} activeOpacity={0.9} onPress={() => navigation.navigate('QuestRecommendChat')}>
              <Text style={styles.actionButtonText}>커스텀 추천</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>

        {/* 하단 네비바 (5탭 고정) */}
        <View style={styles.bottomNav}>
          <NavItem Icon={Users} label="커뮤니티" onPress={() => navigation.navigate('Community')} />
          <NavItem Icon={MapPin} label="지도" onPress={() => navigation.navigate('Map')} />
          <NavItem Icon={Home} label="홈" active onPress={() => navigation.navigate('Main')} />
          <NavItem Icon={Coins} label="상점" onPress={() => navigation.navigate('Store')} />
          <NavItem Icon={User} label="마이" onPress={() => navigation.navigate('MyPage')} />
        </View>

        {/* 우측 슬라이드 햄버거 메뉴 — 아코디언 */}
        <Modal statusBarTranslucent visible={menuVisible} transparent animationType="fade" onRequestClose={() => setMenuVisible(false)}>
          <View style={styles.menuOverlayRow}>
            <Pressable style={{ flex: 1 }} onPress={() => setMenuVisible(false)} />
            <LinearGradient colors={['#033236', '#063e42', '#04484d']} locations={[0, 0.55, 1]} style={styles.menuPanel}>
              <ScrollView showsVerticalScrollIndicator={false}>
                <View style={styles.menuHeader}>
                  <View style={styles.menuLogoBadge}>
                    <CareIcon size={16} color={COLORS.mint} />
                  </View>
                  <Text style={styles.menuLogoText}>선행퀘스트</Text>
                  <View style={{ flex: 1 }} />
                  <TouchableOpacity onPress={() => setMenuVisible(false)} hitSlop={10}>
                    <X size={20} color="rgba(255,255,255,0.55)" />
                  </TouchableOpacity>
                </View>

                <View style={{ gap: 8 }}>
                  {NAV_SECTIONS.map((section) => (
                    <AccordionSection
                      key={section.title}
                      section={section}
                      expanded={expandedSection === section.title}
                      onToggle={() => toggleSection(section.title)}
                      navigation={navigation}
                    />
                  ))}
                </View>

                <View style={styles.menuDivider} />

                <View style={{ gap: 1 }}>
                  {MENU_LABELS.map((label) => (
                    <TouchableOpacity key={label} style={styles.menuFooterItem}>
                      <Text style={styles.menuFooterItemText}>{label}</Text>
                    </TouchableOpacity>
                  ))}
                  {MENU_NAV_ITEMS.map((item) => (
                    <TouchableOpacity
                      key={item.label}
                      style={styles.menuFooterItem}
                      onPress={() => {
                        setMenuVisible(false);
                        navigation.navigate(item.screen);
                      }}
                    >
                      <Text style={styles.menuFooterItemText}>{item.label}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </ScrollView>
            </LinearGradient>
          </View>
        </Modal>
      </SafeAreaView>
    </LinearGradient>
  );
}

function NavItem({ Icon, label, onPress, active }) {
  return (
    <TouchableOpacity style={styles.navItem} onPress={onPress}>
      <Icon size={22} color={active ? COLORS.primary : COLORS.inkMuted48} strokeWidth={active ? 2 : 1.6} />
      <Text style={[styles.navLabel, active && { color: COLORS.primary, fontWeight: '600' }]}>{label}</Text>
    </TouchableOpacity>
  );
}

