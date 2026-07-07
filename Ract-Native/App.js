// App.js — 선행퀘스트 React Native 통합 앱 (Expo)
// 인증부터 홈/지도/상점/커뮤니티/마이페이지/관리자까지 전체 화면을 이 파일 하나로 통합했습니다.
// 각 화면은 개별 파일에서 import — 로직/애니메이션은 그 파일들이 단일 소스입니다.
//
// 설치:
//   npm i @react-navigation/native @react-navigation/native-stack
//   npm i react-native-screens react-native-safe-area-context react-native-gesture-handler
//   npm i lucide-react-native react-native-svg
//   npx expo install expo-linear-gradient
//
// ⚠️ 14-QuestSubmissionScreen(단독 페이지), 19/26/34(팝업 상태 전용 화면), 46~49(숏폼 팝업
//    상태), 55(신고 처리 확인 팝업)는 각각 12/25/32/39/54번 화면의 모달로 통합되어 별도
//    파일이 없습니다 — dc.html 스토리보드와 동일한 구조입니다.
// 41(달성 퀘스트 강조 이펙트)은 35-MyPage.js의 업적 팝업에 컨페티+글로우 애니메이션으로
//    통합했습니다.
// 지도 화면(17/22)은 react-native-svg로 그린 대한민국 8도 지도를 공용으로 씁니다.

import 'react-native-gesture-handler';
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, StatusBar } from 'react-native';
import { SafeAreaView, SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Users, MapPin, Home, Coins, User } from 'lucide-react-native';
import Svg, { Path } from 'react-native-svg';

import LoginScreen from './src/screens/06-LoginScreen/기능/LoginScreen';
import SignupTermsScreen from './src/screens/07-SignupTermsScreen/기능/SignupTermsScreen';
import SignupAccountScreen from './src/screens/08-SignupAccountScreen/기능/SignupAccountScreen';
import SignupProfileScreen from './src/screens/09-SignupProfileScreen/기능/SignupProfileScreen';
import SignupCompleteScreen from './src/screens/10-SignupCompleteScreen/기능/SignupCompleteScreen';
import MainScreen from './src/screens/11-MainScreen/기능/MainScreen';
import QuestDetailScreen from './src/screens/12-QuestDetailScreen/기능/QuestDetailScreen';
import CustomQuestScreen from './src/screens/13-CustomQuestScreen/기능/CustomQuestScreen';
import QuestChatbotScreen from './src/screens/15-QuestChatbot/기능/QuestChatbot';
import MapMainScreen from './src/screens/17-MapMain/기능/MapMain';
import NearbyScreen from './src/screens/18-Nearby/기능/Nearby';
import CenterDetailScreen from './src/screens/20-CenterDetail/기능/CenterDetail';
import RegionSearchScreen from './src/screens/21-RegionSearch/기능/RegionSearch';
import CompetitionScreen from './src/screens/22-Competition/기능/Competition';
import DistrictRankingScreen from './src/screens/23-DistrictRanking/기능/DistrictRanking';
import StoreScreen from './src/screens/24-Store/기능/Store';
import ItemDetailScreen from './src/screens/25-ItemDetail/기능/ItemDetail';
import PurchaseListScreen from './src/screens/27-PurchaseList/기능/PurchaseList';
import CommunityScreen from './src/screens/28-Community/기능/Community';
import TeamChallengeScreen from './src/screens/29-TeamChallenge/기능/TeamChallenge';
import RoomCreateScreen from './src/screens/30-RoomCreate/기능/RoomCreate';
import RoomFindScreen from './src/screens/31-RoomFind/기능/RoomFind';
import TeamDetailScreen from './src/screens/32-TeamDetail/기능/TeamDetail';
import UserRecommendScreen from './src/screens/33-UserRecommend/기능/UserRecommend';
import TeamListScreen from './src/screens/34-TeamList/기능/TeamList';
import MyPageScreen from './src/screens/35-MyPage/기능/MyPage';
import MyLevelScreen from './src/screens/36-MyLevel/기능/MyLevel';
import UserDetailScreen from './src/screens/37-UserDetail/기능/UserDetail';
import MyRankingScreen from './src/screens/38-MyRanking/기능/MyRanking';
import ShortFormCreateScreen from './src/screens/39-ShortFormCreate/기능/ShortFormCreate';
import ShortFormGenerateScreen from './src/screens/40-ShortFormGenerate/기능/ShortFormGenerate';
import AdminDashboardScreen from './src/screens/50-AdminDashboard/기능/AdminDashboard';
import AdminUserListScreen from './src/screens/51-AdminUserList/기능/AdminUserList';
import AdminReportsScreen from './src/screens/53-AdminReports/기능/AdminReports';
import AdminReportDetailScreen from './src/screens/54-AdminReportDetail/기능/AdminReportDetail';

