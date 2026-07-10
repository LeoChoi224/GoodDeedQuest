// 21-RegionSearch.js — React Native (Expo) 원하는 지역 검색페이지
// 선행퀘스트 / 스토리보드 21번 기준

import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, Search, X, MapPin, ChevronRight } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { CareIcon, GreenGradientBG, BottomNav, HamburgerMenu, HamburgerButton } from '../../../shared/기능/components';
import { styles } from '../디자인/RegionSearch.styles';

const PLACES = [
  { id: 'p1', name: '행복나눔 복지관', address: '서울 중구 행복로 12', desc: '노인 및 취약계층 지원 봉사를 상시 모집하고 있어요.' },
  { id: 'p2', name: '사랑동물보호센터', address: '서울 서구 사랑길 8', desc: '유기동물 보호 및 산책 봉사를 진행합니다.' },
  { id: 'p3', name: '푸른급식소', address: '서울 남구 나눔길 3', desc: '무료 급식 준비와 배식을 돕는 봉사입니다.' },
  { id: 'p4', name: '초록환경센터', address: '경기 수원시 초록로 20', desc: '지역 환경 정화 캠페인을 운영해요.' },
  { id: 'p5', name: '한마음 아동센터', address: '부산 해운대구 한마음로 5', desc: '지역 아동 학습 멘토링 봉사자를 찾고 있어요.' },
  { id: 'p6', name: '늘봄 요양원', address: '대구 수성구 늘봄길 44', desc: '어르신 말벗 및 생활 지원 봉사를 진행합니다.' },
  { id: 'p7', name: '해맑은 지역아동센터', address: '광주 서구 해맑은로 9', desc: '방과후 아이들과 함께하는 놀이 봉사예요.' },
];

export default function RegionSearchScreen({ navigation }) {
  const [menuVisible, setMenuVisible] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedId, setSelectedId] = useState(null);

  const q = query.trim();
  const filtered = q ? PLACES.filter((p) => p.name.includes(q) || p.address.includes(q)) : PLACES;
  const selected = selectedId ? PLACES.find((p) => p.id === selectedId) : null;

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate('MapMain')} hitSlop={10} style={{ padding: 4 }}>
            <ChevronLeft size={22} color={COLORS.ink} />
          </TouchableOpacity>
          <View style={styles.logoBadge}>
            <CareIcon size={18} />
          </View>
          <Text style={styles.logo}>선·퀘</Text>
          <View style={{ flex: 1 }} />
          <HamburgerButton onPress={() => setMenuVisible(true)} />
        </View>

        <View style={styles.searchBar}>
          <Search size={18} color={COLORS.inkMuted48} />
          <TextInput
            style={styles.searchInput}
            placeholder="지역명, 주소를 입력해보세요 (예: 강남구)"
            placeholderTextColor={COLORS.inkMuted48}
            value={query}
            onChangeText={setQuery}
          />
          {!!query && (
            <TouchableOpacity onPress={() => setQuery('')} hitSlop={6}>
              <X size={16} color={COLORS.inkMuted48} />
            </TouchableOpacity>
          )}
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <Text style={styles.resultCount}>{q ? `검색 결과 ${filtered.length}건` : `전체 장소 ${filtered.length}건`}</Text>
          {filtered.map((p) => (
            <TouchableOpacity key={p.id} style={styles.resultRow} onPress={() => setSelectedId(p.id)}>
              <View style={styles.resultIcon}>
                <MapPin size={17} color="#fff" />
              </View>
              <View style={{ flex: 1, minWidth: 0, gap: 2 }}>
                <Text style={styles.resultName}>{p.name}</Text>
                <Text style={styles.resultAddress}>{p.address}</Text>
              </View>
              <ChevronRight size={16} color={COLORS.inkMuted48} />
            </TouchableOpacity>
          ))}
          {filtered.length === 0 && (
            <View style={{ paddingVertical: 40, alignItems: 'center' }}>
              <Text style={{ fontSize: 14, color: COLORS.inkMuted48 }}>검색 결과가 없어요</Text>
            </View>
          )}
        </ScrollView>

        <BottomNav navigation={navigation} active="map" translucent />
        <HamburgerMenu visible={menuVisible} onClose={() => setMenuVisible(false)} navigation={navigation} />

        {selected && (
          <View style={styles.selectedCard}>
            <View style={{ flexDirection: 'row', alignItems: 'flex-start', gap: 12 }}>
              <View style={styles.resultIcon}>
                <MapPin size={19} color="#fff" />
              </View>
              <View style={{ flex: 1, minWidth: 0, gap: 2 }}>
                <Text style={styles.resultName}>{selected.name}</Text>
                <Text style={styles.resultAddress}>{selected.address}</Text>
              </View>
              <TouchableOpacity onPress={() => setSelectedId(null)} hitSlop={8}>
                <X size={18} color={COLORS.inkMuted48} />
              </TouchableOpacity>
            </View>
            <Text style={[styles.resultAddress, { color: COLORS.ink, marginTop: 10, paddingLeft: 52, lineHeight: 19 }]}>{selected.desc}</Text>
            <TouchableOpacity style={styles.aroundButton} onPress={() => navigation.navigate('Nearby')}>
              <Text style={styles.aroundButtonText}>내 주변에서 보기</Text>
            </TouchableOpacity>
          </View>
        )}
      </SafeAreaView>
    </GreenGradientBG>
  );
}

