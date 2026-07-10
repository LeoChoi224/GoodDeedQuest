// 25-ItemDetail.js — React Native (Expo) 아이템 상세 페이지 (+ 구매확인 팝업 내장)
// 선행퀘스트 / 스토리보드 25·26번 기준 (26번 구매확인 팝업은 이 화면 내 모달로 통합)

import React, { useState, useRef } from 'react';
import { View, Text, TouchableOpacity, ScrollView, Modal, Pressable, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, Coins } from 'lucide-react-native';
import { ITEMS } from '../../24-Store/기능/Store';

import { COLORS } from '../../../shared/디자인/tokens';
import { CareIcon, GreenGradientBG, BottomNav, HamburgerMenu, HamburgerButton } from '../../../shared/기능/components';
import { styles } from '../디자인/ItemDetail.styles';

export default function ItemDetailScreen({ navigation, route }) {
  const itemId = route?.params?.itemId || 'i1';
  const item = ITEMS.find((i) => i.id === itemId) || ITEMS[0];
  const [menuVisible, setMenuVisible] = useState(false);
  const [confirmVisible, setConfirmVisible] = useState(false);
  const [myPoint, setMyPoint] = useState(480);
  const [showToast, setShowToast] = useState(false);
  const navTimer = useRef(null);

  const onConfirmBuy = () => {
    setMyPoint((p) => Math.max(0, p - item.price));
    setConfirmVisible(false);
    setShowToast(true);
    navTimer.current = setTimeout(() => navigation.navigate('PurchaseList'), 1100);
  };

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate('Store')} hitSlop={10} style={{ padding: 4 }}>
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
          <View style={[styles.imageBox, { backgroundColor: item.iconBg }]}>
            <Text style={{ fontSize: 64 }}>{item.emoji}</Text>
          </View>

          <View style={styles.infoCard}>
            <Text style={styles.itemName}>{item.name}</Text>
            <Text style={styles.itemDesc}>{item.desc}</Text>
            <View style={styles.divider} />
            <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
              <Text style={styles.priceLabel}>가격</Text>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                <Coins size={15} color={COLORS.gold} />
                <Text style={styles.priceValue}>{item.price}P</Text>
              </View>
            </View>
          </View>

          <View style={styles.myPointRow}>
            <Text style={styles.myPointLabel}>보유 포인트</Text>
            <Text style={styles.myPointValue}>{myPoint}P</Text>
          </View>
        </ScrollView>

        <View style={styles.footer}>
          <TouchableOpacity style={styles.buyButton} onPress={() => setConfirmVisible(true)}>
            <Text style={styles.buyButtonText}>아이템 구매</Text>
          </TouchableOpacity>
        </View>

        <BottomNav navigation={navigation} active="store" />
        <HamburgerMenu visible={menuVisible} onClose={() => setMenuVisible(false)} navigation={navigation} />

        {showToast && (
          <View style={styles.toast}>
            <Text style={styles.toastText}>아이템을 구매했습니다</Text>
          </View>
        )}

        {/* 구매 확인 팝업 (26번) */}
        <Modal statusBarTranslucent visible={confirmVisible} transparent animationType="fade" onRequestClose={() => setConfirmVisible(false)}>
          <View style={styles.confirmOverlay}>
            <Pressable style={StyleSheet.absoluteFill} onPress={() => setConfirmVisible(false)} />
            <View style={styles.confirmCard}>
              <View style={{ alignItems: 'center', gap: 6 }}>
                <Text style={styles.confirmTitle}>구매 하시겠습니까?</Text>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                  <Coins size={13} color={COLORS.gold} />
                  <Text style={styles.confirmPrice}>{item.price}P 사용</Text>
                </View>
              </View>
              <View style={{ flexDirection: 'row', gap: 8, width: '100%' }}>
                <TouchableOpacity style={styles.confirmCancel} onPress={() => setConfirmVisible(false)}>
                  <Text style={styles.confirmCancelText}>아니오</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.confirmOk} onPress={onConfirmBuy}>
                  <Text style={styles.confirmOkText}>예</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>
      </SafeAreaView>
    </GreenGradientBG>
  );
}

