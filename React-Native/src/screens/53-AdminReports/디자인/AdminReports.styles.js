import { StyleSheet } from 'react-native';
import { COLORS, RADIUS } from '../../../shared/디자인/tokens';


export const styles = StyleSheet.create({
  header: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 4, flexDirection: 'row', alignItems: 'center', gap: 10 },
  headerTitle: { fontSize: 18, fontWeight: '700', color: COLORS.ink },
  content: { paddingHorizontal: 20, paddingTop: 14, paddingBottom: 22, gap: 14 },
  tab: { height: 32, paddingHorizontal: 14, borderRadius: 14, backgroundColor: COLORS.parchment, borderWidth: 1, borderColor: COLORS.hairline, alignItems: 'center', justifyContent: 'center' },
  tabActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  tabText: { fontSize: 13, fontWeight: '600', color: COLORS.ink },
  countText: { fontSize: 12.5, fontWeight: '600', color: COLORS.inkMuted48 },
  reportCard: { backgroundColor: '#fff', borderWidth: 1, borderColor: COLORS.hairline, borderRadius: 16, padding: 13, paddingHorizontal: 14, gap: 7 },
  typeTag: { backgroundColor: '#FBEAE8', paddingVertical: 3, paddingHorizontal: 9, borderRadius: RADIUS.pill },
  typeTagText: { fontSize: 11, fontWeight: '700', color: '#B23A34' },
  newBadge: { backgroundColor: COLORS.primary, paddingVertical: 2, paddingHorizontal: 7, borderRadius: RADIUS.pill },
  newBadgeText: { fontSize: 9.5, fontWeight: '800', color: '#fff' },
  statusChip: { paddingVertical: 3, paddingHorizontal: 9, borderRadius: RADIUS.pill },
  statusChipText: { fontSize: 10.5, fontWeight: '700' },
  reportTarget: { fontSize: 14, fontWeight: '700', color: COLORS.ink },
  reportReason: { fontSize: 12.5, color: COLORS.inkMuted48, lineHeight: 17 },
  reportMeta: { fontSize: 11, color: COLORS.inkMuted48 },
  bottomNav: { flexDirection: 'row', justifyContent: 'space-around', paddingTop: 10, paddingBottom: 20, borderTopWidth: 1, borderTopColor: COLORS.hairline, backgroundColor: 'rgba(255,255,255,0.7)' },
  navItem: { alignItems: 'center', gap: 4, width: 76 },
  navLabel: { fontSize: 10, color: COLORS.inkMuted48 },
});
