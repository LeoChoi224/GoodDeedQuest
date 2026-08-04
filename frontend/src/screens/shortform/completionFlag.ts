/**
 * 숏폼 완성 화면(PlayerScreen)이 실제로 보여졌는지를 기록하는 모듈 레벨 플래그.
 *
 * PhotoSelectScreen은 완성 화면을 보고 돌아오면 선택/AI 대본/음악을 초기화해야 하는데,
 * "어떻게 나갔는지"(버튼/스와이프 제스처/안드로이드 하드웨어 뒤로가기/드로어 메뉴)에
 * 의존하는 방식(beforeRemove 등)은 이 앱에서 반복적으로 문제가 있었다(재귀 크래시,
 * 아예 안 먹힘). 대신 "Player가 보여졌다"는 사실 자체를 여기 기록해두고, PhotoSelect가
 * 포커스를 되찾을 때(useFocusEffect) 이 값을 소비해서 초기화 여부를 판단한다 -
 * 나가는 경로와 무관하게 항상 동작한다.
 */
let playerShown = false;

export function markPlayerShown() {
  playerShown = true;
}

/** 값을 읽고 즉시 false로 되돌린다 (한 번만 초기화되게). */
export function consumePlayerShown(): boolean {
  const was = playerShown;
  playerShown = false;
  return was;
}
