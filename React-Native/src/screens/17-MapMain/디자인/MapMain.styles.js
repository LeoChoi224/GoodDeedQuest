import { StyleSheet } from 'react-native';
import { COLORS, RADIUS, TYPE } from '../../../shared/디자인/tokens';


export const styles = StyleSheet.create({
  header: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 4, flexDirection: 'row', alignItems: 'center', gap: 8 },
  logoBadge: { width: 30, height: 30, borderRadius: 9, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  logo: { fontSize: 20, fontWeight: '700', color: COLORS.primary },
  content: { paddingHorizontal: 24, paddingTop: 18, paddingBottom: 24, gap: 16 },
  currentRegionRow: { height: 48, backgroundColor: COLORS.parchment, borderWidth: 1, borderColor: COLORS.hairline, borderRadius: 14, flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 16 },
  currentRegionText: { fontSize: 15, fontWeight: '600', color: COLORS.ink },
  topCard: { backgroundColor: COLORS.goldTint, borderRadius: 16, padding: 16, gap: 10 },
  topCardHeader: { fontSize: 11, fontWeight: '700', color: COLORS.gold, letterSpacing: 0.4 },
  topRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  rankBadge: { width: 24, height: 24, borderRadius: 9999, alignItems: 'center', justifyContent: 'center' },
  rankBadgeText: { color: '#fff', fontSize: 12, fontWeight: '700' },
  topRowName: { fontSize: 14.5, fontWeight: '700', color: COLORS.ink, flex: 1 },
  topRowScore: { fontSize: 13.5, fontWeight: '700', color: COLORS.primary },
  competitionLink: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 4, alignSelf: 'center' },
  competitionLinkText: { fontSize: 12, fontWeight: '700', color: COLORS.inkMuted48 },
  actionButton: { height: 50, borderRadius: RADIUS.pill, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  actionButtonText: { ...TYPE.body, color: COLORS.canvas, fontWeight: '600' },
  sheetOverlay: { flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(3,50,54,0.35)' },
  sheet: { backgroundColor: '#fff', borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 20, paddingBottom: 28 },
  sheetHandle: { width: 36, height: 4, borderRadius: 9999, backgroundColor: 'rgba(0,0,0,0.12)', alignSelf: 'center', marginBottom: 16 },
  sheetHeaderRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 },
  sheetTitle: { fontSize: 18, fontWeight: '700', color: COLORS.ink },
  sheetRow: { flexDirection: 'row', alignItems: 'center', gap: 12, padding: 10, paddingHorizontal: 12, borderRadius: 14, backgroundColor: COLORS.parchment },
  sheetRowName: { fontSize: 14.5, fontWeight: '700', color: COLORS.ink },
  sheetRowDong: { fontSize: 12, color: COLORS.inkMuted48 },
  sheetRowScore: { fontSize: 14, fontWeight: '700', color: COLORS.primary },
});
