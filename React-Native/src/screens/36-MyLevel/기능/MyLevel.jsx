// 36-MyLevel.js — React Native (Expo) 마이레벨 페이지
// 선행퀘스트 / 스토리보드 36번 기준 — 경험치바 + 레벨추이(주간/월간) + 랭킹 보러가기

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft } from 'lucide-react-native';
import Svg, { Line, Polyline, Polygon, Circle, Defs, LinearGradient as SvgLinearGradient, Stop } from 'react-native-svg';

import { COLORS } from '../../../shared/디자인/tokens';
import { GreenGradientBG } from '../../../shared/기능/components';
import { styles } from '../디자인/MyLevel.styles';

const WEEKLY = [3, 5, 4, 7, 6, 9, 12];
const WEEKLY_LABELS = ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7'];
const MONTHLY = [4, 6, 5, 8, 7, 10, 9];
const MONTHLY_LABELS = ['1월', '2월', '3월', '4월', '5월', '6월', '7월'];

export default function MyLevelScreen({ navigation }) {
  const [range, setRange] = useState('weekly');
  const data = range === 'weekly' ? WEEKLY : MONTHLY;
  const labels = range === 'weekly' ? WEEKLY_LABELS : MONTHLY_LABELS;

  const max = Math.max(...data);
  const w = 280, h = 130, pad = 6;
  const stepX = w / (data.length - 1);
  const points = data.map((v, i) => ({
    x: i * stepX,
    y: pad + (h - pad * 2) * (1 - v / (max || 1)),
  }));
  const polylinePoints = points.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
  const areaPoints = `0,${h} ` + points.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ') + ` ${w},${h}`;

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate('MyPage')} hitSlop={10} style={{ padding: 4 }}>
            <ChevronLeft size={22} color={COLORS.ink} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>마이 레벨</Text>
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.profileCard}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>민</Text>
            </View>
            <View style={{ gap: 4 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <Text style={styles.nickname}>민선행</Text>
                <View style={styles.titleTag}>
                  <Text style={styles.titleTagText}>따뜻한 이웃</Text>
                </View>
              </View>
              <View style={styles.levelTag}>
                <Text style={styles.levelTagText}>Lv.12</Text>
              </View>
            </View>
          </View>

          <View style={styles.card}>
            <View style={{ flexDirection: 'row', alignItems: 'baseline', justifyContent: 'space-between' }}>
              <Text style={styles.cardTitle}>경험치</Text>
              <Text style={styles.expText}>1,240 / 1,500 EXP</Text>
            </View>
            <View style={styles.expBarTrack}>
              <View style={[styles.expBarFill, { width: `${Math.round((1240 / 1500) * 100)}%` }]} />
            </View>
            <Text style={styles.expHint}>다음 레벨까지 260 EXP 남았어요</Text>
          </View>

          <View style={{ gap: 12 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
              <Text style={styles.cardTitle}>레벨 추이</Text>
              <View style={{ flexDirection: 'row', gap: 6 }}>
                <TouchableOpacity style={[styles.tab, range === 'weekly' && styles.tabActive]} onPress={() => setRange('weekly')}>
                  <Text style={[styles.tabText, range === 'weekly' && styles.tabTextActive]}>주간</Text>
                </TouchableOpacity>
                <TouchableOpacity style={[styles.tab, range === 'monthly' && styles.tabActive]} onPress={() => setRange('monthly')}>
                  <Text style={[styles.tabText, range === 'monthly' && styles.tabTextActive]}>월간</Text>
                </TouchableOpacity>
              </View>
            </View>

            <View style={styles.card}>
              <Svg viewBox={`0 0 ${w} ${h}`} width="100%" height={130}>
                <Line x1="0" y1="0" x2={w} y2="0" stroke="rgba(0,0,0,0.06)" />
                <Line x1="0" y1="43" x2={w} y2="43" stroke="rgba(0,0,0,0.06)" />
                <Line x1="0" y1="86" x2={w} y2="86" stroke="rgba(0,0,0,0.06)" />
                <Defs>
                  <SvgLinearGradient id="lvlGrad" x1="0" y1="0" x2="0" y2="1">
                    <Stop offset="0%" stopColor={COLORS.mint} stopOpacity={0.6} />
                    <Stop offset="100%" stopColor={COLORS.mint} stopOpacity={0} />
                  </SvgLinearGradient>
                </Defs>
                <Polygon points={areaPoints} fill="url(#lvlGrad)" opacity={0.5} />
                <Polyline points={polylinePoints} fill="none" stroke={COLORS.primary} strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" />
                {points.map((p, i) => (
                  <Circle key={i} cx={p.x} cy={p.y} r={3.5} fill="#fff" stroke={COLORS.primary} strokeWidth={2} />
                ))}
              </Svg>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', paddingTop: 8 }}>
                {labels.map((l, i) => (
                  <Text key={i} style={styles.chartLabel}>
                    {l}
                  </Text>
                ))}
              </View>
            </View>
          </View>

          <TouchableOpacity style={styles.rankingButton} onPress={() => navigation.navigate('MyRanking')}>
            <Text style={styles.rankingButtonText}>랭킹 보러가기</Text>
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>
    </GreenGradientBG>
  );
}

