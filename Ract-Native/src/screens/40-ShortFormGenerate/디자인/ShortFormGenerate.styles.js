import { StyleSheet } from 'react-native';
import { COLORS, RADIUS } from '../../../shared/디자인/tokens';


export const styles = StyleSheet.create({
  header: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 4, flexDirection: 'row', alignItems: 'center', gap: 10 },
  headerTitle: { fontSize: 18, fontWeight: '700', color: COLORS.ink },
  content: { paddingHorizontal: 24, paddingTop: 18, paddingBottom: 16, gap: 18 },
  title: { fontSize: 20, fontWeight: '700', color: COLORS.ink },
  subtitle: { fontSize: 13, color: COLORS.inkMuted48, marginTop: 2 },
  preview: { width: '100%', aspectRatio: 9 / 16, borderRadius: 20, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center', overflow: 'hidden' },
  spinner: { width: 44, height: 44, borderRadius: 9999, borderWidth: 3, borderColor: 'rgba(255,255,255,0.25)', borderTopColor: COLORS.mint },
  playButton: { width: 64, height: 64, borderRadius: 9999, backgroundColor: 'rgba(255,255,255,0.14)', alignItems: 'center', justifyContent: 'center' },
  playHint: { fontSize: 13, fontWeight: '600', color: 'rgba(255,255,255,0.75)' },
  previewCaption: { position: 'absolute', left: 14, right: 14, bottom: 14, gap: 4 },
  previewScript: { fontSize: 12.5, fontWeight: '700', color: '#fff' },
  previewTrack: { fontSize: 11, color: 'rgba(255,255,255,0.7)' },
  progressTrack: { height: 10, borderRadius: RADIUS.pill, backgroundColor: COLORS.parchment, overflow: 'hidden' },
  progressFill: { height: '100%', borderRadius: RADIUS.pill, backgroundColor: COLORS.primary },
  progressLabel: { fontSize: 12, color: COLORS.inkMuted48, textAlign: 'center' },
  summaryCard: { backgroundColor: '#fff', borderWidth: 1, borderColor: COLORS.hairline, borderRadius: 16, padding: 14, gap: 10 },
  summaryLabel: { fontSize: 12.5, color: COLORS.inkMuted48 },
  summaryValue: { fontSize: 13, fontWeight: '700', color: COLORS.ink },
  divider: { height: 1, backgroundColor: 'rgba(0,0,0,0.06)' },
  footer: { paddingHorizontal: 24, paddingBottom: 16 },
  downloadButton: { height: 50, borderRadius: RADIUS.pill, backgroundColor: COLORS.primary, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  downloadButtonText: { fontSize: 15, fontWeight: '700', color: '#fff' },
  toast: { position: 'absolute', left: '50%', bottom: 96, transform: [{ translateX: -110 }], backgroundColor: COLORS.ink, borderRadius: RADIUS.pill, paddingVertical: 12, paddingHorizontal: 20 },
  toastText: { color: '#fff', fontSize: 13, fontWeight: '600' },
});
