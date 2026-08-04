/**
 * EmptyState — 리스트 빈 상태 공통. (아이콘) + message(DotGothic16 15) + subMessage(body 13).
 * icon: 이모지 문자열 또는 임의 노드(PNG 등). message는 필수.
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, fonts } from '../theme';

export default function EmptyState({
  icon,
  message,
  subMessage,
}: {
  icon?: React.ReactNode;
  message: string;
  subMessage?: string;
}) {
  return (
    <View style={styles.wrap}>
      {icon != null ? (
        typeof icon === 'string' ? <Text style={styles.emoji}>{icon}</Text> : <View style={styles.iconWrap}>{icon}</View>
      ) : null}
      <Text style={styles.message}>{message}</Text>
      {subMessage ? <Text style={styles.sub}>{subMessage}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { alignItems: 'center', justifyContent: 'center', paddingVertical: 40, paddingHorizontal: 20 },
  emoji: { fontSize: 40, marginBottom: 12 },
  iconWrap: { marginBottom: 12 },
  message: { fontFamily: fonts.pixel, fontSize: 15, color: colors.primaryDark, textAlign: 'center' },
  sub: { fontFamily: fonts.bodyR, fontSize: 13, color: colors.textMuted, textAlign: 'center', marginTop: 6, lineHeight: 19 },
});
