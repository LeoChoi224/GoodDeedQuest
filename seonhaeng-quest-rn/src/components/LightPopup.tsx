/**
 * LightPopup — 기능성(비밀번호·소개·확인/취소) 라이트 대화상자.
 * bg parchment(#FFF8E7) · 1.5px pixelBorder(#5C3D1E) · radius 16 · dim 0.28 · 우상단 X.
 * 다크 RPG 팝업(GamePopup: 완료/보상/신고/이벤트)과 용도 구분.
 */
import React from 'react';
import { Modal, View, Text, Pressable, StyleSheet, StyleProp, ViewStyle } from 'react-native';
import Animated, { FadeIn, FadeOut, ZoomIn } from 'react-native-reanimated';
import { colors, fonts, radii } from '../theme';

export default function LightPopup({
  visible,
  onClose,
  children,
  width = 320,
  dismissOnBackdrop = true,
  showClose = true,
  style,
}: {
  visible: boolean;
  onClose?: () => void;
  children?: React.ReactNode;
  width?: number;
  dismissOnBackdrop?: boolean;
  showClose?: boolean;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <Modal visible={visible} transparent animationType="none" onRequestClose={onClose} statusBarTranslucent>
      <View style={styles.center}>
        <Animated.View entering={FadeIn.duration(160)} exiting={FadeOut.duration(140)} style={StyleSheet.absoluteFill}>
          <Pressable style={styles.backdrop} onPress={dismissOnBackdrop ? onClose : undefined} />
        </Animated.View>
        <Animated.View
          entering={ZoomIn.duration(180)}
          exiting={FadeOut.duration(120)}
          style={[styles.card, { width }, style]}
        >
          {showClose ? (
            <Pressable style={styles.close} onPress={onClose} hitSlop={10}>
              <Text style={styles.closeX}>✕</Text>
            </Pressable>
          ) : null}
          {children}
        </Animated.View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  backdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.28)' },
  card: {
    backgroundColor: colors.parchment,
    borderWidth: 1.5,
    borderColor: colors.pixelBorder,
    borderRadius: radii.card, // 16
    padding: 24,
    alignItems: 'center',
    elevation: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.2,
    shadowRadius: 18,
  },
  close: { position: 'absolute', top: 12, right: 12, width: 24, height: 24, alignItems: 'center', justifyContent: 'center', zIndex: 3 },
  closeX: { fontSize: 18, color: colors.primaryDark, fontFamily: fonts.bodyB },
});
