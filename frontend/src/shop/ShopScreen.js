import React, { useState } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, Alert } from 'react-native';
import api from '../common/api';
import { ShoppingBag, Gift } from 'lucide-react-native';

export default function ShopScreen() {
  const [points, setPoints] = useState(340);

  const handlePurchase = async (itemId) => {
    try {
      const res = await api.post('/shop/purchase', { item_id: itemId });
      Alert.alert('성공', res.message);
      if (itemId === 1) setPoints((prev) => prev - 100);
      if (itemId === 2) setPoints((prev) => prev - 500);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <View style={styles.header}>
        <ShoppingBag size={24} color="#ec4899" />
        <Text style={styles.title}> 포인트 기부 & 상점</Text>
      </View>
      <Text style={styles.subtitle}>
        선행 퀘스트를 성공하고 획득한 포인트로 탄소 저감 기부에 참여하거나 친환경 굿즈로 교환해 보세요!
      </Text>

      <View style={styles.pointsCard}>
        <Text style={styles.pointsLabel}>보유 포인트</Text>
        <Text style={styles.pointsValue}>{points} P</Text>
      </View>

      <Text style={styles.sectionTitle}>리워드 목록</Text>
      <View style={styles.list}>
        <View style={styles.card}>
          <Text style={styles.cardIcon}>🌳</Text>
          <Text style={styles.cardTitle}>탄소 저감 나무 심기 기부</Text>
          <Text style={styles.cardDesc}>
            사막화 지역에 나무 한 그루를 기부하여 건강한 지구를 만드는 데 동참합니다.
          </Text>
          <TouchableOpacity style={styles.buyButton} onPress={() => handlePurchase(1)}>
            <Gift size={16} color="#fff" />
            <Text style={styles.buyButtonText}> 100 P 기부</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardIcon}>👕</Text>
          <Text style={styles.cardTitle}>오가닉 친환경 캠페인 티셔츠</Text>
          <Text style={styles.cardDesc}>
            100% 오가닉 면으로 생산된 친환경 캠페인 공식 티셔츠로 교환합니다.
          </Text>
          <TouchableOpacity
            style={[styles.buyButton, points < 500 && styles.disabledButton]}
            onPress={() => handlePurchase(2)}
            disabled={points < 500}
          >
            <Gift size={16} color="#fff" />
            <Text style={styles.buyButtonText}> 500 P 교환</Text>
          </TouchableOpacity>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0b0f19',
  },
  contentContainer: {
    padding: 20,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
  },
  subtitle: {
    fontSize: 13,
    color: '#9ca3af',
    marginBottom: 20,
    lineHeight: 18,
  },
  pointsCard: {
    backgroundColor: 'rgba(236, 72, 153, 0.1)',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(236, 72, 153, 0.2)',
    alignItems: 'center',
    marginBottom: 25,
  },
  pointsLabel: {
    color: '#ec4899',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  pointsValue: {
    color: '#fff',
    fontSize: 28,
    fontWeight: '800',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  list: {
    gap: 15,
  },
  card: {
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 16,
    padding: 18,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  cardIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 6,
  },
  cardDesc: {
    fontSize: 13,
    color: '#9ca3af',
    marginBottom: 15,
    lineHeight: 18,
  },
  buyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#ec4899',
    borderRadius: 10,
    paddingVertical: 10,
    gap: 5,
  },
  disabledButton: {
    backgroundColor: '#4b5563',
  },
  buyButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
});
