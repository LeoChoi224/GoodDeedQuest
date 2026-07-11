# Flow Agent Contract — 선행퀘스트 RN

You implement ONE flow of an existing Expo React Native app. The app shell, navigation,
theme, and a shared component library already exist. **Reuse them. Do not re-invent tokens,
headers, popups, or navigation.** Write ONLY to your flow's screen files (paths given per flow).

## Golden rules
1. **Reuse `src/theme.ts`** for every color/font/radius/shadow. Never hardcode a hex that
   exists there. Body text `fonts.bodyR/bodyM/bodyB` (Noto Sans KR); pixel titles `fonts.pixel`
   (DotGothic16); numbers bold gold/green.
2. **Reuse shared components** (see API below). Screens render their own `<MainHeader/>`.
3. **Match the design 1:1** with the flow's `.dc.html` (I give you the path). It is hi-fi —
   colors, copy (Korean, verbatim), spacing, conditional states are final.
4. **Motion = Reanimated**, transform/opacity only. Apply interaction-gallery effects where the
   `.dc.html` shows them (spring press, error shake, stagger, confetti, shimmer, tilt, pulse,
   check-draw, count-up). Use the shared components that already encapsulate these.
5. **Screen props are untyped**: `export default function XxxScreen({ navigation, route }: any)`.
   Navigate with `navigation.navigate('RouteName', params?)` using the route names I list.
6. **Backgrounds**: light screens use `<HazeBackground/>` behind content (never flat mint).
   Dark hero/popup areas use the teal gradients from theme.
7. **Assets**: category tiles `CATEGORY_ICONS[key]`, glyphs `CATEGORY_GLYPHS[key]`,
   nav `NAV_ICONS`, brand `brand.appIcon`/`brand.appIconCheck`. Do NOT create new art; if you
   need imagery not in assets, use a neutral placeholder View/box (e.g. feed photos, item art).
8. **Verify 5×** against your `.dc.html` before returning: (1) screen inventory & nav edges,
   (2) layout/structure, (3) tokens, (4) interaction/validation logic, (5) motion. Fix each pass.
9. Keep files focused; put screen-local subcomponents in the same file or a `_parts.tsx` in
   your folder. Overwrite the placeholder files that already exist at your paths.

## Shared component API (import from `../../components/...`)

- `MainHeader` — `{ showBack?, onBack?, title?, right? }`. Dark 56px header + hamburger (opens drawer).
- `HazeBackground` — wrap: `<HazeBackground/>` as first child (absolute), content after.
- `SpringButton` — `{ onPress, disabled?, style, active?, bgColors?:[off,on], children }`. Spring press.
- `GdqInput` — `{ leftIcon?, rightAccessory?, onRightPress?, ...TextInputProps }`. Focus ring.
- `Checkbox` — `{ checked, onToggle, size? }`.
- `Shake` — `{ trigger:number, children }`. Bump trigger to shake (error).
- `Confetti` — celebratory burst (mount to fire).
- `Toast` — `useToast().show(msg)`. Provider already mounted at root.
- `GamePopup` — `{ visible, onClose, title?, width?, children }` + `PopupButtons` `{ primaryLabel,onPrimary,secondaryLabel?,onSecondary? }`. Dark teal + gold, scale-in. Use for confirms, password prompts, invites, purchase.
- `BottomSheet` — `{ visible, onClose, title?, children }`. Slide-up + backdrop. Comments, more-actions, music picker, terms detail.
- `Shimmer` — `{ width?, height?, radius? }`. Skeleton loader.
- `SegmentedTabs` — `{ tabs:string[], index, onChange }`. Sliding gold pill.
- `PixelProgress` — `{ progress:0..1, height?, color?, track? }`. Animated fill.
- `QuestCard` — `{ category, mode:'idle'|'active', title, desc?, point?, exp?, showDesc? }`. RPG card.
- Icons in `PixelIcons.tsx`: MailIcon, LockIcon, SwordIcon, EyeOpen, EyeOff, KakaoIcon, GoogleIcon,
  CalIcon, HamburgerIcon, ChevronLeft, CheckMark. Add more small SVG icons in your folder if needed.

## Theme quick ref (`src/theme.ts`)
`colors` (primaryDark #033236, parchment #FFF8E7, gold #D4A017, xpGreen #4CAF50, screenBg #EEF6F0,
danger #E53935, textPrimary/secondary/muted, white, inputBorder #E5E7EB). `radii`, `shadow`,
`fonts`, `spring`, `easing`, `CATEGORY_DEFS/COLORS/ICONS/GLYPHS`, `TIME_DEFS`, `gamePopup`, `brand`.

## Return format (IMPORTANT)
Return a concise **route manifest** + notes:
- Files you wrote (paths).
- For each screen: route name (must match my list), what it shows, nav edges (which button →
  which route), and any params it reads/writes.
- Any modal/bottom-sheet used inside a screen (not a route).
- New shared-ish components you added inside your folder.
- Confirmation you ran the 5 verification passes and what you fixed.
Do NOT edit files outside your flow folder or the navigation files — I own integration.
