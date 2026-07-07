// 23-DistrictRanking.js — React Native (Expo) 시군구 랭킹
// 선행퀘스트 / 스토리보드 23번 기준 — 대항전 메인에서 시·도 선택 시 진입, region 파라미터로 표시

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, Trophy } from 'lucide-react-native';

import { COLORS, RANK_BADGE_COLOR } from '../../../shared/디자인/tokens';
import { CareIcon, GreenGradientBG, BottomNav, HamburgerMenu, HamburgerButton } from '../../../shared/기능/components';
import { styles } from '../디자인/DistrictRanking.styles';

const DISTRICTS = {
  gg: { name: '수도권', myDistrict: '수원시', list: ['수원시', '성남시', '고양시', '용인시', '부천시', '화성시', '안산시', '안양시', '평택시', '시흥시'] },
  gw: { name: '강원', myDistrict: '춘천시', list: ['춘천시', '원주시', '강릉시', '동해시', '속초시', '삼척시', '태백시', '홍천군', '횡성군', '영월군'] },
  cc: { name: '충청', myDistrict: '천안시', list: ['천안시', '청주시', '대전시', '세종시', '아산시', '서산시', '공주시', '논산시', '당진시', '제천시'] },
  gb: { name: '경북', myDistrict: '포항시', list: ['포항시', '구미시', '경주시', '안동시', '김천시', '영주시', '영천시', '경산시', '상주시', '문경시'] },
  jb: { name: '전북', myDistrict: '전주시', list: ['전주시', '군산시', '익산시', '정읍시', '남원시', '김제시', '완주군', '고창군', '부안군', '임실군'] },
  gn: { name: '경남', myDistrict: '창원시', list: ['창원시', '김해시', '진주시', '양산시', '거제시', '통영시', '사천시', '밀양시', '함안군', '거창군'] },
  jn: { name: '전남', myDistrict: '여수시', list: ['여수시', '순천시', '목포시', '광양시', '나주시', '담양군', '고흥군', '보성군', '화순군', '해남군'] },
  jj: { name: '제주', myDistrict: '제주시', list: ['제주시', '서귀포시'] },
};
const FACILITY_TEMPLATES = [
  { suffix: '행복나눔 복지관', desc: '노인 및 취약계층 지원 봉사를 상시 모집하고 있어요.' },
  { suffix: '동물보호센터', desc: '유기동물 보호 및 산책 봉사를 진행합니다.' },
];

function seedNum(seed) {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) >>> 0;
  return h;
}
function seedScore(seed) { return 1200 + (seedNum(seed) % 4200); }

