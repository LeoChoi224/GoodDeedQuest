// 17-MapMain.js — React Native (Expo) 지도 메인페이지
// 선행퀘스트 / 스토리보드 17번 기준
// 전국 지도(도별), 전국 TOP3, 대항전 바로가기, 내 주변/지역검색 진입점

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView, Modal, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronRight, MapPin, X } from 'lucide-react-native';

import { COLORS, RANK_BADGE_COLOR } from '../../../shared/디자인/tokens';
import { CareIcon, GreenGradientBG, BottomNav, HamburgerMenu, HamburgerButton, KoreaMap } from '../../../shared/기능/components';
import { styles } from '../디자인/MapMain.styles';

const REGIONS_DATA = {
  gg: { name: '수도권', top: [{ name: '김선행', dong: '강남구', score: 2840 }, { name: '이나눔', dong: '수원시', score: 2510 }, { name: '박봉사', dong: '성남시', score: 2290 }] },
  gw: { name: '강원', top: [{ name: '최정하', dong: '춘천시', score: 1980 }, { name: '윤바다', dong: '강릉시', score: 1720 }, { name: '한소원', dong: '원주시', score: 1540 }] },
  cc: { name: '충청', top: [{ name: '서지안', dong: '대전 서구', score: 2140 }, { name: '문하늘', dong: '청주시', score: 1890 }, { name: '배준서', dong: '천안시', score: 1650 }] },
  gb: { name: '경북', top: [{ name: '황도윤', dong: '포항시', score: 1870 }, { name: '남기쁨', dong: '경주시', score: 1610 }, { name: '류상현', dong: '구미시', score: 1420 }] },
  jb: { name: '전북', top: [{ name: '오은비', dong: '전주시', score: 1760 }, { name: '조민재', dong: '군산시', score: 1530 }, { name: '백서연', dong: '익산시', score: 1310 }] },
  gn: { name: '경남', top: [{ name: '강태민', dong: '창원시', score: 2050 }, { name: '임소율', dong: '김해시', score: 1780 }, { name: '송재현', dong: '진주시', score: 1490 }] },
  jn: { name: '전남', top: [{ name: '노유진', dong: '여수시', score: 1690 }, { name: '권도현', dong: '순천시', score: 1450 }, { name: '홍아름', dong: '목포시', score: 1260 }] },
  jj: { name: '제주', top: [{ name: '정하윤', dong: '제주시', score: 1580 }, { name: '신유나', dong: '서귀포시', score: 1340 }, { name: '유건우', dong: '애월읍', score: 1120 }] },
};

export default function MapMainScreen({ navigation }) {
  const [menuVisible, setMenuVisible] = useState(false);
  const [selectedRegionId, setSelectedRegionId] = useState(null);

  const rankedRegions = Object.entries(REGIONS_DATA)
    .map(([id, r]) => ({ id, name: r.name, total: r.top.reduce((s, p) => s + p.score, 0) }))
    .sort((a, b) => b.total - a.total);

  const selectedRegion = selectedRegionId ? REGIONS_DATA[selectedRegionId] : null;
  const regionStyles = {};
  if (selectedRegionId) regionStyles[selectedRegionId] = { fill: COLORS.primary, labelColor: '#FFFFFF' };

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <View style={styles.logoBadge}>
            <CareIcon size={18} />
          </View>
          <Text style={styles.logo}>선·퀘</Text>
          <View style={{ flex: 1 }} />
          <HamburgerButton onPress={() => setMenuVisible(true)} />
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.currentRegionRow}>
            <MapPin size={18} color={COLORS.primary} />
            <Text style={styles.currentRegionText}>서울특별시 강남구</Text>
          </View>

          <View style={styles.topCard}>
            <Text style={styles.topCardHeader}>전국 TOP 3 지역</Text>
            {rankedRegions.slice(0, 3).map((r, i) => (
              <View key={r.id} style={styles.topRow}>
                <View style={[styles.rankBadge, { backgroundColor: RANK_BADGE_COLOR[i + 1] }]}>
                  <Text style={styles.rankBadgeText}>{i + 1}</Text>
                </View>
                <Text style={styles.topRowName} numberOfLines={1}>
                  {r.name}
                </Text>
                <Text style={styles.topRowScore}>{r.total.toLocaleString()}P</Text>
              </View>
            ))}
          </View>

          <KoreaMap regionStyles={regionStyles} onPressRegion={(id) => setSelectedRegionId(id)} />

          <TouchableOpacity style={styles.competitionLink} onPress={() => navigation.navigate('Competition')}>
            <Text style={styles.competitionLinkText}>대항전 바로가기</Text>
            <ChevronRight size={12} color={COLORS.inkMuted48} />
          </TouchableOpacity>

          <View style={{ flex: 1, minHeight: 12 }} />

          <View style={{ gap: 10 }}>
            <TouchableOpacity style={styles.actionButton} onPress={() => navigation.navigate('Nearby')}>
              <Text style={styles.actionButtonText}>내 주변 둘러보기</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.actionButton} onPress={() => navigation.navigate('RegionSearch')}>
              <Text style={styles.actionButtonText}>원하는 장소 검색하기</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>

        <BottomNav navigation={navigation} active="map" translucent />
        <HamburgerMenu visible={menuVisible} onClose={() => setMenuVisible(false)} navigation={navigation} />

        {/* 도별 TOP3 팝업 */}
        <Modal statusBarTranslucent visible={!!selectedRegion} transparent animationType="slide" onRequestClose={() => setSelectedRegionId(null)}>
          <View style={styles.sheetOverlay}>
            <Pressable style={{ flex: 1 }} onPress={() => setSelectedRegionId(null)} />
            {selectedRegion && (
              <View style={styles.sheet}>
                <View style={styles.sheetHandle} />
                <View style={styles.sheetHeaderRow}>
                  <Text style={styles.sheetTitle}>{selectedRegion.name} TOP 3</Text>
                  <TouchableOpacity onPress={() => setSelectedRegionId(null)} hitSlop={8}>
                    <X size={18} color={COLORS.inkMuted48} />
                  </TouchableOpacity>
                </View>
                <View style={{ gap: 8 }}>
                  {selectedRegion.top.map((p, i) => (
                    <View key={i} style={styles.sheetRow}>
                      <View style={[styles.rankBadge, { width: 28, height: 28, backgroundColor: RANK_BADGE_COLOR[i + 1] }]}>
                        <Text style={styles.rankBadgeText}>{i + 1}</Text>
                      </View>
                      <View style={{ flex: 1, minWidth: 0 }}>
                        <Text style={styles.sheetRowName}>{p.name}</Text>
                        <Text style={styles.sheetRowDong}>{p.dong}</Text>
                      </View>
                      <Text style={styles.sheetRowScore}>{p.score.toLocaleString()}P</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}
          </View>
        </Modal>
      </SafeAreaView>
    </GreenGradientBG>
  );
}

