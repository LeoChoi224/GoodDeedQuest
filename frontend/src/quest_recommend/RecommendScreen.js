import React, { useState } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import api from '../common/api';
import { Sparkles } from 'lucide-react-native';

export default function RecommendScreen() {
  const [loading, setLoading] = useState(false);
  const [quests, setQuests] = useState([]);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const res = await api.post('/quest-recommend');
      if (res.success) {
        setQuests(res.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <View style={styles.heroCard}>
        <Text style={styles.heroTitle}>🤖 AI 맞춤형 퀘스트 추천</Text>
        <Text style={styles.heroSubtitle}>
          사용자님의 관심사와 활동 이력을 기반으로 최적의 선행 퀘스트를 AI가 실시간 매칭합니다.
        </Text>
        
        <TouchableOpacity style={styles.recommendButton} onPress={fetchRecommendations} disabled={loading}>
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <View style={styles.buttonRow}>
              <Sparkles size={18} color="#fff" />
              <Text style={styles.recommendButtonText}> AI에게 추천받기</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      <View style={styles.listContainer}>
        {quests.map((q) => (
          <View key={q.id} style={styles.questCard}>
            <Text style={styles.questTitle}>{q.title}</Text>
            <Text style={styles.questDesc}>{q.description}</Text>
            <View style={styles.reasonBox}>
              <Text style={styles.reasonText}>💡 AI 추천 이유: {q.reason}</Text>
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
  heroCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    alignItems: 'center',
    marginBottom: 20,
  },
  heroTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  heroSubtitle: {
    fontSize: 14,
    color: '#9ca3af',
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 20,
  },
  recommendButton: {
    backgroundColor: '#10b981',
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 24,
    alignItems: 'center',
  },
  buttonRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  recommendButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  listContainer: {
    gap: 15,
  },
  questCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 16,
    padding: 18,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    borderLeftWidth: 4,
    borderLeftColor: '#10b981',
  },
  questTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#10b981',
    marginBottom: 6,
  },
  questDesc: {
    fontSize: 14,
    color: '#f3f4f6',
    marginBottom: 15,
    lineHeight: 20,
  },
  reasonBox: {
    backgroundColor: 'rgba(16, 185, 129, 0.08)',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.2)',
  },
  reasonText: {
    fontSize: 13,
    color: '#f3f4f6',
    lineHeight: 18,
  },
});
