import { StyleSheet } from 'react-native';
import { COLORS } from '../../../shared/디자인/tokens';


export const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.canvas },
  header: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 12, flexDirection: 'row', alignItems: 'center', gap: 8, borderBottomWidth: 1, borderBottomColor: COLORS.hairline },
  logoBadge: { width: 30, height: 30, borderRadius: 9, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  logo: { fontSize: 20, fontWeight: '700', color: COLORS.primary },
  mapArea: { flex: 1, backgroundColor: COLORS.parchment, overflow: 'hidden' },
  roadH: { position: 'absolute', left: 0, width: '100%', height: 16, backgroundColor: '#fff', borderTopWidth: 1, borderBottomWidth: 1, borderColor: 'rgba(0,0,0,0.06)' },
  roadV: { position: 'absolute', top: 0, width: 14, height: '100%', backgroundColor: '#fff', borderLeftWidth: 1, borderRightWidth: 1, borderColor: 'rgba(0,0,0,0.06)' },
  block: { position: 'absolute', borderRadius: 8, backgroundColor: 'rgba(0,0,0,0.035)' },
  blockGreen: { position: 'absolute', borderRadius: 8, backgroundColor: 'rgba(139,209,157,0.3)' },
  pin: { width: 34, height: 34, borderRadius: 17, borderBottomRightRadius: 0, transform: [{ rotate: '45deg' }], alignItems: 'center', justifyContent: 'center', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 1, shadowRadius: 6, elevation: 4 },
  tabToggleWrap: { position: 'absolute', left: 0, right: 0, bottom: 14, alignItems: 'center' },
  tabToggle: { flexDirection: 'row', gap: 8, backgroundColor: 'rgba(255,255,255,0.95)', borderRadius: 14, padding: 5, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.1, shadowRadius: 12, elevation: 4 },
  tabButton: { height: 38, paddingHorizontal: 18, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  tabButtonText: { fontSize: 14, fontWeight: '600', color: COLORS.ink },
  popupCard: { position: 'absolute', left: 20, right: 20, bottom: 82, backgroundColor: '#fff', borderRadius: 20, padding: 16, paddingBottom: 14, shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.16, shadowRadius: 20, elevation: 8 },
  popupIcon: { width: 40, height: 40, borderRadius: 9999, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  popupTitle: { fontSize: 16, fontWeight: '700', color: COLORS.ink },
  popupSub: { fontSize: 12.5, color: COLORS.inkMuted48 },
  popupDesc: { fontSize: 13.5, color: COLORS.ink, lineHeight: 19, paddingLeft: 52 },
  difficultyBadge: { fontSize: 11, fontWeight: '700', color: COLORS.inkMuted48, backgroundColor: COLORS.parchment, borderWidth: 1, borderColor: COLORS.hairline, borderRadius: 9999, paddingVertical: 2, paddingHorizontal: 9 },
  rewardPill: { flexDirection: 'row', alignItems: 'center', gap: 5, backgroundColor: COLORS.goldTint, borderRadius: 9999, paddingVertical: 7, paddingHorizontal: 13 },
  rewardPillLabel: { fontSize: 12.5, fontWeight: '700', color: COLORS.gold },
  rewardPillValue: { fontSize: 12.5, fontWeight: '700', color: COLORS.ink },
  detailButton: { height: 40, paddingHorizontal: 18, borderRadius: 9999, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  detailButtonText: { fontSize: 14, fontWeight: '600', color: '#fff' },
});
