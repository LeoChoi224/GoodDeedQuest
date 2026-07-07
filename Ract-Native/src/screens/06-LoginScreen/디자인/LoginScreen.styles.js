import { StyleSheet } from 'react-native';

export const COLORS = {
  primary: '#033236',       // 메인 강조색 (다크 틸)
  canvas: '#FFFFFF',
  parchment: '#F6F6F6',     // 서브 배경 / 인풋 필
  ink: '#1D1D1F',
  inkMuted48: '#7A7A7A',
  hairline: 'rgba(0,0,0,0.08)',
  kakao: '#FEE500',
  kakaoText: '#191919',
};
export const RADIUS = {
  lg: 18,
  pill: 9999,
};
export const TYPE = {
  display: { fontSize: 28, fontWeight: '600', letterSpacing: -0.3 },
  body: { fontSize: 17, letterSpacing: -0.37 },
  caption: { fontSize: 14, letterSpacing: -0.22 },
  micro: { fontSize: 10 },
};

export const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.canvas,
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  logoBadge: {
    width: 30,
    height: 30,
    borderRadius: 9,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logo: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.primary,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
    gap: 32,
  },
  title: {
    ...TYPE.display,
    color: COLORS.ink,
    textAlign: 'center',
    marginBottom: 8,
  },
  input: {
    height: 48,
    backgroundColor: COLORS.parchment,
    borderWidth: 1,
    borderColor: COLORS.hairline,
    borderRadius: RADIUS.lg,
    paddingHorizontal: 18,
    ...TYPE.body,
    color: COLORS.ink,
  },
  primaryButton: {
    height: 48,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryButtonText: {
    ...TYPE.body,
    color: COLORS.canvas,
    fontWeight: '600',
  },
  signupLink: {
    ...TYPE.caption,
    color: COLORS.inkMuted48,
  },
  oauthButton: {
    height: 48,
    borderRadius: RADIUS.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  oauthButtonText: {
    ...TYPE.body,
    fontWeight: '600',
  },
  bottomNav: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 10,
    paddingBottom: 20,
    borderTopWidth: 1,
    borderTopColor: COLORS.hairline,
    backgroundColor: COLORS.canvas,
  },
  navItem: {
    alignItems: 'center',
    gap: 4,
    width: 56,
  },
  navLabel: {
    ...TYPE.micro,
    color: COLORS.inkMuted48,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.35)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalCard: {
    width: 300,
    backgroundColor: COLORS.canvas,
    borderRadius: RADIUS.lg,
    paddingHorizontal: 24,
    paddingTop: 28,
    paddingBottom: 20,
    alignItems: 'center',
    gap: 18,
    shadowColor: '#000',
    shadowOpacity: 0.22,
    shadowRadius: 30,
    shadowOffset: { width: 3, height: 5 },
    elevation: 8,
  },
  modalTitle: {
    ...TYPE.body,
    fontWeight: '600',
    color: COLORS.ink,
  },
  modalSubtitle: {
    ...TYPE.caption,
    color: COLORS.inkMuted48,
    textAlign: 'center',
  },
  modalButton: {
    width: '100%',
    height: 44,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalButtonText: {
    ...TYPE.body,
    color: COLORS.canvas,
    fontWeight: '600',
  },
});
