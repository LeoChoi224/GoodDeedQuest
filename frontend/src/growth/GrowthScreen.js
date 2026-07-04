import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, ScrollView } from 'react-native';
import api from '../common/api';
import { Award, ShieldCheck, Flame, Gift } from 'lucide-react-native';

export default function GrowthScreen() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const res = await api.get('/growth/status');
        if (res.success) {
          setStatus(res.data);
        }
      } catch (err) {
        console.error(err);
      }
    };
    loadStatus();
  }, []);

  if (!status) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>성장 데이터를 불러오는 중...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <Text style={styles.title}>🎮 나의 선행 성장 대시보드</Text>

      <View style={styles.grid}>
        <View style={styles.gridItem}>
          <Award size={32} color="#10b981" />
          <Text style={styles.label}>레벨</Text>
          <Text style={styles.value}>Lv.{status.level}</Text>
        </View>
        <View style={styles.gridItem}>
          <ShieldCheck size={32} color="#6366f1" />
          <Text style={styles.label}>경험치</Text>
          <Text style={styles.value}>{status.xp} XP</Text>
          <Text style={styles.subtext}>다음 레벨: {status.next_level_xp - status.xp} XP 남음</Text>
        </View>
        <View style={styles.gridItem}>
          <Flame size={32} color="#f59e0b" />
          <Text style={styles.label}>스트릭</Text>
          <Text style={styles.value}>{status.streak_days}일 연속</Text>
        </View>
        <View style={styles.gridItem}>
          <Gift size={32} color="#ec4899" />
          <Text style={styles.label}>포인트</Text>
          <Text style={[styles.value, { color: '#ec4899' }]}>{status.points} P</Text>
        </View>
      </View>

      <Text style={styles.sectionTitle}>🏅 획득한 선행 배지</Text>
      <View style={styles.badgeContainer}>
        {status.badges.map((badge, idx) => (
          <View key={idx} style={styles.badgeCard}>
            <Text style={styles.badgeIcon}>🏆</Text>
            <View>
              <Text style={styles.badgeName}>{badge}</Text>
              <Text style={styles.badgeSub}>선행 퀘스트 클리어</Text>
            </View>
          </View>
        ))}
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
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 20,
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#0b0f19',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#9ca3af',
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 15,
    marginBottom: 30,
  },
  gridItem: {
    width: '47%',
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    alignItems: 'center',
  },
  label: {
    color: '#9ca3af',
    fontSize: 12,
    marginTop: 8,
    marginBottom: 4,
  },
  value: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  subtext: {
    fontSize: 9,
    color: '#6b7280',
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  badgeContainer: {
    gap: 10,
  },
  badgeCard: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
    gap: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  badgeIcon: {
    fontSize: 24,
  },
  badgeName: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  badgeSub: {
    color: '#6b7280',
    fontSize: 11,
  },
});
