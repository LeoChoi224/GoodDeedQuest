// 24-Store.js — React Native (Expo) 상점 페이지
// 선행퀘스트 / 스토리보드 24번 기준

import React, { useState, useRef } from 'react';
import { View, Text, TouchableOpacity, ScrollView, Animated } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Coins } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { CareIcon, GreenGradientBG, BottomNav, HamburgerMenu, HamburgerButton } from '../../../shared/기능/components';
import { styles } from '../디자인/Store.styles';

export const ITEMS = [
  { id: 'i1', name: '골드 프로필 테두리', desc: '내 프로필 사진에 반짝이는 골드 테두리 적용', price: 300, iconBg: '#FDF6E3', emoji: '🖼️' },
  { id: 'i2', name: '나눔이 스티커팩', desc: '커뮤니티 게시글에 쓸 수 있는 스티커 12종', price: 150, iconBg: '#F6F6F6', emoji: '✨' },
  { id: 'i3', name: '랭킹 강조 카드', desc: '시군구 랭킹에서 내 순위 카드 하이라이트', price: 250, iconBg: '#F6F6F6', emoji: '🏷️' },
  { id: 'i4', name: '선행왕 칭호', desc: '프로필에 표시되는 특별 칭호 "선행왕"', price: 400, iconBg: '#FDF6E3', emoji: '👑' },
  { id: 'i5', name: '다크모드 테마', desc: '앱 전체에 어두운 테마 적용', price: 200, iconBg: '#F6F6F6', emoji: '🌙' },
];

export default function StoreScreen({ navigation }) {
  const [menuVisible, setMenuVisible] = useState(false);
  const [myPoint, setMyPoint] = useState(480);
  const [showToast, setShowToast] = useState(false);
  const toastTimer = useRef(null);
  const pulse = useRef(new Animated.Value(1)).current;

  const onBuy = (item) => {
    clearTimeout(toastTimer.current);
    setMyPoint((p) => Math.max(0, p - item.price));
    setShowToast(true);
    Animated.sequence([
      Animated.timing(pulse, { toValue: 1.14, duration: 160, useNativeDriver: true }),
      Animated.timing(pulse, { toValue: 1, duration: 200, useNativeDriver: true }),
    ]).start();
    toastTimer.current = setTimeout(() => setShowToast(false), 2200);
  };

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

        <View style={styles.titleRow}>
          <View style={{ flex: 1 }}>
            <Text style={styles.title}>상점 페이지</Text>
            <Text style={styles.subtitle}>포인트를 모아 아이템을 구매하세요</Text>
          </View>
          <Animated.View style={[styles.pointPill, { transform: [{ scale: pulse }] }]}>
            <Coins size={14} color={COLORS.gold} />
            <Text style={styles.pointPillText}>{myPoint}P</Text>
          </Animated.View>
        </View>
        <View style={{ paddingHorizontal: 20, paddingBottom: 12, alignItems: 'flex-end' }}>
          <TouchableOpacity style={styles.purchaseListButton} onPress={() => navigation.navigate('PurchaseList')}>
            <Text style={styles.purchaseListButtonText}>구매 목록</Text>
          </TouchableOpacity>
        </View>

        <ScrollView contentContainerStyle={styles.list}>
          {ITEMS.map((item) => (
            <View key={item.id} style={styles.itemRow}>
              <View style={[styles.itemIcon, { backgroundColor: item.iconBg }]}>
                <Text style={{ fontSize: 26 }}>{item.emoji}</Text>
              </View>
              <View style={{ flex: 1, minWidth: 0, gap: 3 }}>
                <Text style={styles.itemName}>{item.name}</Text>
                <Text style={styles.itemDesc} numberOfLines={1}>
                  {item.desc}
                </Text>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 3, marginTop: 2 }}>
                  <Coins size={12} color={COLORS.gold} />
                  <Text style={styles.itemPrice}>{item.price}P</Text>
                </View>
              </View>
              <View style={{ gap: 6 }}>
                <TouchableOpacity style={styles.buyButton} onPress={() => onBuy(item)}>
                  <Text style={styles.buyButtonText}>구매</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.detailButton} onPress={() => navigation.navigate('ItemDetail', { itemId: item.id })}>
                  <Text style={styles.detailButtonText}>상세보기</Text>
                </TouchableOpacity>
              </View>
            </View>
          ))}
        </ScrollView>

        <BottomNav navigation={navigation} active="store" />
        <HamburgerMenu visible={menuVisible} onClose={() => setMenuVisible(false)} navigation={navigation} />

        {showToast && (
          <View style={styles.toast}>
            <Text style={styles.toastText}>아이템을 구매했습니다</Text>
          </View>
        )}
      </SafeAreaView>
    </GreenGradientBG>
  );
}

