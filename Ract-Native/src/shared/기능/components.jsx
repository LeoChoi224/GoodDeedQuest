// components.jsx — 선행퀘스트 RN 공통 컴포넌트 (네비게이션/햄버거 메뉴/지도/애니메이션)
// 디자인 토큰은 ../디자인/tokens, 스타일은 ../디자인/components.styles에서 가져옵니다.
//
// 설치 필요: expo-linear-gradient, lucide-react-native, react-native-svg
//   npx expo install expo-linear-gradient
//   npm i lucide-react-native react-native-svg

import React, { useRef, useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView, Modal, Pressable, Animated, Easing, LayoutAnimation, Platform, UIManager } from 'react-native';
import { Users, MapPin, Home, Coins, User, ChevronRight, X } from 'lucide-react-native';
import Svg, { Path } from 'react-native-svg';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS, GREEN_GRADIENT, GREEN_GRADIENT_LOCATIONS } from '../디자인/tokens';
import { styles } from '../디자인/components.styles';

if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

// 홈/지도/대항전 계열(연두 그라디언트 배경) 화면에 씀. plain 리스트/폼 화면(상점/커뮤니티/마이/관리자)은
// 이 래퍼 없이 COLORS.canvas 배경을 그대로 쓰면 됨.
export function GreenGradientBG({ children, style }) {
  return (
    <LinearGradient colors={GREEN_GRADIENT} locations={GREEN_GRADIENT_LOCATIONS} style={[{ flex: 1 }, style]}>
      {children}
    </LinearGradient>
  );
}

export function CareIcon({ size = 18, color = '#fff' }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round">
      <Path d="M12 6.8c-.9-1.6-3-1.8-4.1-.4-.9 1.1-.7 2.7.4 3.7L12 13l3.7-2.9c1.1-1 1.3-2.6.4-3.7-1.1-1.4-3.2-1.2-4.1.4Z" />
      <Path d="M4.3 13.2c0 3.2 2.9 5.9 6.4 6.3" />
      <Path d="M19.7 13.2c0 3.2-2.9 5.9-6.4 6.3" />
    </Svg>
  );
}