const COLORS = {
  primary: '#033236',
  canvas: '#FFFFFF',
  ink: '#1D1D1F',
  inkMuted48: '#7A7A7A',
  hairline: 'rgba(0,0,0,0.08)',
};

function CareIcon({ size = 18 }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round">
      <Path d="M12 6.8c-.9-1.6-3-1.8-4.1-.4-.9 1.1-.7 2.7.4 3.7L12 13l3.7-2.9c1.1-1 1.3-2.6.4-3.7-1.1-1.4-3.2-1.2-4.1.4Z" />
      <Path d="M4.3 13.2c0 3.2 2.9 5.9 6.4 6.3" />
      <Path d="M19.7 13.2c0 3.2-2.9 5.9-6.4 6.3" />
    </Svg>
  );
}

function NavItem({ Icon, label, onPress, active }) {
  return (
    <TouchableOpacity style={placeholderStyles.navItem} onPress={onPress}>
      <Icon size={22} color={active ? COLORS.primary : COLORS.inkMuted48} strokeWidth={active ? 2 : 1.6} />
      <Text style={[placeholderStyles.navLabel, active && { color: COLORS.primary, fontWeight: '600' }]}>{label}</Text>
    </TouchableOpacity>
  );
}

function BottomNav({ navigation, active }) {
  return (
    <View style={placeholderStyles.bottomNav}>
      <NavItem Icon={Users} label="커뮤니티" active={active === 'community'} onPress={() => navigation.navigate('Community')} />
      <NavItem Icon={MapPin} label="지도" active={active === 'map'} onPress={() => navigation.navigate('Map')} />
      <NavItem Icon={Home} label="홈" active={active === 'home'} onPress={() => navigation.navigate('Main')} />
      <NavItem Icon={Coins} label="상점" active={active === 'store'} onPress={() => navigation.navigate('Store')} />
      <NavItem Icon={User} label="마이" active={active === 'mypage'} onPress={() => navigation.navigate('MyPage')} />
    </View>
  );
}

// 아직 RN으로 옮기지 않은 화면(하단 탭 4개, 챗봇, 햄버거 메뉴의 미구현 하위 화면들) 자리.
// route.params.title로 어떤 화면인지 표시하고, activeTab이 있으면 하단 탭도 강조.
function PlaceholderScreen({ navigation, route }) {
  const title = route?.params?.title ?? '준비 중';
  const activeTab = route?.params?.activeTab;

  return (
    <SafeAreaView style={placeholderStyles.container}>
      <View style={placeholderStyles.header}>
        <View style={placeholderStyles.logoBadge}>
          <CareIcon size={18} />
        </View>
        <Text style={placeholderStyles.logo}>선·퀘</Text>
      </View>

      <View style={placeholderStyles.content}>
        <Text style={placeholderStyles.title}>{title}</Text>
        <Text style={placeholderStyles.subtitle}>이 화면은 아직 React Native로 옮기지 않았어요.{'\n'}디자인 시안(dc.html)을 참고해 주세요.</Text>
      </View>

      <BottomNav navigation={navigation} active={activeTab} />
    </SafeAreaView>
  );
}

const placeholderStyles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.canvas },
  header: { paddingHorizontal: 20, paddingTop: 12, flexDirection: 'row', alignItems: 'center', gap: 8 },
  logoBadge: { width: 30, height: 30, borderRadius: 9, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  logo: { fontSize: 20, fontWeight: '700', color: COLORS.primary },
  content: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 8, paddingHorizontal: 32 },
  title: { fontSize: 17, fontWeight: '600', color: COLORS.ink },
  subtitle: { fontSize: 13, color: COLORS.inkMuted48, textAlign: 'center', lineHeight: 19 },
  bottomNav: { flexDirection: 'row', justifyContent: 'space-around', paddingTop: 10, paddingBottom: 20, borderTopWidth: 1, borderTopColor: COLORS.hairline, backgroundColor: COLORS.canvas },
  navItem: { alignItems: 'center', gap: 4, width: 56 },
  navLabel: { fontSize: 10, color: COLORS.inkMuted48 },
});

