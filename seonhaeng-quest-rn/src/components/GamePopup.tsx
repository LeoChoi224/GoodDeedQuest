/**
 * 다크 게임 팝업 (딥틸 그라데이션 + 골드 테두리/이너 링 + 크림 텍스트) 스케일 인.
 * Backdrop fade + content scale-in (overshoot spring). Used for confirms, password
 * prompts, invite dialogs, purchase confirms, etc.
 */
import React from 'react';
import { Modal, View, Text, Pressable, StyleSheet, StyleProp, ViewStyle } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, { FadeIn, FadeOut, ZoomIn } from 'react-native-reanimated';
import { colors, fonts, gamePopup, radii } from '../theme';

export default function GamePopup({
  visible,
  onClose,
  title,
  children,
  width = 320,
  dismissOnBackdrop = true,
  style,
}: {
  visible: boolean;
  onClose?: () => void;
  title?: string;
  children?: React.ReactNode;
  width?: number;
  dismissOnBackdrop?: boolean;
  style?: StyleProp<ViewStyle>;
}) {
  return (
    <Modal visible={visible} transparent animationType="none" onRequestClose={onClose} statusBarTranslucent>
      <View style={styles.center}>
        <Animated.View entering={FadeIn.duration(180)} exiting={FadeOut.duration(160)} style={StyleSheet.absoluteFill}>
          <Pressable style={styles.backdrop} onPress={dismissOnBackdrop ? onClose : undefined} />
        </Animated.View>

        <Animated.View
          entering={ZoomIn.duration(180)}
          exiting={FadeOut.duration(140)}
          style={[styles.frame, { width }, style]}
        >
          <LinearGradient colors={gamePopup.goldFrame} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.frameGrad}>
            <LinearGradient colors={gamePopup.gradient} start={{ x: 0.5, y: 0 }} end={{ x: 0.5, y: 1 }} style={styles.body}>
              {title ? <Text style={styles.title}>{title}</Text> : null}
              {children}
            </LinearGradient>
          </LinearGradient>
        </Animated.View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  backdrop: { flex: 1, backgroundColor: 'rgba(2,20,22,0.62)' },
  frame: { borderRadius: 24, overflow: 'hidden' },
  frameGrad: { padding: 3, borderRadius: 24 },
  body: {
    borderRadius: 21,
    paddingHorizontal: 22,
    paddingVertical: 26,
    borderWidth: 1.5,
    borderColor: gamePopup.innerRing,
    alignItems: 'center',
  },
  title: {
    fontFamily: fonts.pixel,
    fontSize: 20,
    color: gamePopup.cream,
    textAlign: 'center',
    marginBottom: 14,
  },
});

/** Cream-on-teal primary + secondary buttons for use inside GamePopup. */
export function PopupButtons({
  primaryLabel,
  onPrimary,
  secondaryLabel,
  onSecondary,
}: {
  primaryLabel: string;
  onPrimary?: () => void;
  secondaryLabel?: string;
  onSecondary?: () => void;
}) {
  return (
    <View style={pb.row}>
      {secondaryLabel ? (
        <Pressable style={[pb.btn, pb.secondary]} onPress={onSecondary}>
          <Text style={pb.secondaryText}>{secondaryLabel}</Text>
        </Pressable>
      ) : null}
      <Pressable style={[pb.btn, pb.primary]} onPress={onPrimary}>
        <Text style={pb.primaryText}>{primaryLabel}</Text>
      </Pressable>
    </View>
  );
}

const pb = StyleSheet.create({
  row: { flexDirection: 'row', gap: 10, marginTop: 20, alignSelf: 'stretch' },
  btn: { flex: 1, height: 46, borderRadius: radii.button, alignItems: 'center', justifyContent: 'center' },
  primary: { backgroundColor: colors.gold },
  primaryText: { color: '#3A2A08', fontSize: 15, fontWeight: '800', fontFamily: fonts.bodyB },
  secondary: { borderWidth: 1, borderColor: 'rgba(242,215,131,0.5)' },
  secondaryText: { color: gamePopup.cream, fontSize: 15, fontWeight: '700', fontFamily: fonts.bodyB },
});