// 별 모양 스파클 — opacity/scale/rotate 삼각파 반복 (게이미피케이션 화면 전용: 퀘스트 상세/인증 계열)
export function Sparkle({ size = 10, color = COLORS.gold, style, duration = 1600, delay = 0 }) {
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

function BottomNavItem({ Icon, label, onPress, active }) {
  return (
    <TouchableOpacity style={styles.navItem} onPress={onPress}>
      <Icon size={22} color={active ? COLORS.primary : COLORS.inkMuted48} strokeWidth={active ? 2 : 1.6} />
      <Text style={[styles.navLabel, active && { color: COLORS.primary, fontWeight: '600' }]}>{label}</Text>
    </TouchableOpacity>
  );
}

// 하단 탭바 5탭 고정 (커뮤니티/지도/홈/상점/마이). active: 'community'|'map'|'home'|'store'|'mypage'
export function BottomNav({ navigation, active, translucent }) {
  return (
    <View style={[styles.bottomNav, translucent && { backgroundColor: 'rgba(255,255,255,0.7)' }]}>
      <BottomNavItem Icon={Users} label="커뮤니티" active={active === 'community'} onPress={() => navigation.navigate('Community')} />
      <BottomNavItem Icon={MapPin} label="지도" active={active === 'map'} onPress={() => navigation.navigate('MapMain')} />
      <BottomNavItem Icon={Home} label="홈" active={active === 'home'} onPress={() => navigation.navigate('Main')} />
      <BottomNavItem Icon={Coins} label="상점" active={active === 'store'} onPress={() => navigation.navigate('Store')} />
      <BottomNavItem Icon={User} label="마이" active={active === 'mypage'} onPress={() => navigation.navigate('MyPage')} />
    </View>
  );
}

// 대카테고리(하단 5탭 기준) → 하위 화면. 실제 구현된 화면만 route가 있고, 없으면 Placeholder로 이동.
export const NAV_SECTIONS = [
  { title: '홈', items: [{ label: '메인', screen: 'Main' }, { label: '퀘스트 상세', screen: 'QuestDetail' }, { label: '커스텀 퀘스트 등록', screen: 'QuestRegister' }] },
  { title: '지도', items: [{ label: '지도 메인', screen: 'MapMain' }, { label: '내 주변', screen: 'Nearby' }, { label: '봉사센터 상세', screen: 'CenterDetail' }, { label: '지역 검색', screen: 'RegionSearch' }, { label: '대항전', screen: 'Competition' }, { label: '시군구 랭킹', screen: 'DistrictRanking' }] },
  { title: '상점', items: [{ label: '상점', screen: 'Store' }, { label: '아이템 상세', screen: 'ItemDetail' }, { label: '구매 목록', screen: 'PurchaseList' }] },
  { title: '커뮤니티', items: [{ label: '커뮤니티 메인', screen: 'Community' }, { label: '팀 챌린지', screen: 'TeamChallenge' }, { label: '방 찾기', screen: 'RoomFind' }, { label: '방 만들기', screen: 'RoomCreate' }, { label: '팀 상세', screen: 'TeamDetail' }, { label: '유저 추천', screen: 'UserRecommend' }, { label: '팀 목록', screen: 'TeamList' }, { label: '유저 상세정보', screen: 'UserDetail' }, { label: '숏폼 제작', screen: 'ShortFormCreate' }] },
  { title: '마이페이지', items: [{ label: '마이페이지', screen: 'MyPage' }, { label: '마이 레벨', screen: 'MyLevel' }, { label: '내 랭킹', screen: 'MyRanking' }] },
];

export const MENU_LABELS = ['공지사항', '설정', '이용약관', '로그아웃'];

// 햄버거 메뉴 맨 아래 — 실제 화면으로 이동하는 항목(관리자/로그인)
export const MENU_NAV_ITEMS = [
  { label: '관리자 페이지', screen: 'AdminDashboard' },
  { label: '로그인 페이지', screen: 'Login' },
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
              onPress={() => (item.screen ? navigation.navigate(item.screen) : navigation.navigate('Placeholder', { title: item.label }))}
            >
              <Text style={styles.menuItemRowText}>{item.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
}

// 우측 슬라이드 햄버거 메뉴 — 모든 화면 공통. <HamburgerMenu visible={..} onClose={..} navigation={navigation} />
export function HamburgerMenu({ visible, onClose, navigation }) {
  const [expandedSection, setExpandedSection] = useState(null);

  const toggleSection = (title) => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpandedSection((prev) => (prev === title ? null : title));
  };

  return (
    <Modal statusBarTranslucent visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.menuOverlayRow}>
        <Pressable style={{ flex: 1 }} onPress={onClose} />
        <LinearGradient colors={['#033236', '#063e42', '#04484d']} locations={[0, 0.55, 1]} style={styles.menuPanel}>
          <ScrollView showsVerticalScrollIndicator={false}>
            <View style={styles.menuHeader}>
              <View style={styles.menuLogoBadge}>
                <CareIcon size={16} color={COLORS.mint} />
              </View>
              <Text style={styles.menuLogoText}>선행퀘스트</Text>
              <View style={{ flex: 1 }} />
              <TouchableOpacity onPress={onClose} hitSlop={10}>
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
                    onClose();
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
  );
}

// 헤더 오른쪽 3줄 햄버거 아이콘 버튼
export function HamburgerButton({ onPress }) {
  return (
    <TouchableOpacity onPress={onPress} hitSlop={10} style={{ padding: 10 }}>
      <View style={{ gap: 5 }}>
        <View style={styles.burgerLine} />
        <View style={styles.burgerLine} />
        <View style={styles.burgerLine} />
      </View>
    </TouchableOpacity>
  );
}

