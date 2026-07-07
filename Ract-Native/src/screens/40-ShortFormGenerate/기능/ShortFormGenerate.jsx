// 40-ShortFormGenerate.js — React Native (Expo) 영상 생성 및 다운로드
// 선행퀘스트 / 스토리보드 40번 기준 — 생성중 스피너+진행바 → 완성 미리보기 → 다운로드

import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, ScrollView, Animated, Easing } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, Play, Download } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { GreenGradientBG, BottomNav, HamburgerMenu, HamburgerButton } from '../../../shared/기능/components';
import { styles } from '../디자인/ShortFormGenerate.styles';

export default function ShortFormGenerateScreen({ navigation, route }) {
  const auto = !!route?.params?.auto;
  const [menuVisible, setMenuVisible] = useState(false);
  const [progress, setProgress] = useState(0);
  const [isGenerating, setIsGenerating] = useState(true);
  const [toast, setToast] = useState('');
  const toastTimer = useRef(null);
  const spin = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const spinLoop = Animated.loop(Animated.timing(spin, { toValue: 1, duration: 900, easing: Easing.linear, useNativeDriver: true }));
    spinLoop.start();
    const timer = setInterval(() => {
      setProgress((p) => {
        const next = Math.min(100, p + 8 + Math.random() * 10);
        if (next >= 100) {
          clearInterval(timer);
          setTimeout(() => setIsGenerating(false), 300);
        }
        return next;
      });
    }, 260);
    return () => {
      clearInterval(timer);
      spinLoop.stop();
      clearTimeout(toastTimer.current);
    };
  }, []);

  const rotate = spin.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '360deg'] });
  const scriptPreview = auto ? 'AI가 자동으로 대본을 작성했어요' : '오늘도 작은 선행 하나가 세상을 조금 더 따뜻하게 만들었어요';
  const trackName = auto ? '희망찬 발걸음' : '잔잔한 오후';

  const onDownload = () => {
    clearTimeout(toastTimer.current);
    setToast('영상이 다운로드됐어요');
    toastTimer.current = setTimeout(() => setToast(''), 1600);
  };

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate('ShortFormCreate')} hitSlop={10} style={{ padding: 4 }}>
            <ChevronLeft size={22} color={COLORS.ink} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>영상 생성</Text>
          <View style={{ flex: 1 }} />
          <HamburgerButton onPress={() => setMenuVisible(true)} />
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <View>
            <Text style={styles.title}>{isGenerating ? '영상을 만들고 있어요' : '숏폼이 완성됐어요'}</Text>
            <Text style={styles.subtitle}>{isGenerating ? '대본과 음악을 반영해 자동으로 생성 중이에요' : '확인하고 핸드폰에 저장해보세요'}</Text>
          </View>

          <View style={styles.preview}>
            {isGenerating ? (
              <Animated.View style={[styles.spinner, { transform: [{ rotate }] }]} />
            ) : (
              <View style={{ alignItems: 'center', gap: 10 }}>
                <View style={styles.playButton}>
                  <Play size={26} color="#fff" fill="#fff" />
                </View>
                <Text style={styles.playHint}>탭하여 재생</Text>
              </View>
            )}
            <View style={styles.previewCaption}>
              <Text style={styles.previewScript}>{scriptPreview}</Text>
              <Text style={styles.previewTrack}>🎵 {trackName}</Text>
            </View>
          </View>

          {isGenerating ? (
            <View style={{ gap: 10 }}>
              <View style={styles.progressTrack}>
                <View style={[styles.progressFill, { width: `${Math.round(progress)}%` }]} />
              </View>
              <Text style={styles.progressLabel}>영상 생성 중 · {Math.round(progress)}%</Text>
            </View>
          ) : (
            <View style={styles.summaryCard}>
              <SummaryRow label="사용 사진" value="3장" />
              <View style={styles.divider} />
              <SummaryRow label="배경 음악" value={trackName} />
              <View style={styles.divider} />
              <SummaryRow label="영상 길이" value="00:18" />
            </View>
          )}
        </ScrollView>

        {!isGenerating && (
          <View style={styles.footer}>
            <TouchableOpacity style={styles.downloadButton} onPress={onDownload}>
              <Download size={17} color="#fff" />
              <Text style={styles.downloadButtonText}>다운로드</Text>
            </TouchableOpacity>
          </View>
        )}

        <BottomNav navigation={navigation} active="community" translucent />
        <HamburgerMenu visible={menuVisible} onClose={() => setMenuVisible(false)} navigation={navigation} />

        {!!toast && (
          <View style={styles.toast}>
            <Text style={styles.toastText}>{toast}</Text>
          </View>
        )}
      </SafeAreaView>
    </GreenGradientBG>
  );
}

function SummaryRow({ label, value }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
      <Text style={styles.summaryLabel}>{label}</Text>
      <Text style={styles.summaryValue}>{value}</Text>
    </View>
  );
}

