/**
 * SCREEN 04-2/3 · 아이템 상세 + 구매 확인 팝업 (back). 상단 3D tilt 히어로(pan → rotateX/Y,
 * 놓으면 스프링 복귀), 가격/설명 카드, 하단 고정 "아이템 구매" 버튼. 구매 → GamePopup
 * "구매 하시겠습니까?" → 예: 처리(픽셀 스피너) → Toast "구매 완료 🎉" + 구매 내역 이동.
 * 상태: 포인트 부족 / 이미 구매 시 버튼 비활성.
 */
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LinearGradient } from 'expo-linear-gradient';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import Animated, {
  FadeInDown,
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withRepeat,
  withTiming,
  Easing,
} from 'react-native-reanimated';
import HazeBackground from '../../components/HazeBackground';
import MainHeader from '../../components/MainHeader';
import SpringButton from '../../components/SpringButton';
import GamePopup, { PopupButtons } from '../../components/GamePopup';
import { useToast } from '../../components/Toast';
import { colors, fonts, shadow, spring, gamePopup } from '../../theme';
import { ShopItem, PixelCoin, POINTS_NUM } from './_parts';
import { purchaseShopItem, getItemDetail } from '../../api/shop';

export default function ItemDetailScreen({ navigation, route }: any) {
  const toast = useToast();
  
  // 전달받은 라우트 파라미터 파싱
  const routeItem: ShopItem = route?.params?.item;
  const routeItemId: number = route?.params?.itemId ?? routeItem?.item_id ?? 1;

  const [item, setItem] = useState<ShopItem>(
    routeItem || {
      item_id: routeItemId,
      name: '프로필 테두리',
      description: '상세 설명을 불러오는 중입니다.',
      price_point: 1000,
      image_url: '',
      is_active: true,
      is_equipped: false,
      created_at: '',
      updated_at: '',
      c1: '#4A90E2',
      c2: '#50E3C2',
      emoji: '🖼️',
      price: '1,000',
      priceNum: 1000,
      desc: '선행을 실천하여 획득할 수 있는 프로필 테두리입니다.',
    }
  );

  const owned: boolean = route?.params?.owned ?? item?.is_equipped ?? false;
  const [confirm, setConfirm] = useState(false);
  const [processing, setProcessing] = useState(false);

  // 백엔드 데이터 상세 동기화
  useEffect(() => {
    if (routeItemId) {
      getItemDetail(routeItemId)
        .then((data) => {
          setItem((prev) => ({ ...prev, ...data }));
        })
        .catch((err) => {
          console.log('단일 상세 조회  fallback:', err);
        });
    }
  }, [routeItemId]);

  const priceNum = item.price_point ?? (item as any).priceNum ?? 1000;
  const affordable = priceNum <= POINTS_NUM;
  const canBuy = affordable && !owned;
  const buyLabel = owned ? '이미 구매한 아이템이에요' : !affordable ? '포인트가 부족해요' : '아이템 구매';

  // ── 3D tilt (pan → rotateX / rotateY) ──
  const rx = useSharedValue(0);
  const ry = useSharedValue(0);
  const w = useSharedValue(1);
  const H = 220;

  const tilt = Gesture.Pan()
    .minDistance(0)
    .onBegin((e) => {
      rx.value = -((e.y / H) - 0.5) * 14;
      ry.value = ((e.x / w.value) - 0.5) * 14;
    })
    .onUpdate((e) => {
      rx.value = -((e.y / H) - 0.5) * 14;
      ry.value = ((e.x / w.value) - 0.5) * 14;
    })
    .onFinalize(() => {
      rx.value = withSpring(0, spring.press);
      ry.value = withSpring(0, spring.press);
    });

  const tiltStyle = useAnimatedStyle(() => ({
    transform: [
      { perspective: 800 },
      { rotateX: `${rx.value}deg` },
      { rotateY: `${ry.value}deg` },
    ],
  }));

  // 백엔드 구매 API (`POST /api/v1/shop/purchase`) 연동 핸들러
  const onConfirmYes = async () => {
    if (processing) return;
    setProcessing(true);

    try {
      await purchaseShopItem(item.item_id || routeItemId);
      setProcessing(false);
      setConfirm(false);
      toast.show('구매 완료 🎉');
      navigation.navigate('PurchaseHistory');
    } catch (error: any) {
      setProcessing(false);
      setConfirm(false);

      // 백엔드 예외 처리 (중복 구매 방지 400 Bad Request / 포인트 잔액 부족 400 Bad Request)
      const detailMsg =
        error.response?.data?.detail || error.message || '구매 도중 오류가 발생했습니다.';

      toast.show(`구매 실패: ${detailMsg}`);
      Alert.alert('구매 불가', detailMsg);
    }
  };

  const itemC1 = (item as any).c1 || '#4A90E2';
  const itemC2 = (item as any).c2 || '#50E3C2';
  const itemEmoji = (item as any).emoji || '🖼️';
  const itemDesc = item.description || (item as any).desc || '';
  const itemPriceFormatted = (item.price_point || (item as any).priceNum || 1000).toLocaleString();

  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <HazeBackground />
      <MainHeader showBack title="아이템 상세" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
        {/* tilt hero */}
        <View style={styles.perspective}>
          <GestureDetector gesture={tilt}>
            <Animated.View
              onLayout={(e) => (w.value = e.nativeEvent.layout.width)}
              style={[styles.hero, tiltStyle]}
            >
              <LinearGradient colors={[itemC1, itemC2]} start={{ x: 0.5, y: 0.05 }} end={{ x: 0.5, y: 1 }} style={StyleSheet.absoluteFill} />
              <Text style={styles.heroEmoji}>{itemEmoji}</Text>
            </Animated.View>
          </GestureDetector>
        </View>

        {/* info card */}
        <Animated.View entering={FadeInDown.delay(80).duration(420)} style={styles.infoCard}>
          <Text style={styles.name}>{item.name}</Text>
          <Text style={styles.desc}>{itemDesc}</Text>
          <View style={styles.priceRow}>
            <PixelCoin size={16} />
            <Text style={styles.priceText}>가격 : {itemPriceFormatted} P</Text>
          </View>
        </Animated.View>
      </ScrollView>

      {/* pinned buy button */}
      <LinearGradient colors={['rgba(245,251,246,0)', '#F3FAF4']} locations={[0, 0.35]} style={styles.footer}>
        <SpringButton
          style={[styles.buyBtn, !canBuy && styles.buyBtnDisabled]}
          disabled={!canBuy}
          pressScale={0.96}
          onPress={() => setConfirm(true)}
        >
          <Text style={styles.buyText}>{buyLabel}</Text>
        </SpringButton>
      </LinearGradient>

      {/* purchase confirm popup */}
      <GamePopup
        visible={confirm}
        onClose={() => (processing ? null : setConfirm(false))}
        title="구매 하시겠습니까?"
        dismissOnBackdrop={!processing}
      >
        <View style={styles.popPrice}>
          <PixelCoin size={14} />
          <Text style={styles.popPriceText}>가격 : {itemPriceFormatted} P</Text>
        </View>

        {processing ? (
          <View style={styles.processing}>
            <PixelSpinner />
            <Text style={styles.processingText}>구매 중...</Text>
          </View>
        ) : (
          <PopupButtons
            primaryLabel="예"
            onPrimary={onConfirmYes}
            secondaryLabel="아니오"
            onSecondary={() => setConfirm(false)}
          />
        )}
      </GamePopup>
    </View>
  );
}

