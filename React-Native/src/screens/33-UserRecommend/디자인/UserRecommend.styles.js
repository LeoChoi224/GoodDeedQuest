import { StyleSheet } from 'react-native';
import { COLORS } from '../../../shared/디자인/tokens';


export const styles = StyleSheet.create({
  header: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 4, flexDirection: 'row', alignItems: 'center', gap: 10 },
  logoBadge: { width: 30, height: 30, borderRadius: 9, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  logo: { fontSize: 20, fontWeight: '700', color: COLORS.primary },
  content: { paddingHorizontal: 24, paddingTop: 22, paddingBottom: 20, gap: 18 },
  title: { fontSize: 24, fontWeight: '600', color: COLORS.ink, lineHeight: 32 },
  subtitle: { fontSize: 13, color: COLORS.inkMuted48, marginTop: 8 },
  searchBar: { height: 48, backgroundColor: COLORS.parchment, borderWidth: 1, borderColor: COLORS.hairline, borderRadius: 14, flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 16 },
  searchInput: { flex: 1, fontSize: 15, color: COLORS.ink },
  userRow: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: 'rgba(0,0,0,0.06)' },
  avatar: { width: 44, height: 44, borderRadius: 9999, alignItems: 'center', justifyContent: 'center' },
  avatarText: { fontSize: 15, fontWeight: '700', color: '#fff' },
  userId: { fontSize: 14.5, fontWeight: '700', color: COLORS.ink },
  userBio: { fontSize: 12.5, color: COLORS.inkMuted48 },
  inviteButton: { height: 34, paddingHorizontal: 16, borderRadius: 14, borderWidth: 1, borderColor: COLORS.hairline, backgroundColor: COLORS.parchment, flexDirection: 'row', alignItems: 'center', gap: 4, justifyContent: 'center' },
  inviteButtonActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  inviteButtonText: { fontSize: 13, fontWeight: '600', color: COLORS.ink },
});
