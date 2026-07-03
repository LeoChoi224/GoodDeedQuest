import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, Alert } from 'react-native';
import api from '../common/api';
import { ShieldAlert, Check } from 'lucide-react-native';

export default function AdminScreen() {
  const [reports, setReports] = useState([]);

  useEffect(() => {
    const loadReports = async () => {
      try {
        const res = await api.get('/admin/reports');
        if (res.success) {
          setReports(res.data);
        }
      } catch (err) {
        console.error(err);
      }
    };
    loadReports();
  }, []);

  const handleResolve = async (id) => {
    try {
      const res = await api.post(`/admin/reports/${id}/resolve`);
      Alert.alert('알림', res.message);
      setReports((prev) =>
        prev.map((r) => (r.id === id ? { ...r, status: '해결됨' } : r))
      );
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <View style={styles.header}>
        <ShieldAlert size={22} color="#ef4444" />
        <Text style={styles.title}> 어드민 - 부정 인증 및 신고 관리</Text>
      </View>
      <Text style={styles.subtitle}>
        Vision AI 및 사용자가 제기한 부정 인증 건을 심사하여 처리합니다.
      </Text>

      <View style={styles.list}>
        {reports.map((r) => (
          <View key={r.id} style={styles.card}>
            <View style={styles.cardHeader}>
              <View
                style={[
                  styles.badge,
                  r.status === '대기중' ? styles.pendingBadge : styles.resolvedBadge,
                ]}
              >
                <Text
                  style={[
                    styles.badgeText,
                    r.status === '대기중' ? styles.pendingBadgeText : styles.resolvedBadgeText,
                  ]}
                >
                  {r.status}
                </Text>
              </View>
              <Text style={styles.reporterText}>신고자 ID: {r.reporter_id}</Text>
            </View>

            <Text style={styles.targetTitle}>🚨 대상 퀘스트 ID: {r.target_quest_id}</Text>
            <Text style={styles.reasonText}>신고 사유: {r.reason}</Text>

            {r.status === '대기중' && (
              <TouchableOpacity style={styles.resolveBtn} onPress={() => handleResolve(r.id)}>
                <Check size={14} color="#fff" />
                <Text style={styles.resolveBtnText}> 해결 완료 처리</Text>
              </TouchableOpacity>
            )}
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  subtitle: {
    fontSize: 12,
    color: '#9ca3af',
    marginBottom: 20,
  },
  list: {
    gap: 15,
  },
  card: {
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  badge: {
    borderRadius: 4,
    paddingVertical: 2,
    paddingHorizontal: 8,
  },
  pendingBadge: {
    backgroundColor: 'rgba(245, 158, 11, 0.15)',
  },
  resolvedBadge: {
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
  },
  badgeText: {
    fontSize: 11,
    fontWeight: 'bold',
  },
  pendingBadgeText: {
    color: '#f59e0b',
  },
  resolvedBadgeText: {
    color: '#10b981',
  },
  reporterText: {
    fontSize: 11,
    color: '#6b7280',
  },
  targetTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  reasonText: {
    fontSize: 13,
    color: '#9ca3af',
    marginBottom: 15,
  },
  resolveBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#ef4444',
    borderRadius: 8,
    paddingVertical: 8,
  },
  resolveBtnText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: 'bold',
  },
});
