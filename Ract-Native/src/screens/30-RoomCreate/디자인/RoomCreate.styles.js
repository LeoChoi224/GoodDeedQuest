import { StyleSheet } from 'react-native';
import { COLORS, RADIUS } from '../../../shared/디자인/tokens';


export const styles = StyleSheet.create({
  header: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 4, flexDirection: 'row', alignItems: 'center', gap: 10 },
  logoBadge: { width: 30, height: 30, borderRadius: 9, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  logo: { fontSize: 20, fontWeight: '700', color: COLORS.primary },
  content: { paddingHorizontal: 24, paddingTop: 24, paddingBottom: 16, gap: 22 },
  title: { fontSize: 24, fontWeight: '600', color: COLORS.ink, lineHeight: 32 },
  subtitle: { fontSize: 13, color: COLORS.inkMuted48, marginTop: 8 },
  label: { fontSize: 13, fontWeight: '500', color: COLORS.inkMuted48 },
  input: { height: 48, backgroundColor: COLORS.parchment, borderWidth: 1, borderColor: COLORS.hairline, borderRadius: 14, paddingHorizontal: 16, fontSize: 15, color: COLORS.ink },
  textarea: { height: 88, paddingVertical: 12, textAlignVertical: 'top' },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  chip: { width: '47.5%', height: 48, borderRadius: 14, borderWidth: 1, borderColor: COLORS.hairline, backgroundColor: COLORS.parchment, alignItems: 'center', justifyContent: 'center' },
  chipSelected: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  chipText: { fontSize: 15, color: COLORS.ink },
  chipTextSelected: { color: '#fff' },
  stepperRow: { height: 48, backgroundColor: COLORS.parchment, borderWidth: 1, borderColor: COLORS.hairline, borderRadius: 14, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 8 },
  stepBtn: { width: 36, height: 36, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  stepperValue: { fontSize: 16, fontWeight: '700', color: COLORS.ink },
  noticeCard: { backgroundColor: COLORS.goldTint, borderRadius: 14, paddingVertical: 14, paddingHorizontal: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  noticeText: { fontSize: 13, color: COLORS.gold, fontWeight: '600' },
  footer: { paddingHorizontal: 24, paddingBottom: 24, paddingTop: 8 },
  submitButton: { height: 50, borderRadius: RADIUS.pill, alignItems: 'center', justifyContent: 'center' },
  submitButtonText: { fontSize: 17, fontWeight: '600' },
});
