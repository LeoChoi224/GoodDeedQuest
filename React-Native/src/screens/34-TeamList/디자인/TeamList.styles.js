import { StyleSheet } from 'react-native';
import { COLORS, RADIUS } from '../../../shared/디자인/tokens';


export const styles = StyleSheet.create({
  header: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 4, flexDirection: 'row', alignItems: 'center', gap: 10 },
  logoBadge: { width: 30, height: 30, borderRadius: 9, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  logo: { fontSize: 20, fontWeight: '700', color: COLORS.primary },
  addButton: { width: 36, height: 36, borderRadius: 9999, backgroundColor: COLORS.parchment, borderWidth: 1, borderColor: COLORS.hairline, alignItems: 'center', justifyContent: 'center' },
  content: { paddingHorizontal: 24, paddingTop: 22, paddingBottom: 20, gap: 18 },
  title: { fontSize: 24, fontWeight: '600', color: COLORS.ink, lineHeight: 32 },
  subtitle: { fontSize: 13, color: COLORS.inkMuted48, marginTop: 8 },
  teamCard: { backgroundColor: '#fff', borderWidth: 1, borderColor: COLORS.hairline, borderRadius: 18, padding: 16, gap: 10 },
  categoryTag: { backgroundColor: '#F0FAF2', paddingVertical: 4, paddingHorizontal: 9, borderRadius: RADIUS.pill },
  categoryTagText: { fontSize: 10, fontWeight: '700', color: COLORS.primary },
  memberCountText: { fontSize: 12, color: COLORS.inkMuted48 },
  teamName: { fontSize: 16, fontWeight: '700', color: COLORS.ink },
  hostAvatar: { width: 22, height: 22, borderRadius: 9999, alignItems: 'center', justifyContent: 'center' },
  hostAvatarText: { fontSize: 10, fontWeight: '700', color: '#fff' },
  hostText: { fontSize: 12.5, color: COLORS.inkMuted48 },
  findMoreButton: { height: 48, borderRadius: 14, borderWidth: 1, borderColor: 'rgba(0,0,0,0.18)', borderStyle: 'dashed', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6 },
  findMoreText: { fontSize: 14, fontWeight: '600', color: COLORS.inkMuted48 },
});
