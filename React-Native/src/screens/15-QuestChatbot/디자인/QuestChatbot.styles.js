import { StyleSheet } from 'react-native';
import { COLORS, RADIUS } from '../../../shared/디자인/tokens';


export const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.canvas },
  header: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 12, flexDirection: 'row', alignItems: 'center', gap: 10, borderBottomWidth: 1, borderBottomColor: COLORS.hairline },
  logoBadge: { width: 30, height: 30, borderRadius: 9, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  logo: { fontSize: 17, fontWeight: '700', color: COLORS.primary },
  subLogo: { fontSize: 12, color: COLORS.inkMuted48 },
  chatArea: { padding: 20, gap: 14 },
  userBubble: { alignSelf: 'flex-end', maxWidth: '78%', paddingVertical: 12, paddingHorizontal: 16, borderRadius: 18, borderBottomRightRadius: 4, backgroundColor: COLORS.primary },
  userBubbleText: { color: '#fff', fontSize: 15, lineHeight: 21 },
  botRow: { alignSelf: 'flex-start', maxWidth: '88%', flexDirection: 'row', gap: 8, alignItems: 'flex-end' },
  botAvatar: { width: 26, height: 26, borderRadius: 9999, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  botBubble: { padding: 12, paddingHorizontal: 16, borderRadius: 18, borderBottomLeftRadius: 4, backgroundColor: COLORS.parchment },
  botBubbleText: { color: COLORS.ink, fontSize: 15, lineHeight: 21 },
  typingBubble: { padding: 14, paddingHorizontal: 16, borderRadius: 18, borderBottomLeftRadius: 4, backgroundColor: COLORS.parchment, flexDirection: 'row', gap: 4, alignItems: 'center' },
  typingDot: { width: 6, height: 6, borderRadius: 9999, backgroundColor: COLORS.inkMuted48 },
  questRecRow: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 12, paddingHorizontal: 14, borderRadius: 16, backgroundColor: COLORS.parchment, borderWidth: 1, borderColor: 'rgba(0,0,0,0.06)' },
  questRecIcon: { width: 34, height: 34, borderRadius: 9999, backgroundColor: COLORS.goldTint, alignItems: 'center', justifyContent: 'center' },
  questRecTitle: { fontSize: 14.5, fontWeight: '600', color: COLORS.ink, flex: 1 },
  questRecButton: { height: 32, paddingHorizontal: 14, borderRadius: RADIUS.pill, backgroundColor: COLORS.canvas, borderWidth: 1, borderColor: COLORS.hairline, alignItems: 'center', justifyContent: 'center' },
  questRecButtonText: { fontSize: 13, fontWeight: '600', color: COLORS.ink },
  chipsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, paddingHorizontal: 20, paddingBottom: 12 },
  chip: { height: 38, paddingHorizontal: 16, borderRadius: RADIUS.sm + 4, backgroundColor: COLORS.parchment, borderWidth: 1, borderColor: COLORS.hairline, alignItems: 'center', justifyContent: 'center' },
  chipText: { fontSize: 14, fontWeight: '600', color: COLORS.ink },
  inputRow: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 20, paddingVertical: 10, paddingBottom: 20, borderTopWidth: 1, borderTopColor: COLORS.hairline },
  input: { flex: 1, height: 48, backgroundColor: COLORS.parchment, borderWidth: 1, borderColor: COLORS.hairline, borderRadius: 14, paddingHorizontal: 16, fontSize: 15, color: COLORS.ink },
  sendButton: { width: 48, height: 48, borderRadius: 9999, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
});