const Stack = createNativeStackNavigator();

export default function App() {
  return (
    <SafeAreaProvider>
      {/* 앱 전역 상태바 — 대부분 화면이 밝은 배경이라 어두운 아이콘. 안드로이드 edge-to-edge에선
          배경이 투명 처리되어 화면 그라디언트가 상태바 뒤로 자연스럽게 이어집니다. */}
      <StatusBar
        barStyle="dark-content"
        translucent
        backgroundColor="transparent"
      />
      <NavigationContainer>
        <Stack.Navigator initialRouteName="Login" screenOptions={{ headerShown: false }}>
        {/* 온보딩 */}
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="SignupTerms" component={SignupTermsScreen} />
        <Stack.Screen name="SignupAccount" component={SignupAccountScreen} />
        <Stack.Screen name="SignupProfile" component={SignupProfileScreen} />
        <Stack.Screen name="SignupComplete" component={SignupCompleteScreen} />

        {/* 홈 / 퀘스트 (인증 제출은 QuestDetail 내부 팝업으로 통합됨) */}
        <Stack.Screen name="Main" component={MainScreen} />
        <Stack.Screen name="QuestDetail" component={QuestDetailScreen} />
        <Stack.Screen name="QuestRegister" component={CustomQuestScreen} />
        <Stack.Screen name="QuestRecommendChat" component={QuestChatbotScreen} />

        {/* 지도 */}
        <Stack.Screen name="MapMain" component={MapMainScreen} />
        <Stack.Screen name="Map" component={MapMainScreen} />
        <Stack.Screen name="Nearby" component={NearbyScreen} />
        <Stack.Screen name="CenterDetail" component={CenterDetailScreen} />
        <Stack.Screen name="RegionSearch" component={RegionSearchScreen} />
        <Stack.Screen name="Competition" component={CompetitionScreen} />
        <Stack.Screen name="DistrictRanking" component={DistrictRankingScreen} />

        {/* 상점 */}
        <Stack.Screen name="Store" component={StoreScreen} />
        <Stack.Screen name="ItemDetail" component={ItemDetailScreen} />
        <Stack.Screen name="PurchaseList" component={PurchaseListScreen} />

        {/* 커뮤니티 / 팀 */}
        <Stack.Screen name="Community" component={CommunityScreen} />
        <Stack.Screen name="CommunityFeed" component={CommunityScreen} />
        <Stack.Screen name="TeamChallenge" component={TeamChallengeScreen} />
        <Stack.Screen name="RoomCreate" component={RoomCreateScreen} />
        <Stack.Screen name="RoomFind" component={RoomFindScreen} />
        <Stack.Screen name="TeamDetail" component={TeamDetailScreen} />
        <Stack.Screen name="UserRecommend" component={UserRecommendScreen} />
        <Stack.Screen name="TeamList" component={TeamListScreen} />
        <Stack.Screen name="UserDetail" component={UserDetailScreen} />
        <Stack.Screen name="ShortFormCreate" component={ShortFormCreateScreen} />
        <Stack.Screen name="ShortFormGenerate" component={ShortFormGenerateScreen} />

        {/* 마이페이지 */}
        <Stack.Screen name="MyPage" component={MyPageScreen} />
        <Stack.Screen name="MyLevel" component={MyLevelScreen} />
        <Stack.Screen name="MyRanking" component={MyRankingScreen} />

        {/* 관리자 (별도 플로우) */}
        <Stack.Screen name="AdminDashboard" component={AdminDashboardScreen} />
        <Stack.Screen name="AdminUserList" component={AdminUserListScreen} />
        <Stack.Screen name="AdminReports" component={AdminReportsScreen} />
        <Stack.Screen name="AdminReportDetail" component={AdminReportDetailScreen} />

        {/* 메인 햄버거 메뉴에서 실제 화면이 없는 하위 항목이 여기로 연결됩니다 (title은 항목별로 동적 전달) */}
        <Stack.Screen name="Placeholder" component={PlaceholderScreen} />
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
