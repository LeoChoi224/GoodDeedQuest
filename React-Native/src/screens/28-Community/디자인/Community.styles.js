import { StyleSheet } from 'react-native';
import { COLORS } from '../../../shared/디자인/tokens';


export const styles = StyleSheet.create({
  header: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 4, flexDirection: 'row', alignItems: 'center', gap: 8 },
  logoBadge: { width: 30, height: 30, borderRadius: 9, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  logo: { fontSize: 20, fontWeight: '700', color: COLORS.primary },
  challengeButton: { height: 36, paddingHorizontal: 16, borderRadius: 9999, backgroundColor: COLORS.parchment, borderWidth: 1, borderColor: COLORS.hairline, alignItems: 'center', justifyContent: 'center', marginRight: 6 },
  challengeButtonText: { fontSize: 13, fontWeight: '600', color: COLORS.ink },
  postBlock: { paddingBottom: 16, marginBottom: 16, borderBottomWidth: 1, borderBottomColor: 'rgba(0,0,0,0.07)' },
  postHeaderRow: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 20, paddingBottom: 10 },
  avatar: { width: 36, height: 36, borderRadius: 9999, alignItems: 'center', justifyContent: 'center' },
  avatarText: { fontSize: 12, fontWeight: '700', color: '#fff' },
  userId: { fontSize: 14, fontWeight: '700', color: COLORS.ink },
  timeAgo: { fontSize: 12, color: COLORS.inkMuted48 },
  mediaPlaceholder: { width: '100%', height: 420, backgroundColor: COLORS.parchment, alignItems: 'center', justifyContent: 'center' },
  mediaPlaceholderText: { fontSize: 13, color: COLORS.inkMuted48, fontWeight: '600' },
  actionsRow: { flexDirection: 'row', alignItems: 'center', gap: 14, paddingHorizontal: 20, paddingTop: 12 },
  likeCount: { paddingHorizontal: 20, paddingTop: 8, fontSize: 13.5, fontWeight: '700', color: COLORS.ink },
  caption: { paddingHorizontal: 20, paddingTop: 4, fontSize: 13.5, color: COLORS.ink, lineHeight: 19 },
  commentLink: { paddingHorizontal: 20, paddingTop: 4, fontSize: 13, color: COLORS.inkMuted48 },
  sheetOverlay: { flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(3,50,54,0.4)' },
  sheet: { backgroundColor: '#fff', borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 20, paddingBottom: 28 },
  sheetHandle: { width: 36, height: 4, borderRadius: 9999, backgroundColor: 'rgba(0,0,0,0.12)', alignSelf: 'center', marginBottom: 10 },
  sheetTitle: { fontSize: 15, fontWeight: '700', color: COLORS.ink, textAlign: 'center', paddingBottom: 12, borderBottomWidth: 1, borderBottomColor: 'rgba(0,0,0,0.06)' },
  optionRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 16 },
  optionText: { fontSize: 15, fontWeight: '600', color: COLORS.ink },
  optionDivider: { height: 1, backgroundColor: 'rgba(0,0,0,0.06)', marginHorizontal: 20 },
  cancelRow: { marginTop: 8, marginHorizontal: 0, paddingVertical: 15, borderRadius: 14, backgroundColor: COLORS.parchment, alignItems: 'center' },
});
