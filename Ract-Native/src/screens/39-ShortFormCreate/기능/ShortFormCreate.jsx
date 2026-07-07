// 39-ShortFormCreate.js — React Native (Expo) 숏폼 제작 (사진/AI대본/음악 선택)
// 선행퀘스트 / 스토리보드 39번 기준 — 46/47/48/49는 이 화면의 팝업 상태들과 동일하게 통합

import React, { useState, useRef } from 'react';
import { View, Text, TextInput, TouchableOpacity, ScrollView, Modal, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ChevronLeft, FileText, Music, Check, X } from 'lucide-react-native';

import { COLORS } from '../../../shared/디자인/tokens';
import { GreenGradientBG, BottomNav, HamburgerMenu, HamburgerButton } from '../../../shared/기능/components';
import { styles } from '../디자인/ShortFormCreate.styles';

const PHOTO_DATES = ['3.02 봉사', '3.15 봉사', '3.28 봉사', '4.02 봉사', '4.11 봉사', '4.20 봉사'];
const TRACKS = [
  { id: 't1', name: '잔잔한 오후', desc: '어쿠스틱 · 따뜻한 분위기' },
  { id: 't2', name: '희망찬 발걸음', desc: '팝 · 경쾌한 분위기' },
  { id: 't3', name: '고요한 다짐', desc: '피아노 · 잔잔한 분위기' },
];

