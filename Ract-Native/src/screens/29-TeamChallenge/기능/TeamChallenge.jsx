// 29-TeamChallenge.js — React Native (Expo) 팀 챌린지 (방 찾기 / 방 만들기 선택)
// 선행퀘스트 / 스토리보드 29번 기준

import React from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, Plus, Search, ChevronRight } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { CareIcon, GreenGradientBG } from '../../../shared/기능/components';
import { styles } from '../디자인/TeamChallenge.styles';

export default function TeamChallengeScreen({ navigation }) {
  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate('Community')} hitSlop={10} style={{ padding: 4 }}>
            <ChevronLeft size={22} color={COLORS.ink} />
          </TouchableOpacity>
          <View style={styles.logoBadge}>
            <CareIcon size={18} />
          </View>
          <Text style={styles.logo}>선·퀘</Text>
        </View>

        <View style={styles.content}>
          <View>
            <Text style={styles.title}>팀 챌린지</Text>
            <Text style={styles.subtitle}>함께 선행 퀘스트를 수행할 팀을 만들거나 찾아보세요</Text>
          </View>

          <View style={{ gap: 14 }}>
            <TouchableOpacity style={styles.optionCard} onPress={() => navigation.navigate('RoomCreate')}>
              <View style={styles.optionIcon}>
                <Plus size={22} color="#fff" />
              </View>
              <View style={{ flex: 1, minWidth: 0, gap: 4 }}>
                <Text style={styles.optionTitle}>방 만들기</Text>
                <Text style={styles.optionDesc}>새로운 팀 챌린지 방을 만들고 팀원을 모아보세요</Text>
              </View>
              <ChevronRight size={18} color={COLORS.inkMuted48} />
            </TouchableOpacity>

            <TouchableOpacity style={styles.optionCard} onPress={() => navigation.navigate('RoomFind')}>
              <View style={styles.optionIcon}>
                <Search size={22} color="#fff" />
              </View>
              <View style={{ flex: 1, minWidth: 0, gap: 4 }}>
                <Text style={styles.optionTitle}>방 찾기</Text>
                <Text style={styles.optionDesc}>진행 중인 팀 챌린지에 참여해보세요</Text>
              </View>
              <ChevronRight size={18} color={COLORS.inkMuted48} />
            </TouchableOpacity>
          </View>
        </View>
      </SafeAreaView>
    </GreenGradientBG>
  );
}

