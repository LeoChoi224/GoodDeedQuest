/**
 * Per-flow nested stacks. Each screen renders its own MainHeader, so headerShown is
 * off and transitions use the iOS slide. Route names are the contract the flow agents
 * navigate against (see CONTRACT.md).
 */
import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

// quest (02)
import QuestHome from '../screens/quest/HomeScreen';
import QuestDetailScreen from '../screens/quest/QuestDetailScreen';
import QuestVerifyScreen from '../screens/quest/QuestVerifyScreen';
import QuestChallengeScreen from '../screens/quest/QuestChallengeScreen';
import QuestCompleteScreen from '../screens/quest/QuestCompleteScreen';
import QuestRegisterScreen from '../screens/quest/QuestRegisterScreen';
import AiRecommendScreen from '../screens/quest/AiRecommendScreen';
// community (03)
import FeedScreen from '../screens/community/FeedScreen';
import NewPostScreen from '../screens/community/NewPostScreen';
// (TeamHomeScreen is imported below in the team section; reused as the Community
//  "팀 챌린지" 탭 진입점 — BUG-1)
// shop (04)
import ShopScreen from '../screens/shop/ShopScreen';
import ItemDetailScreen from '../screens/shop/ItemDetailScreen';
import PurchaseHistoryScreen from '../screens/shop/PurchaseHistoryScreen';
import InventoryScreen from '../screens/shop/InventoryScreen';
// map (05)
import MapScreen from '../screens/map/MapScreen';
import RankingScreen from '../screens/map/RankingScreen';
import NearbyScreen from '../screens/map/NearbyScreen';
import VolunteerDetailScreen from '../screens/map/VolunteerDetailScreen';
// mypage (06)
import MyPageScreen from '../screens/mypage/MyPageScreen';
import LevelScreen from '../screens/mypage/LevelScreen';
import RankScreen from '../screens/mypage/RankScreen';
import ItemListScreen from '../screens/mypage/ItemListScreen';
// team (07)
import TeamHomeScreen from '../screens/team/TeamHomeScreen';
import RoomFindScreen from '../screens/team/RoomFindScreen';
import TeamDetailScreen from '../screens/team/TeamDetailScreen';
import TeamListScreen from '../screens/team/TeamListScreen';
// shortform (08)
import PhotoSelectScreen from '../screens/shortform/PhotoSelectScreen';
import GeneratingScreen from '../screens/shortform/GeneratingScreen';
import PlayerScreen from '../screens/shortform/PlayerScreen';
// admin (09)
import DashboardScreen from '../screens/admin/DashboardScreen';
import UserListScreen from '../screens/admin/UserListScreen';
import ReportListScreen from '../screens/admin/ReportListScreen';
import ReportDetailScreen from '../screens/admin/ReportDetailScreen';

const opts = { headerShown: false, animation: 'slide_from_right' as const };
const S = createNativeStackNavigator();

export function HomeStack() {
  return (
    <S.Navigator screenOptions={opts}>
      <S.Screen name="QuestHome" component={QuestHome} />
      <S.Screen name="QuestDetail" component={QuestDetailScreen} />
      <S.Screen name="QuestVerify" component={QuestVerifyScreen} options={{ presentation: 'transparentModal', animation: 'fade' }} />
      <S.Screen name="QuestChallenge" component={QuestChallengeScreen} />
      <S.Screen name="QuestComplete" component={QuestCompleteScreen} options={{ animation: 'fade' }} />
      <S.Screen name="QuestRegister" component={QuestRegisterScreen} />
      <S.Screen name="AiRecommend" component={AiRecommendScreen} />
    </S.Navigator>
  );
}

export function CommunityStack() {
  return (
    <S.Navigator screenOptions={opts}>
      <S.Screen name="Feed" component={FeedScreen} />
      <S.Screen name="NewPost" component={NewPostScreen} />
      {/* 커뮤니티 상단 "팀 챌린지" 탭 진입점 — 뒤로가기 시 Feed 복귀 (TeamStack은 별도) */}
      <S.Screen name="TeamHome" component={TeamHomeScreen} />
    </S.Navigator>
  );
}

export function ShopStack() {
  return (
    <S.Navigator screenOptions={opts}>
      <S.Screen name="Shop" component={ShopScreen} />
      <S.Screen name="ItemDetail" component={ItemDetailScreen} />
      <S.Screen name="PurchaseHistory" component={PurchaseHistoryScreen} />
      <S.Screen name="Inventory" component={InventoryScreen} />
    </S.Navigator>
  );
}

export function MapStack() {
  return (
    <S.Navigator screenOptions={opts}>
      <S.Screen name="Map" component={MapScreen} />
      <S.Screen name="Ranking" component={RankingScreen} />
      <S.Screen name="Nearby" component={NearbyScreen} />
      <S.Screen name="VolunteerDetail" component={VolunteerDetailScreen} />
    </S.Navigator>
  );
}

export function MyStack() {
  return (
    <S.Navigator screenOptions={opts}>
      <S.Screen name="MyPage" component={MyPageScreen} />
      <S.Screen name="Level" component={LevelScreen} />
      <S.Screen name="Rank" component={RankScreen} />
      <S.Screen name="ItemList" component={ItemListScreen} />
    </S.Navigator>
  );
}

export function TeamStack() {
  return (
    <S.Navigator screenOptions={opts}>
      <S.Screen name="TeamHome" component={TeamHomeScreen} />
      <S.Screen name="RoomFind" component={RoomFindScreen} />
      <S.Screen name="TeamDetail" component={TeamDetailScreen} />
      <S.Screen name="TeamList" component={TeamListScreen} />
    </S.Navigator>
  );
}

export function ShortformStack() {
  return (
    <S.Navigator screenOptions={opts}>
      <S.Screen name="PhotoSelect" component={PhotoSelectScreen} />
      <S.Screen name="Generating" component={GeneratingScreen} options={{ animation: 'fade' }} />
      <S.Screen name="Player" component={PlayerScreen} />
    </S.Navigator>
  );
}

export function AdminStack() {
  return (
    <S.Navigator screenOptions={opts}>
      <S.Screen name="Dashboard" component={DashboardScreen} />
      <S.Screen name="UserList" component={UserListScreen} />
      <S.Screen name="ReportList" component={ReportListScreen} />
      <S.Screen name="ReportDetail" component={ReportDetailScreen} />
    </S.Navigator>
  );
}
