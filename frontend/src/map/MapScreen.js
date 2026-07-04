import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity } from 'react-native';
import api from '../common/api';
import { MapPin, Navigation } from 'lucide-react-native';

export default function MapScreen() {
  const [quests, setQuests] = useState([]);
  const [coords, setCoords] = useState({ lat: 37.5562, lng: 126.9223 });

  useEffect(() => {
    const fetchNearby = async () => {
      try {
        const res = await api.get('/map/quests', {
          params: { lat: coords.lat, lng: coords.lng, radius_meters: 1500 },
        });
        if (res.success) {
          setQuests(res.data);
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchNearby();
  }, [coords]);

  const handleGetCurrentLocation = () => {
    setCoords({ lat: 37.5585, lng: 126.9255 });
  };

  return (
    <View style={styles.container}>
      <View style={styles.mapArea}>
        <MapPin size={40} color="#10b981" style={styles.bounceMarker} />
        <Text style={styles.mapTitle}>🗺️ Kakao Map SDK MapView 영역</Text>
        <Text style={styles.mapSubtitle}>
          React Native용 Kakao Map 라이브러리 또는 WebView 컴포넌트를 이 자리에 결합해 마커를 표기하세요.
        </Text>
        <Text style={styles.coordsText}>
          현재 좌표: {coords.lat.toFixed(4)}, {coords.lng.toFixed(4)}
        </Text>
      </View>

      <View style={styles.bottomSheet}>
        <View style={styles.sheetHeader}>
          <Text style={styles.sheetTitle}>내 주변 선행 스팟</Text>
          <TouchableOpacity style={styles.gpsButton} onPress={handleGetCurrentLocation}>
            <Navigation size={14} color="#fff" />
            <Text style={styles.gpsButtonText}> GPS 갱신</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.list}>
          {quests.map((q) => (
            <View key={q.id} style={styles.listItem}>
              <View style={styles.listHeader}>
                <MapPin size={16} color="#10b981" />
                <Text style={styles.itemTitle}>{q.title}</Text>
              </View>
              <Text style={styles.itemAddr}>📍 {q.address}</Text>
              <Text style={styles.itemReward}>보상: +{q.xp_reward} XP</Text>
            </View>
          ))}
        </ScrollView>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0b0f19',
  },
  mapArea: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#111827',
    padding: 24,
  },
  bounceMarker: {
    marginBottom: 10,
  },
  mapTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 6,
  },
  mapSubtitle: {
    color: '#6b7280',
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
    maxWidth: 280,
    marginBottom: 15,
  },
  coordsText: {
    color: '#10b981',
    fontSize: 11,
    fontFamily: 'monospace',
  },
  bottomSheet: {
    flex: 1,
    backgroundColor: '#161d30',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.08)',
  },
  sheetHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  sheetTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  gpsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#10b981',
    borderRadius: 8,
    paddingVertical: 5,
    paddingHorizontal: 12,
  },
  gpsButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  list: {
    flex: 1,
  },
  listItem: {
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.05)',
    marginBottom: 10,
  },
  listHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 5,
  },
  itemTitle: {
    color: '#10b981',
    fontWeight: 'bold',
    fontSize: 14,
  },
  itemAddr: {
    color: '#9ca3af',
    fontSize: 12,
    marginBottom: 6,
  },
  itemReward: {
    color: '#f59e0b',
    fontSize: 12,
  },
});
