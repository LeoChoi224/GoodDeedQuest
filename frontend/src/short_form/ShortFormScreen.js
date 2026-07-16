import React, { useState } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import api from '../common/api';
import { Video, Film } from 'lucide-react-native';

export default function ShortFormScreen() {
  const [loading, setLoading] = useState(false);
  const [questId, setQuestId] = useState(1);
  const [msg, setMsg] = useState('');

  const handleGenerate = async () => {
    setLoading(true);
    setMsg('');
    try {
      const res = await api.post('/shorts/generate', {
        quest_id: questId,
        user_name: '홍길동',
        bg_music_style: 'calm',
      });
      if (res.success) {
        setMsg(res.message);
      }
    } catch (err) {
      console.error(err);
      setMsg('숏폼 생성 요청 도중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <View style={styles.card}>
        <View style={styles.header}>
          <Film size={24} color="#f59e0b" />
          <Text style={styles.title}> AI 숏폼 동영상 제작</Text>
        </View>
        <Text style={styles.subtitle}>
          인증 사진과 텍스트를 조합해 숏폼 나레이션 음성 및 영상을 자동 합성합니다.
        </Text>

        <Text style={styles.label}>적용할 퀘스트 선택</Text>
        <View style={styles.selector}>
          <TouchableOpacity
            style={[styles.selectorItem, questId === 1 && styles.selectorActive]}
            onPress={() => setQuestId(1)}
          >
            <Text style={[styles.selectorText, questId === 1 && styles.selectorActiveText]}>
              플로깅 퀘스트
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.selectorItem, questId === 2 && styles.selectorActive]}
            onPress={() => setQuestId(2)}
          >
            <Text style={[styles.selectorText, questId === 2 && styles.selectorActiveText]}>
              유기동물 봉사
            </Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity style={styles.generateBtn} onPress={handleGenerate} disabled={loading}>
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <View style={styles.btnRow}>
              <Video size={18} color="#fff" />
              <Text style={styles.generateBtnText}> 숏폼 렌더링 요청</Text>
            </View>
          )}
        </TouchableOpacity>

        {msg ? (
          <View style={styles.alertBox}>
            <Text style={styles.alertText}>📣 {msg}</Text>
          </View>
        ) : null}
      </View>

      <View style={styles.videoPlaceholder}>
        <Video size={36} color="#4b5563" />
        <Text style={styles.placeholderText}>제작이 완료된 동영상이 여기에 노출됩니다.</Text>
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
  card: {
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    marginBottom: 20,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  subtitle: {
    fontSize: 13,
    color: '#9ca3af',
    marginBottom: 20,
    lineHeight: 18,
  },
  label: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  selector: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 20,
  },
  selectorItem: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.2)',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  selectorText: {
    color: '#9ca3af',
    fontSize: 13,
  },
  selectorActive: {
    borderColor: '#f59e0b',
  },
  selectorActiveText: {
    color: '#f59e0b',
    fontWeight: 'bold',
  },
  generateBtn: {
    backgroundColor: '#6366f1',
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
  },
  btnRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  generateBtnText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 15,
  },
  alertBox: {
    backgroundColor: 'rgba(245, 158, 11, 0.1)',
    borderWidth: 1,
    borderColor: '#f59e0b',
    borderRadius: 8,
    padding: 12,
    marginTop: 15,
  },
  alertText: {
    color: '#fff',
    fontSize: 13,
  },
  videoPlaceholder: {
    backgroundColor: 'rgba(255, 255, 255, 0.01)',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.05)',
    padding: 40,
    alignItems: 'center',
    gap: 10,
  },
  placeholderText: {
    color: '#6b7280',
    fontSize: 13,
  },
});
