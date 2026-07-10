import { StyleSheet } from 'react-native';
import { COLORS, RADIUS } from '../../../shared/디자인/tokens';


export const styles = StyleSheet.create({
  header: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 4, flexDirection: 'row', alignItems: 'center', gap: 10 },
  headerTitle: { fontSize: 18, fontWeight: '700', color: COLORS.ink },
  content: { paddingHorizontal: 24, paddingTop: 18, paddingBottom: 24, gap: 20 },
  profileCard: { flexDirection: 'row', alignItems: 'center', gap: 14, backgroundColor: '#fff', borderWidth: 1, borderColor: COLORS.hairline, borderRadius: 18, padding: 14, paddingHorizontal: 16 },
  avatar: { width: 52, height: 52, borderRadius: 9999, backgroundColor: COLORS.mint, alignItems: 'center', justifyContent: 'center' },
  avatarText: { fontSize: 17, fontWeight: '700', color: '#fff' },
  nickname: { fontSize: 16, fontWeight: '700', color: COLORS.ink },
  titleTag: { backgroundColor: COLORS.goldTint, borderWidth: 1, borderColor: 'rgba(201,162,39,0.5)', paddingVertical: 3, paddingHorizontal: 10, borderRadius: RADIUS.pill },
  titleTagText: { fontSize: 12, fontWeight: '800', color: COLORS.primary },
  levelTag: { alignSelf: 'flex-start', backgroundColor: COLORS.primary, paddingVertical: 2, paddingHorizontal: 9, borderRadius: RADIUS.pill },
  levelTagText: { fontSize: 13, fontWeight: '800', color: '#fff' },
  card: { backgroundColor: '#fff', borderWidth: 1, borderColor: COLORS.hairline, borderRadius: 18, padding: 16, gap: 10 },
  cardTitle: { fontSize: 15, fontWeight: '700', color: COLORS.ink },
  expText: { fontSize: 12.5, color: COLORS.inkMuted48 },
  expBarTrack: { height: 12, borderRadius: RADIUS.pill, backgroundColor: COLORS.parchment, overflow: 'hidden' },
  expBarFill: { height: '100%', borderRadius: RADIUS.pill, backgroundColor: COLORS.primary },
  expHint: { fontSize: 11.5, color: COLORS.inkMuted48 },
  tab: { height: 26, paddingHorizontal: 12, borderRadius: RADIUS.pill, backgroundColor: COLORS.parchment, borderWidth: 1, borderColor: COLORS.hairline, alignItems: 'center', justifyContent: 'center' },
  tabActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  tabText: { fontSize: 12, fontWeight: '600', color: COLORS.ink },
  tabTextActive: { color: '#fff' },
  chartLabel: { fontSize: 10.5, color: COLORS.inkMuted48, flex: 1, textAlign: 'center' },
  rankingButton: { height: 50, borderRadius: RADIUS.pill, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  rankingButtonText: { fontSize: 15, fontWeight: '700', color: '#fff' },
});