/** Small rotating pixel-square spinner (transform-only) for the 처리 중 state. */
function PixelSpinner() {
  const r = useSharedValue(0);
  React.useEffect(() => {
    r.value = withRepeat(withTiming(1, { duration: 900, easing: Easing.linear }), -1, false);
  }, []);
  const style = useAnimatedStyle(() => ({ transform: [{ rotate: `${r.value * 360}deg` }] }));
  return (
    <Animated.View style={[styles.spinner, style]}>
      <View style={[styles.spinnerDot, { top: 0, left: 0 }]} />
      <View style={[styles.spinnerDot, { top: 0, right: 0, opacity: 0.7 }]} />
      <View style={[styles.spinnerDot, { bottom: 0, right: 0, opacity: 0.45 }]} />
      <View style={[styles.spinnerDot, { bottom: 0, left: 0, opacity: 0.25 }]} />
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.screenBg },
  body: { paddingHorizontal: 16, paddingTop: 18, paddingBottom: 120 },

  perspective: { marginBottom: 16 },
  hero: {
    width: '100%',
    height: 220,
    borderRadius: 14,
    overflow: 'hidden',
    alignItems: 'center',
    justifyContent: 'center',
    ...shadow.card,
    shadowOpacity: 0.18,
    shadowRadius: 24,
  },
  heroEmoji: { fontSize: 82 },

  infoCard: { backgroundColor: colors.white, borderRadius: 14, padding: 18, ...shadow.card },
  name: { fontSize: 20, fontWeight: '700', color: colors.textPrimary, marginBottom: 8, fontFamily: fonts.bodyB },
  desc: { fontSize: 14, color: colors.textSecondary, lineHeight: 22, marginBottom: 16, fontFamily: fonts.bodyR },
  priceRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  priceText: { fontSize: 16, fontWeight: '800', color: colors.gold, fontFamily: fonts.bodyB },

  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, paddingHorizontal: 20, paddingTop: 16, paddingBottom: 30 },
  buyBtn: {
    height: 52,
    borderRadius: 14,
    backgroundColor: colors.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
    ...shadow.button,
  },
  buyBtnDisabled: { backgroundColor: colors.textMuted, shadowOpacity: 0 },
  buyText: { color: colors.white, fontSize: 16, fontWeight: '700', fontFamily: fonts.bodyB },

  popPrice: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  popPriceText: { fontSize: 14, fontWeight: '700', color: '#F0C24B', fontFamily: fonts.bodyB },

  processing: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, marginTop: 20 },
  processingText: { color: gamePopup.cream, fontSize: 14, fontWeight: '700', fontFamily: fonts.bodyB },
  spinner: { width: 18, height: 18 },
  spinnerDot: { position: 'absolute', width: 6, height: 6, backgroundColor: colors.gold },
});