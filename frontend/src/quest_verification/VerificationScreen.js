import React, { useState } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import api from '../common/api';
import { Camera, Check, AlertTriangle } from 'lucide-react-native';

export default function VerificationScreen() {
  const [questId, setQuestId] = useState(1);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);

  const handleSimulateFileSelect = () => {
    setSelectedImage({
      uri: 'file://mock-image-path/plogging_verification.jpg',
      name: 'plogging_verification.jpg',
      type: 'image/jpeg',
    });
    Alert.alert('사진 선택 완료(Mock)', '모의 테스트용 가상 사진 파일이 첨부되었습니다.');
  };

  const handleVerify = async () => {
    if (!selectedImage) {
      Alert.alert('오류', '인증할 사진을 선택해 주세요.');
      return;
    }

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append('quest_id', questId.toString());
    formData.append('image', {
      uri: selectedImage.uri,
      name: selectedImage.name,
      type: selectedImage.type,
    });

    try {
      const res = await api.post('/quest-verification/verify', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      if (res.success) {
        setResult(res.data);
      }
    } catch (err) {
      console.error(err);
      setResult({ verified: false, reason: '서버와 통신하는 도중 에러가 발생했습니다.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <View style={styles.card}>
        <Text style={styles.title}>📷 Vision AI 퀘스트 인증</Text>
        <Text style={styles.subtitle}>
          수행한 퀘스트의 인증 사진을 업로드해 주세요. Gemini Vision AI가 조건 충족 여부를 판단합니다.
        </Text>

        <Text style={styles.label}>대상 퀘스트 선택</Text>
        <View style={styles.pickerContainer}>
          <TouchableOpacity style={styles.pickerItem} onPress={() => setQuestId(1)}>
            <Text style={[styles.pickerItemText, questId === 1 && styles.pickerActiveText]}>
              플로깅 인증 (ID: 1)
            </Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.pickerItem} onPress={() => setQuestId(2)}>
            <Text style={[styles.pickerItemText, questId === 2 && styles.pickerActiveText]}>
              유기동물 보호 (ID: 2)
            </Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity style={styles.uploadArea} onPress={handleSimulateFileSelect}>
          <Camera size={36} color="#10b981" style={styles.cameraIcon} />
          <Text style={styles.uploadAreaText}>
            {selectedImage ? selectedImage.name : '인증 사진 촬영 및 첨부하기'}
          </Text>
          <Text style={styles.uploadAreaSubtext}>JPG, PNG 포맷 지원 (시뮬레이터 터치 가능)</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.submitButton, !selectedImage && styles.disabledButton]}
          onPress={handleVerify}
          disabled={loading || !selectedImage}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.submitButtonText}>인증서 제출하기</Text>
          )}
        </TouchableOpacity>

        {result && (
          <View
            style={[
              styles.resultCard,
              result.verified ? styles.successResult : styles.failResult,
            ]}
          >
            <View style={styles.resultHeader}>
              {result.verified ? (
                <Check size={20} color="#10b981" />
              ) : (
                <AlertTriangle size={20} color="#ef4444" />
              )}
              <Text style={styles.resultTitle}>
                {result.verified ? '인증 성공' : '인증 반려'}
              </Text>
            </View>
            <Text style={styles.resultReason}>{result.reason}</Text>
            {result.verified && result.rewards && (
              <View style={styles.rewardBox}>
                <Text style={styles.rewardText}>
                  🎁 획득 보상: XP +{result.rewards.xp_gained} | 포인트 +{result.rewards.points_gained}
                </Text>
              </View>
            )}
          </View>
        )}
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
  },
  title: {
    fontSize: 20,
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
  label: {
    color: '#f3f4f6',
    fontWeight: 'bold',
    fontSize: 14,
    marginBottom: 10,
  },
  pickerContainer: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 20,
  },
  pickerItem: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.2)',
    paddingVertical: 10,
    paddingHorizontal: 8,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  pickerItemText: {
    color: '#9ca3af',
    fontSize: 13,
  },
  pickerActiveText: {
    color: '#10b981',
    fontWeight: 'bold',
  },
  uploadArea: {
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: 'rgba(255, 255, 255, 0.15)',
    borderRadius: 12,
    paddingVertical: 30,
    alignItems: 'center',
    marginBottom: 20,
    backgroundColor: 'rgba(255,255,255,0.01)',
  },
  cameraIcon: {
    marginBottom: 10,
  },
  uploadAreaText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 15,
  },
  uploadAreaSubtext: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 6,
  },
  submitButton: {
    backgroundColor: '#10b981',
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
  },
  disabledButton: {
    backgroundColor: '#374151',
  },
  submitButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  resultCard: {
    marginTop: 20,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  successResult: {
    backgroundColor: 'rgba(16, 185, 129, 0.08)',
    borderColor: '#10b981',
  },
  failResult: {
    backgroundColor: 'rgba(239, 68, 68, 0.08)',
    borderColor: '#ef4444',
  },
  resultHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  resultTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  resultReason: {
    color: '#e5e7eb',
    fontSize: 14,
    lineHeight: 20,
  },
  rewardBox: {
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.1)',
    marginTop: 10,
    paddingTop: 10,
  },
  rewardText: {
    color: '#f59e0b',
    fontSize: 13,
    fontWeight: '600',
  },
});
