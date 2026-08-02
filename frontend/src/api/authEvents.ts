/**
 * 로그아웃 신호를 주고받는 자리.
 *
 * axios 인터셉터(client.ts)는 React 컴포넌트가 아니라서 useAuth() 같은 훅을
 * 쓸 수 없다. 그래서 "토큰이 죽었다"는 신호만 여기에 던지고, AuthProvider 가
 * 그 신호를 받아 실제 로그아웃을 처리한다.
 *
 * 사용법
 *   - client.ts (인터셉터):  401 을 받으면  emitUnauthorized()  를 부른다
 *   - AuthContext:          앱이 뜰 때  setUnauthorizedHandler(signOut)  으로 등록한다
 */

type Handler = () => void;

let handler: Handler | null = null;

/** 401 이 왔을 때 실행할 함수를 등록한다. AuthProvider 가 부른다. */
export function setUnauthorizedHandler(fn: Handler | null): void {
  handler = fn;
}

/** 토큰이 죽었다고 알린다. 등록된 함수가 없으면 아무 일도 일어나지 않는다. */
export function emitUnauthorized(): void {
  handler?.();
}
