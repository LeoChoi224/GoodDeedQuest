import { StyleSheet } from 'react-native';
import { COLORS, RADIUS } from '../../../shared/디자인/tokens';


export const styles = StyleSheet.create({
  header: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 4, flexDirection: 'row', alignItems: 'center', gap: 10 },
  headerTitle: { fontSize: 18, fontWeight: '700', color: COLORS.ink },
  content: { paddingHorizontal: 24, paddingTop: 10, paddingBottom: 24, gap: 18 },
  title: { fontSize: 22, fontWeight: '700', color: COLORS.ink },
  subtitle: { fontSize: 13, color: COLORS.inkMuted48, marginTop: 2 },
  myRow: { flexDirection: 'row', alignItems: 'center', gap: 14, backgroundColor: COLORS.primary, borderRadius: 18, padding: 16 },
  myBadge: { width: 48, height: 48, borderRadius: 9999, backgroundColor: 'rgba(255,255,255,0.14)', alignItems: 'center', justifyContent: 'center' },
  myBadgeText: { fontSize: 15, fontWeight: '800', color: '#fff' },
  myName: { fontSize: 15, fontWeight: '700', color: '#fff' },
  titleTag: { backgroundColor: COLORS.goldTint, paddingVertical: 2, paddingHorizontal: 9, borderRadius: RADIUS.pill },
  titleTagText: { fontSize: 11, fontWeight: '800', color: COLORS.primary },
  mySub: { fontSize: 12.5, color: 'rgba(255,255,255,0.7)' },
  tab: { height: 32, paddingHorizontal: 16, borderRadius: RADIUS.pill, backgroundColor: COLORS.parchment, borderWidth: 1, borderColor: COLORS.hairline, alignItems: 'center', justifyContent: 'center' },
  tabActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  tabText: { fontSize: 13, fontWeight: '600', color: COLORS.ink },
  tabTextActive: { color: '#fff' },
  rankRow: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 10, paddingHorizontal: 12, borderRadius: 14, borderWidth: 1 },
  rankBadge: { width: 26, height: 26, borderRadius: 9999, alignItems: 'center', justifyContent: 'center' },
  rankBadgeText: { fontSize: 12, fontWeight: '700' },
  avatar: { width: 34, height: 34, borderRadius: 9999, alignItems: 'center', justifyContent: 'center' },
  avatarText: { fontSize: 13, fontWeight: '700', color: '#fff' },
  rowName: { fontSize: 14, fontWeight: '700', color: COLORS.ink },
  mineTag: { fontSize: 10, fontWeight: '700', color: COLORS.primary, backgroundColor: COLORS.goldTint, paddingVertical: 2, paddingHorizontal: 7, borderRadius: RADIUS.pill },
  mineTagText: { fontSize: 10, fontWeight: '700', color: COLORS.primary },
  rowLevel: { fontSize: 11.5, color: COLORS.inkMuted48 },
  rowScore: { fontSize: 13.5, fontWeight: '700', color: COLORS.primary },
});