// 대한민국 8도 지도(간이 SVG) — 지도메인(17)/대항전메인(22)에서 공용으로 사용.
export const KOREA_REGIONS = [
  { id: 'gg', name: '수도권', path: 'M118,140 L88,145 L72,155 L55,168 L45,180 L55,190 L70,182 L84,175 L96,214 L128,205 L155,200 L185,195 L213,200 L210,138 L180,100 L150,110 Z', labelXPct: 18, labelYPct: 27 },
  { id: 'gw', name: '강원', path: 'M215,100 L240,72 L268,54 L300,50 L330,58 L344,88 L350,128 L354,168 L349,208 L344,248 L333,278 L300,289 L268,268 L248,238 L238,198 L224,168 L210,138 Z', labelXPct: 52, labelYPct: 25 },
  { id: 'cc', name: '충청', path: 'M128,205 L155,200 L185,195 L213,200 L238,198 L250,235 L265,265 L248,292 L222,296 L200,282 L188,300 L165,310 L143,330 L120,315 L98,300 L78,285 L58,262 L48,248 L64,232 L76,224 L96,214 Z', labelXPct: 29, labelYPct: 38 },
  { id: 'gb', name: '경북', path: 'M298,285 L330,275 L345,245 L358,290 L368,335 L372,380 L358,415 L332,432 L305,420 L282,400 L268,372 L252,340 L228,295 L255,288 Z', labelXPct: 56, labelYPct: 52 },
  { id: 'jb', name: '전북', path: 'M165,310 L190,300 L205,280 L230,295 L252,340 L235,362 L212,378 L188,383 L162,372 L148,352 L143,330 Z', labelXPct: 35, labelYPct: 52 },
  { id: 'gn', name: '경남', path: 'M268,372 L282,400 L305,420 L332,432 L358,415 L372,380 L378,415 L365,445 L345,462 L322,470 L298,460 L275,450 L252,438 L232,420 L212,405 L235,362 L252,340 Z', labelXPct: 54, labelYPct: 63 },
  { id: 'jn', name: '전남', path: 'M143,330 L148,352 L162,372 L188,383 L212,378 L235,362 L212,405 L232,420 L212,435 L188,450 L162,462 L135,470 L108,458 L88,440 L78,415 L85,392 L100,372 L120,350 Z', labelXPct: 29, labelYPct: 63 },
  { id: 'jj', name: '제주', path: 'M150,600 L165,585 L190,580 L220,582 L245,590 L255,605 L245,618 L215,625 L185,623 L160,615 Z', labelXPct: 36, labelYPct: 92 },
];

export const KOREA_ISLANDS = [
  'M95,478 L108,472 L118,480 L110,490 L96,488 Z',
  'M70,450 L82,445 L88,455 L76,462 Z',
  'M55,420 L66,415 L70,425 L58,430 Z',
  'M130,485 L145,480 L150,492 L135,496 Z',
  'M45,395 L58,392 L60,402 L48,405 Z',
  'M45,195 L56,190 L60,200 L48,205 Z',
  'M35,175 L46,170 L50,180 L38,183 Z',
];

// regionStyles: { [id]: { fill, labelColor } } — 나머지는 기본값(#E3F5E7 / #033236)
export function KoreaMap({ size = 230, regionStyles = {}, onPressRegion }) {
  return (
    <View style={{ width: size, aspectRatio: 555 / 650, alignSelf: 'center' }}>
      <Svg viewBox="0 0 555 650" style={{ position: 'absolute', width: '100%', height: '100%' }}>
        {KOREA_REGIONS.map((r) => {
          const st = regionStyles[r.id] || {};
          return (
            <Path
              key={r.id}
              d={r.path}
              fill={st.fill || '#E3F5E7'}
              stroke="#FFFFFF"
              strokeWidth={2.5}
              strokeLinejoin="round"
              onPress={onPressRegion ? () => onPressRegion(r.id) : undefined}
            />
          );
        })}
        {KOREA_ISLANDS.map((d, i) => (
          <Path key={i} d={d} fill="#E3F5E7" stroke="#FFFFFF" strokeWidth={1.5} strokeLinejoin="round" />
        ))}
      </Svg>
      {KOREA_REGIONS.map((r) => {
        const st = regionStyles[r.id] || {};
        return (
          <Text
            key={r.id}
            style={{
              position: 'absolute',
              left: `${r.labelXPct}%`,
              top: `${r.labelYPct}%`,
              transform: [{ translateX: -14 }, { translateY: -7 }],
              fontSize: 11,
              fontWeight: '700',
              color: st.labelColor || COLORS.primary,
              width: 40,
              textAlign: 'center',
            }}
          >
            {r.name}
          </Text>
        );
      })}
    </View>
  );
}