export default function ShortFormCreateScreen({ navigation }) {
  const [menuVisible, setMenuVisible] = useState(false);
  const [selected, setSelected] = useState({ p1: true, p2: true, p3: false, p4: true, p5: false, p6: false });
  const [scriptOpen, setScriptOpen] = useState(false);
  const [musicOpen, setMusicOpen] = useState(false);
  const [scriptText, setScriptText] = useState('오늘도 작은 선행 하나가 세상을 조금 더 따뜻하게 만들었어요.');
  const [scriptSaved, setScriptSaved] = useState('');
  const [selectedTrack, setSelectedTrack] = useState(null);
  const [toast, setToast] = useState('');
  const toastTimer = useRef(null);

  const showToast = (text) => {
    clearTimeout(toastTimer.current);
    setToast(text);
    toastTimer.current = setTimeout(() => setToast(''), 1600);
  };

  const togglePhoto = (key) => setSelected((s) => ({ ...s, [key]: !s[key] }));
  const selectedCount = Object.values(selected).filter(Boolean).length;

  const onSaveScript = () => {
    setScriptSaved(scriptText);
    setScriptOpen(false);
    showToast('대본이 저장됐어요');
  };

  const onSelectTrack = (t) => {
    setSelectedTrack(t.id);
    setMusicOpen(false);
    showToast('음악이 선택됐어요');
  };

  const goGenerate = (auto) => {
    if (selectedCount === 0 && !auto) {
      showToast('사진을 1장 이상 선택해주세요');
      return;
    }
    navigation.navigate('ShortFormGenerate', { auto });
  };

  return (
    <GreenGradientBG>
      <SafeAreaView style={{ flex: 1, backgroundColor: 'transparent' }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.navigate('Community')} hitSlop={10} style={{ padding: 4 }}>
            <ChevronLeft size={22} color={COLORS.ink} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>숏폼 제작</Text>
          <View style={{ flex: 1 }} />
          <HamburgerButton onPress={() => setMenuVisible(true)} />
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <View>
            <Text style={styles.title}>인증샷으로 숏폼 만들기</Text>
            <Text style={styles.subtitle}>사용할 사진을 고르고 대본·음악을 설정해보세요</Text>
          </View>

          <View style={{ flexDirection: 'row', gap: 8 }}>
            <TouchableOpacity style={styles.tabButton} onPress={() => setScriptOpen(true)}>
              <FileText size={16} color={COLORS.primary} />
              <Text style={styles.tabButtonText}>AI 대본</Text>
              {!!scriptSaved && <View style={styles.dot} />}
            </TouchableOpacity>
            <TouchableOpacity style={styles.tabButton} onPress={() => setMusicOpen(true)}>
              <Music size={16} color={COLORS.primary} />
              <Text style={styles.tabButtonText}>음악</Text>
              {!!selectedTrack && <View style={styles.dot} />}
            </TouchableOpacity>
          </View>

          <View style={{ gap: 10 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
              <Text style={styles.sectionLabel}>인증한 사진 선택</Text>
              <Text style={styles.countLabel}>{selectedCount}장 선택됨</Text>
            </View>
            <View style={styles.photoGrid}>
              {PHOTO_DATES.map((d, i) => {
                const key = 'p' + (i + 1);
                const isSel = selected[key];
                return (
                  <TouchableOpacity key={key} style={[styles.photoTile, isSel && { borderColor: COLORS.primary }]} onPress={() => togglePhoto(key)}>
                    <Text style={styles.photoPlaceholder}>사진 {i + 1}</Text>
                    {isSel && (
                      <View style={styles.checkBadge}>
                        <Check size={13} color="#fff" strokeWidth={3} />
                      </View>
                    )}
                    <View style={styles.photoDateBar}>
                      <Text style={styles.photoDateText}>{d}</Text>
                    </View>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>
        </ScrollView>

        <View style={styles.footer}>
          <TouchableOpacity style={styles.generateButton} onPress={() => goGenerate(false)}>
            <Text style={styles.generateButtonText}>생성하기</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.autoButton} onPress={() => goGenerate(true)}>
            <Text style={styles.autoButtonText}>자동 생성</Text>
          </TouchableOpacity>
        </View>

        <BottomNav navigation={navigation} active="community" translucent />
        <HamburgerMenu visible={menuVisible} onClose={() => setMenuVisible(false)} navigation={navigation} />

        {!!toast && (
          <View style={styles.toast}>
            <Text style={styles.toastText}>{toast}</Text>
          </View>
        )}

        {/* AI 대본 팝업 */}
        <Modal statusBarTranslucent visible={scriptOpen} transparent animationType="slide" onRequestClose={() => setScriptOpen(false)}>
          <View style={styles.sheetOverlay}>
            <Pressable style={{ flex: 1 }} onPress={() => setScriptOpen(false)} />
            <View style={styles.sheet}>
              <View style={styles.sheetHeaderRow}>
                <Text style={styles.sheetTitle}>AI 대본</Text>
                <TouchableOpacity onPress={() => setScriptOpen(false)} hitSlop={8}>
                  <X size={20} color={COLORS.ink} />
                </TouchableOpacity>
              </View>
              <TextInput style={styles.scriptInput} value={scriptText} onChangeText={setScriptText} multiline textAlignVertical="top" />
              <TouchableOpacity style={styles.saveButton} onPress={onSaveScript}>
                <Text style={styles.saveButtonText}>저장</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>

        {/* 음악 선택 팝업 */}
        <Modal statusBarTranslucent visible={musicOpen} transparent animationType="slide" onRequestClose={() => setMusicOpen(false)}>
          <View style={styles.sheetOverlay}>
            <Pressable style={{ flex: 1 }} onPress={() => setMusicOpen(false)} />
            <View style={styles.sheet}>
              <View style={styles.sheetHeaderRow}>
                <Text style={styles.sheetTitle}>음악 선택</Text>
                <TouchableOpacity onPress={() => setMusicOpen(false)} hitSlop={8}>
                  <X size={20} color={COLORS.ink} />
                </TouchableOpacity>
              </View>
              <View style={{ gap: 10 }}>
                {TRACKS.map((t) => {
                  const isSel = selectedTrack === t.id;
                  return (
                    <View key={t.id} style={[styles.trackRow, isSel && { borderColor: COLORS.primary }]}>
                      <View style={{ flex: 1, gap: 3 }}>
                        <Text style={styles.trackName}>{t.name}</Text>
                        <Text style={styles.trackDesc}>{t.desc}</Text>
                        <TouchableOpacity onPress={() => showToast(t.name + ' 미리듣기 재생 중')}>
                          <Text style={styles.previewLink}>미리듣기</Text>
                        </TouchableOpacity>
                      </View>
                      <TouchableOpacity style={[styles.selectTrackButton, isSel && { backgroundColor: COLORS.primary, borderColor: COLORS.primary }]} onPress={() => onSelectTrack(t)}>
                        <Text style={[styles.selectTrackText, isSel && { color: '#fff' }]}>{isSel ? '선택됨' : '선택'}</Text>
                      </TouchableOpacity>
                    </View>
                  );
                })}
              </View>
            </View>
          </View>
        </Modal>
      </SafeAreaView>
    </GreenGradientBG>
  );
}