export default function DistrictRankingScreen({ navigation, route }) {
  const regionId = route?.params?.regionId || 'gg';
  const data = DISTRICTS[regionId] || DISTRICTS.gg;
  const [menuVisible, setMenuVisible] = useState(false);
  const [selectedName, setSelectedName] = useState(data.myDistrict);

  const ranked = data.list.map((name) => ({ name, score: seedScore(regionId + name) })).sort((a, b) => b.score - a.score);
  const selectedRow = ranked.find((d) => d.name === selectedName);
  const selected = selectedRow
    ? {
        name: selectedRow.name,
        myRankText: '#' + (1 + (seedNum(regionId + selectedRow.name + 'me') % 480)),
        myScoreText: (40 + (seedNum(regionId + selectedRow.name + 'mescore') % 260)) + 'P 획득',
        facilities: FACILITY_TEMPLATES.map((t) => ({ name: selectedRow.name + ' ' + t.suffix, address: data.name + ' ' + selectedRow.name, desc: t.desc })),
      }
    : null;

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate('Competition')} hitSlop={10} style={{ padding: 4 }}>
            <ChevronLeft size={22} color={COLORS.ink} />
          </TouchableOpacity>
          <View style={styles.logoBadge}>
            <CareIcon size={18} />
          </View>
          <Text style={styles.logo}>선·퀘</Text>
          <View style={{ flex: 1 }} />
          <HamburgerButton onPress={() => setMenuVisible(true)} />
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <View>
            <Text style={styles.title}>{data.name} 시·군·구 랭킹</Text>
            <Text style={styles.subtitle}>지역을 선택하면 추천 봉사시설을 볼 수 있어요</Text>
          </View>

          <View style={{ gap: 8 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <Trophy size={15} color={COLORS.gold} />
              <Text style={styles.listHeader}>시군구별 XP 랭킹</Text>
            </View>
            {ranked.map((r, i) => {
              const rank = i + 1;
              const isMine = r.name === data.myDistrict;
              const isSelected = r.name === selectedName;
              return (
                <TouchableOpacity
                  key={r.name}
                  style={[
                    styles.rankRow,
                    { backgroundColor: isMine ? COLORS.goldTint : COLORS.parchment, borderColor: isSelected ? COLORS.primary : isMine ? 'rgba(201,162,39,0.35)' : 'transparent' },
                  ]}
                  onPress={() => setSelectedName(r.name)}
                >
                  <View style={[styles.rankBadge, { backgroundColor: RANK_BADGE_COLOR[rank] || '#E5E5E5' }]}>
                    <Text style={[styles.rankBadgeText, { color: rank <= 3 ? '#fff' : COLORS.inkMuted48 }]}>{rank}</Text>
                  </View>
                  <View style={{ flex: 1, flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                    <Text style={styles.rankName}>{r.name}</Text>
                    {isMine && (
                      <View style={styles.mineTag}>
                        <Text style={styles.mineTagText}>내 지역</Text>
                      </View>
                    )}
                  </View>
                  <Text style={styles.rankScore}>{r.score.toLocaleString()}P</Text>
                </TouchableOpacity>
              );
            })}
          </View>

          <View style={styles.tileCard}>
            <Text style={styles.listHeader}>시군구 지도</Text>
            <View style={styles.tileGrid}>
              {ranked.map((r, i) => {
                const rank = i + 1;
                const isSelected = r.name === selectedName;
                const bg = isSelected ? COLORS.primary : rank <= 3 ? COLORS.goldTint : COLORS.parchment;
                const color = isSelected ? '#fff' : rank <= 3 ? COLORS.gold : COLORS.ink;
                return (
                  <TouchableOpacity key={r.name} style={[styles.tile, { backgroundColor: bg, borderColor: isSelected ? COLORS.primary : 'rgba(0,0,0,0.06)' }]} onPress={() => setSelectedName(r.name)}>
                    <Text style={[styles.tileName, { color }]}>{r.name}</Text>
                    <Text style={[styles.tileRank, { color }]}>{rank}위</Text>
                  </TouchableOpacity>
                );
              })}
            </View>
            <Text style={styles.mapHint}>지역을 눌러 개인 랭킹과 추천 봉사시설을 확인해보세요</Text>
          </View>

          {selected && (
            <View style={styles.myRow}>
              <View style={styles.myBadge}>
                <Text style={styles.myBadgeText}>{selected.myRankText}</Text>
              </View>
              <View style={{ flex: 1, minWidth: 0 }}>
                <Text style={styles.myLabel}>{selected.name} 내 개인 랭킹</Text>
                <Text style={styles.myScore}>{selected.myScoreText}</Text>
              </View>
            </View>
          )}

          {selected && (
            <View style={{ gap: 10 }}>
              <Text style={styles.listHeader}>{selected.name} 추천 봉사시설</Text>
              {selected.facilities.map((f, i) => (
                <View key={i} style={styles.facilityCard}>
                  <View style={styles.facilityIcon}>
                    <Text style={{ color: '#fff', fontSize: 15 }}>⌂</Text>
                  </View>
                  <View style={{ flex: 1, minWidth: 0, gap: 3 }}>
                    <Text style={styles.facilityName}>{f.name}</Text>
                    <Text style={styles.facilityAddress}>{f.address}</Text>
                    <Text style={styles.facilityDesc}>{f.desc}</Text>
                  </View>
                </View>
              ))}
            </View>
          )}
        </ScrollView>

        <BottomNav navigation={navigation} active="map" translucent />
        <HamburgerMenu visible={menuVisible} onClose={() => setMenuVisible(false)} navigation={navigation} />
      </SafeAreaView>
    </GreenGradientBG>
  );
}

