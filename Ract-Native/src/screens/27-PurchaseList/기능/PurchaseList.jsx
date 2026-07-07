// 27-PurchaseList.js — React Native (Expo) 구매 목록 (장착/해제)
// 선행퀘스트 / 스토리보드 27번 기준

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft } from 'lucide-react-native';
import { ITEMS } from '../../24-Store/기능/Store';

import { COLORS } from '../../../shared/디자인/tokens';
import { CareIcon, GreenGradientBG, BottomNav, HamburgerMenu, HamburgerButton } from '../../../shared/기능/components';
import { styles } from '../디자인/PurchaseList.styles';

export default function PurchaseListScreen({ navigation }) {
  const [menuVisible, setMenuVisible] = useState(false);
  const [equipped, setEquipped] = useState({ i1: false, i2: false, i3: false, i4: true, i5: false });

  const toggleEquip = (id) => setEquipped((s) => ({ ...s, [id]: !s[id] }));

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

        <View style={{ paddingHorizontal: 20, paddingTop: 18, paddingBottom: 10 }}>
          <Text style={styles.title}>구매 목록</Text>
          <Text style={styles.subtitle}>포인트를 모아 아이템을 구매하세요</Text>
        </View>

        <ScrollView contentContainerStyle={styles.list}>
          {ITEMS.map((item) => {
            const isEq = equipped[item.id];
            return (
              <View key={item.id} style={styles.itemRow}>
                <View style={[styles.itemIcon, { backgroundColor: item.iconBg }]}>
                  <Text style={{ fontSize: 26 }}>{item.emoji}</Text>
                </View>
                <View style={{ flex: 1, minWidth: 0, gap: 3 }}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                    <Text style={styles.itemName}>{item.name}</Text>
                    {isEq && (
                      <View style={styles.equippedTag}>
                        <Text style={styles.equippedTagText}>장착중</Text>
                      </View>
                    )}
                  </View>
                  <Text style={styles.itemDesc} numberOfLines={1}>
                    {item.desc}
                  </Text>
                  <TouchableOpacity onPress={() => navigation.navigate('ItemDetail', { itemId: item.id })}>
                    <Text style={styles.detailLink}>상세보기</Text>
                  </TouchableOpacity>
                </View>
                <TouchableOpacity
                  style={[styles.toggleButton, { backgroundColor: isEq ? COLORS.parchment : COLORS.primary }]}
                  onPress={() => toggleEquip(item.id)}
                >
                  <Text style={[styles.toggleButtonText, { color: isEq ? COLORS.inkMuted48 : '#fff' }]}>{isEq ? '해제' : '장착'}</Text>
                </TouchableOpacity>
              </View>
            );
          })}
        </ScrollView>

        <BottomNav navigation={navigation} active="store" />
        <HamburgerMenu visible={menuVisible} onClose={() => setMenuVisible(false)} navigation={navigation} />
      </SafeAreaView>
    </GreenGradientBG>
  );
}

