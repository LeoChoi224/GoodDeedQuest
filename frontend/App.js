import React, { useState } from 'react';
import { StyleSheet, Text, View, SafeAreaView, TouchableOpacity, StatusBar } from 'react-native';
import { Sparkles, Camera, Users, Video, MapPin, Award, MessageSquare, ShieldAlert, ShoppingBag } from 'lucide-react-native';

// 화면 컴포넌트 임포트
import RecommendScreen from './src/quest_recommend/RecommendScreen';
import VerificationScreen from './src/quest_verification/VerificationScreen';
import ChallengeScreen from './src/challenge/ChallengeScreen';
import ShortsScreen from './src/shorts/ShortsScreen';
import MapScreen from './src/map/MapScreen';
import GrowthScreen from './src/growth/GrowthScreen';
import ShopScreen from './src/shop/ShopScreen';
import CoachScreen from './src/quest_recommend/CoachScreen'; // quest_recommend 폴더로 통합 이관
import AdminScreen from './src/admin/AdminScreen';
import AuthScreen from './src/auth/AuthScreen';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState('Recommend');

  const renderScreen = () => {
    switch (currentScreen) {
      case 'Auth':
        return <AuthScreen />;
      case 'Recommend':
        return <RecommendScreen />;
      case 'Verify':
        return <VerificationScreen />;
      case 'Challenge':
        return <ChallengeScreen />;
      case 'Shorts':
        return <ShortsScreen />;
      case 'Map':
        return <MapScreen />;
      case 'Growth':
        return <GrowthScreen />;
      case 'Shop':
        return <ShopScreen />;
      case 'Coach':
        return <CoachScreen />;
      case 'Admin':
        return <AdminScreen />;
      default:
        return <RecommendScreen />;
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0b0f19" />
      
      <View style={styles.header}>
        <Text style={styles.logo}>🌱 GDQuest</Text>
        <TouchableOpacity style={styles.loginBtn} onPress={() => setCurrentScreen('Auth')}>
          <Text style={styles.loginBtnText}>로그인</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.body}>
        {renderScreen()}
      </View>

      <View style={styles.tabBar}>
        <TouchableOpacity style={styles.tabItem} onPress={() => setCurrentScreen('Recommend')}>
          <Sparkles size={20} color={currentScreen === 'Recommend' ? '#10b981' : '#6b7280'} />
          <Text style={[styles.tabLabel, currentScreen === 'Recommend' && styles.tabLabelActive]}>추천</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.tabItem} onPress={() => setCurrentScreen('Verify')}>
          <Camera size={20} color={currentScreen === 'Verify' ? '#10b981' : '#6b7280'} />
          <Text style={[styles.tabLabel, currentScreen === 'Verify' && styles.tabLabelActive]}>인증</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.tabItem} onPress={() => setCurrentScreen('Map')}>
          <MapPin size={20} color={currentScreen === 'Map' ? '#10b981' : '#6b7280'} />
          <Text style={[styles.tabLabel, currentScreen === 'Map' && styles.tabLabelActive]}>지도</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.tabItem} onPress={() => setCurrentScreen('Shop')}>
          <ShoppingBag size={20} color={currentScreen === 'Shop' ? '#ec4899' : '#6b7280'} />
          <Text style={[styles.tabLabel, currentScreen === 'Shop' && styles.tabLabelActiveShop]}>상점</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.tabItem} onPress={() => setCurrentScreen('Growth')}>
          <Award size={20} color={currentScreen === 'Growth' ? '#10b981' : '#6b7280'} />
          <Text style={[styles.tabLabel, currentScreen === 'Growth' && styles.tabLabelActive]}>성장</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.tabItem} onPress={() => setCurrentScreen('Coach')}>
          <MessageSquare size={20} color={currentScreen === 'Coach' ? '#10b981' : '#6b7280'} />
          <Text style={[styles.tabLabel, currentScreen === 'Coach' && styles.tabLabelActive]}>코치</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.tabItem} onPress={() => setCurrentScreen('Admin')}>
          <ShieldAlert size={20} color={currentScreen === 'Admin' ? '#ef4444' : '#6b7280'} />
          <Text style={[styles.tabLabel, currentScreen === 'Admin' && styles.tabLabelActiveAdmin]}>관리</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0b0f19',
  },
  header: {
    height: 56,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.08)',
  },
  logo: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#10b981',
  },
  loginBtn: {
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    borderRadius: 8,
    paddingVertical: 5,
    paddingHorizontal: 12,
  },
  loginBtnText: {
    color: '#10b981',
    fontSize: 12,
    fontWeight: 'bold',
  },
  body: {
    flex: 1,
  },
  tabBar: {
    height: 60,
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.08)',
    backgroundColor: '#0b0f19',
    justifyContent: 'space-around',
    alignItems: 'center',
  },
  tabItem: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  tabLabel: {
    fontSize: 10,
    color: '#6b7280',
    marginTop: 4,
  },
  tabLabelActive: {
    color: '#10b981',
    fontWeight: 'bold',
  },
  tabLabelActiveShop: {
    color: '#ec4899',
    fontWeight: 'bold',
  },
  tabLabelActiveAdmin: {
    color: '#ef4444',
    fontWeight: 'bold',
  },
});
