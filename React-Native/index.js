import { registerRootComponent } from 'expo';
import App from './App';

// registerRootComponent는 Expo Go / native build 양쪽 환경에서
// AppRegistry.registerComponent를 자동으로 호출해줍니다.
registerRootComponent(App);
