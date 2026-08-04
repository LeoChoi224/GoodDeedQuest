/**
 * SCREEN 2 & 3 · 퀘스트 상세 (route QuestDetail) — 진행 전(idle)/진행 중(active).
 * RPG 퀘스트 카드(<QuestCard/> 재사용).
 * "퀘스트 시작" → iris/scale 와이프 트랜지션 후 active 전환. "퀘스트 인증" → QuestVerify.
 * "퀘스트 포기" → 확인 후 DELETE /quests/{id}.
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert, Pressable, ActivityIndicator } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { colors, fonts, radii } from '../../theme';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import QuestCard from '../../components/QuestCard';
import { SwordIcon } from '../../components/PixelIcons';
import { CameraIcon, StartTransition } from './_parts';
import { abandonQuest, startQuest } from '../../api/quest';
import { getVolunteerCenter } from '../../api/map';


const DEFAULT_DESC =
  '집 근처 공원을 돌며 쓰레기를 주워 봉투에 담아 주세요. 30분 이상 활동하고 인증하면 보상을 받아요.';

export default function QuestDetailScreen({ navigation, route }: any) {
  const insets = useSafeAreaInsets();
  const p = route?.params ?? {};
  const questId = p.questId;
  const volunteerCenterId = p.volunteerCenterId ?? null;
  const questType = p.questType ?? 'GOOD_DEED';
  const title = p.title ?? '공원 플로깅';
  const category = p.category ?? 'environment';
  const desc = p.desc ?? DEFAULT_DESC;
  const point = p.point ?? 250;
  const exp = p.exp ?? 100;
  const [active, setActive] = useState<boolean>(!!p.active);
  const [starting, setStarting] = useState(false);
  const [abandoning, setAbandoning] = useState(false);
  const [openingCenter, setOpeningCenter] = useState(false);

    const onStart = async () => {
    if (starting || active) return;

    // questId가 없으면 서버에 남길 방법이 없다. 조용히 넘어가면 화면만 진행중으로
    // 바뀌고 홈에는 반영되지 않아 원인을 찾기 어렵다. 실패로 처리해 드러낸다.
    if (!questId) {
      Alert.alert('시작하지 못했어요', '퀘스트 정보를 불러오지 못했습니다.');
      return;
    }

    // 애니메이션을 먼저 돌리면 사용자는 시작됐다고 믿는데 서버엔 안 남을 수 있다.
    // 요청이 짧아 순서를 바꿔도 체감 차이가 없으므로 서버를 먼저 부른다.
    try {
      await startQuest(questId);
    } catch (err: any) {
      Alert.alert('시작하지 못했어요', '잠시 후 다시 시도해 주세요.');
      return;
    }
    setStarting(true);
  };

  const onAbandon = () => {
    if (abandoning || !questId) return;
    Alert.alert(
      '퀘스트를 포기할까요?',
      '내가 만든 퀘스트면 모두에게서 사라지고, 그 외에는 내 목록에서만 사라져요.',
      [
        { text: '취소', style: 'cancel' },
        {
          text: '포기하기',
          style: 'destructive',
          onPress: async () => {
            setAbandoning(true);
            try {
              await abandonQuest(questId);
              navigation.goBack();
            } catch (err: any) {
              setAbandoning(false);
              Alert.alert('포기하지 못했어요', '잠시 후 다시 시도해 주세요.');
            }
          },
        },
      ],
    );
  };

  // 봉사 퀘스트의 제목·설명은 LLM이 원본 공고를 다듬은 것이다.
  // 모집 일정·자격·신청 링크 같은 실제 참여 정보는 원본에만 있으므로 여기로 보낸다.
  const openVolunteerDetail = async () => {
    if (openingCenter || !volunteerCenterId) return;
    setOpeningCenter(true);
    try {
      const center = await getVolunteerCenter(volunteerCenterId);
      // VolunteerDetailScreen은 같은 기관의 공고 여러 건을 카드로 나열하도록 만들어져 있다.
      // 한 건만 보낼 때도 배열이어야 그 로직을 그대로 탄다.
      navigation.navigate('QuestVolunteerDetail', {
        items: [center],
        place: center.vol_name,
        address: center.vol_address,
        latitude: center.latitude,
        longitude: center.longitude,
      });
    } catch (err: any) {
      Alert.alert('공고를 불러오지 못했어요', '잠시 후 다시 시도해 주세요.');
    } finally {
      setOpeningCenter(false);
    }
  };

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title="퀘스트 상세" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={[styles.body, { paddingBottom: 130 }]} showsVerticalScrollIndicator={false}>
        <QuestCard
          category={category}
          mode={active ? 'active' : 'idle'}
          title={title}
          desc={desc}
          point={point}
          exp={exp}
          showDesc
        />
      </ScrollView>

      {/* pinned footer */}
      <LinearGradient
        colors={['rgba(243,250,244,0)', '#F3FAF4']}
        locations={[0, 0.35]}
        style={[styles.footer, { paddingBottom: insets.bottom + 20 }]}
      >
                {active ? (
          <>
            <SpringButton
              onPress={() => navigation.navigate('QuestVerify', { questId, questType, title, exp, point })}
              style={styles.ctaWrap}
            >
              <LinearGradient colors={['#0A4F55', colors.primaryDark]} start={{ x: 0.5, y: 0 }} end={{ x: 0.5, y: 1 }} style={styles.ctaGrad}>
                <CameraIcon />
                <Text style={styles.ctaText}>퀘스트 인증</Text>
              </LinearGradient>
            </SpringButton>

            {/* 인증에 VMS 확인서가 필요해서 진행중에도 원본 공고를 다시 열 일이 있다 */}
            {volunteerCenterId ? (
              <Pressable onPress={openVolunteerDetail} disabled={openingCenter} style={styles.subLinkWrap} hitSlop={8}>
                <Text style={[styles.subLinkText, openingCenter && styles.subLinkTextOff]}>
                  {openingCenter ? '불러오는 중…' : '봉사활동 상세 보기'}
                </Text>
              </Pressable>
            ) : null}
          </>
        ) : volunteerCenterId ? (
          // 봉사는 앱에서 '시작'해도 실제 참여가 아니다. VMS 신청이 먼저라서
          // 원본 공고를 넓게 두고 시작은 옆에 붙인다.
          <View style={styles.dualRow}>
            <SpringButton onPress={openVolunteerDetail} disabled={openingCenter} style={[styles.ctaWrap, styles.dualPrimary]}>
              <LinearGradient colors={['#D4A017', '#B8860B']} start={{ x: 0.5, y: 0 }} end={{ x: 0.5, y: 1 }} style={styles.ctaGrad}>
                <Text style={styles.ctaText}>{openingCenter ? '불러오는 중…' : '봉사활동 상세'}</Text>
              </LinearGradient>
            </SpringButton>

            <SpringButton onPress={onStart} style={[styles.ctaWrap, styles.dualSecondary]}>
              <LinearGradient colors={['#0A4F55', colors.primaryDark]} start={{ x: 0.5, y: 0 }} end={{ x: 0.5, y: 1 }} style={styles.ctaGrad}>
                <SwordIcon size={18} />
                <Text style={styles.ctaText}>퀘스트 시작</Text>
              </LinearGradient>
            </SpringButton>
          </View>
        ) : (
          <SpringButton onPress={onStart} style={styles.ctaWrap}>
            <LinearGradient colors={['#0A4F55', colors.primaryDark]} start={{ x: 0.5, y: 0 }} end={{ x: 0.5, y: 1 }} style={styles.ctaGrad}>
              <SwordIcon size={18} />
              <Text style={styles.ctaText}>퀘스트 시작</Text>
            </LinearGradient>
          </SpringButton>
        )}

        {/* 포기는 진행중인 퀘스트에만 해당한다 */}
        {active && questId ? (
          <Pressable onPress={onAbandon} disabled={abandoning} style={styles.abandonWrap} hitSlop={8}>
            <Text style={[styles.abandonText, abandoning && styles.abandonTextOff]}>
              {abandoning ? '포기하는 중…' : '퀘스트 포기'}
            </Text>
          </Pressable>
        ) : null}
      </LinearGradient>

      {starting ? (
        <StartTransition
          onDone={() => {
            setStarting(false);
            setActive(true);
          }}
        />
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 16, paddingTop: 22 },

  abandonWrap: { alignItems: 'center', paddingTop: 14 },
  abandonText: { fontSize: 14, color: colors.textMuted, fontFamily: fonts.bodyR, textDecorationLine: 'underline' },
  abandonTextOff: { opacity: 0.5 },

  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, paddingHorizontal: 20, paddingTop: 16 },
  ctaWrap: {
    borderRadius: radii.button,
    borderWidth: 2,
    borderColor: '#C9A44C',
    shadowColor: colors.primaryDark,
    shadowOffset: { width: 0, height: 5 },
    shadowOpacity: 0.35,
    shadowRadius: 16,
    elevation: 6,
  },
  ctaGrad: { height: 54, borderRadius: radii.button - 2, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9 },
  ctaText: { color: '#F5EFD8', fontSize: 16, fontWeight: '700', fontFamily: fonts.bodyB },
  dualRow: { flexDirection: 'row', gap: 10 },
  dualPrimary: { flex: 1.3 },
  dualSecondary: { flex: 1 },

  subLinkWrap: { alignItems: 'center', paddingTop: 12 },
  subLinkText: { fontSize: 14, color: colors.primaryDark, fontFamily: fonts.bodyB, textDecorationLine: 'underline' },
  subLinkTextOff: { opacity: 0.5 },
});
