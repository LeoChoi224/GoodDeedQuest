import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, Alert } from 'react-native';
import api from '../common/api';
import { Users, Calendar } from 'lucide-react-native';

export default function ChallengeScreen() {
  const [challenges, setChallenges] = useState([]);

  useEffect(() => {
    const loadChallenges = async () => {
      try {
        const res = await api.get('/challenges');
        if (res.success) {
          setChallenges(res.data);
        }
      } catch (err) {
        console.error(err);
      }
    };
    loadChallenges();
  }, []);

  const handleJoin = async (id) => {
    try {
      const res = await api.post(`/challenges/join/${id}`);
      Alert.alert('알림', res.message);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <Text style={styles.title}>👥 협동 챌린지 및 팀 매칭</Text>
      <Text style={styles.subtitle}>
        관심사가 같은 사람들과 팀을 이루어 챌린지를 극복하고 선행의 경험치를 획득하세요.
      </Text>

      <View style={styles.list}>
        {challenges.map((c) => {
          const progress = (c.current_xp / c.target_xp) * 100;
          return (
            <View key={c.id} style={styles.card}>
              <Text style={styles.cardTitle}>{c.title}</Text>
              <Text style={styles.cardDesc}>{c.description}</Text>

              <View style={styles.infoRow}>
                <View style={styles.infoItem}>
                  <Users size={14} color="#6366f1" />
                  <Text style={styles.infoText}>{c.participants_count}명 참여 중</Text>
                </View>
                <View style={styles.infoItem}>
                  <Calendar size={14} color="#f59e0b" />
                  <Text style={styles.infoText}>D-{c.days_left}일 남음</Text>
                </View>
              </View>

              <View style={styles.progressBarBg}>
                <View style={[styles.progressBarFill, { width: `${progress}%` }]} />
              </View>

              <View style={styles.footerRow}>
                <Text style={styles.progressText}>
                  {c.current_xp} / {c.target_xp} XP ({Math.round(progress)}%)
                </Text>
                <TouchableOpacity style={styles.joinButton} onPress={() => handleJoin(c.id)}>
                  <Text style={styles.joinButtonText}>참여</Text>
                </TouchableOpacity>
              </View>
            </View>
          );
        })}
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
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#9ca3af',
    marginBottom: 20,
    lineHeight: 20,
  },
  list: {
    gap: 20,
  },
  card: {
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 16,
    padding: 18,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#6366f1',
    marginBottom: 8,
  },
  cardDesc: {
    fontSize: 13,
    color: '#d1d5db',
    marginBottom: 15,
    lineHeight: 18,
  },
  infoRow: {
    flexDirection: 'row',
    gap: 15,
    marginBottom: 12,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  infoText: {
    color: '#9ca3af',
    fontSize: 12,
  },
  progressBarBg: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 10,
    height: 8,
    width: '100%',
    overflow: 'hidden',
    marginBottom: 15,
  },
  progressBarFill: {
    backgroundColor: '#6366f1',
    height: '100%',
  },
  footerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  progressText: {
    fontSize: 12,
    color: '#9ca3af',
  },
  joinButton: {
    backgroundColor: 'rgba(99, 102, 241, 0.15)',
    borderWidth: 1,
    borderColor: '#6366f1',
    borderRadius: 8,
    paddingVertical: 6,
    paddingHorizontal: 16,
  },
  joinButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 13,
  },
});
