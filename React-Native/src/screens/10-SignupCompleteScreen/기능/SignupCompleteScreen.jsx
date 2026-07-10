// SignupCompleteScreen.js — React Native (Expo) 회원가입 완료
// 선행퀘스트 / 스토리보드 10번 기준

import React, { useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, Animated, Easing } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Svg, { Path } from 'react-native-svg';

import { COLORS } from '../디자인/SignupCompleteScreen.styles';
import { styles } from '../디자인/SignupCompleteScreen.styles';

const AnimatedPath = Animated.createAnimatedComponent(Path);

function CareIcon({ size = 18 }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round">
      <Path d="M12 6.8c-.9-1.6-3-1.8-4.1-.4-.9 1.1-.7 2.7.4 3.7L12 13l3.7-2.9c1.1-1 1.3-2.6.4-3.7-1.1-1.4-3.2-1.2-4.1.4Z" />
      <Path d="M4.3 13.2c0 3.2 2.9 5.9 6.4 6.3" />
      <Path d="M19.7 13.2c0 3.2-2.9 5.9-6.4 6.3" />
    </Svg>
  );
}

export default function SignupCompleteScreen({ navigation }) {
  const circleScale = useRef(new Animated.Value(0.4)).current;
  const circleOpacity = useRef(new Animated.Value(0)).current;
  const ring1Scale = useRef(new Animated.Value(1)).current;
  const ring1Opacity = useRef(new Animated.Value(0.35)).current;
  const ring2Scale = useRef(new Animated.Value(1)).current;
  const ring2Opacity = useRef(new Animated.Value(0.35)).current;
  const checkDash = useRef(new Animated.Value(26)).current;
  const textShift = useRef(new Animated.Value(8)).current;
  const textOpacity = useRef(new Animated.Value(0)).current;
  const floatY = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(circleScale, { toValue: 1, friction: 5, tension: 120, useNativeDriver: true }),
      Animated.timing(circleOpacity, { toValue: 1, duration: 200, useNativeDriver: true }),
    ]).start();

    Animated.timing(checkDash, {
      toValue: 0,
      duration: 380,
      delay: 420,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false,
    }).start();

    Animated.parallel([
      Animated.timing(textShift, { toValue: 0, duration: 420, delay: 620, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
      Animated.timing(textOpacity, { toValue: 1, duration: 420, delay: 620, useNativeDriver: true }),
    ]).start();

    const rippleLoop = (scaleVal, opacityVal, delayMs) => {
      scaleVal.setValue(1);
      opacityVal.setValue(0.35);
      Animated.loop(
        Animated.parallel([
          Animated.timing(scaleVal, { toValue: 1.6, duration: 1800, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
          Animated.timing(opacityVal, { toValue: 0, duration: 1800, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
        ])
      ).start();
    };

    const floatLoop = () => {
      Animated.loop(
        Animated.sequence([
          Animated.timing(floatY, { toValue: -7, duration: 1300, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
          Animated.timing(floatY, { toValue: 0, duration: 1300, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
        ])
      ).start();
    };

    const t1 = setTimeout(() => rippleLoop(ring1Scale, ring1Opacity, 480), 480);
    const t2 = setTimeout(() => rippleLoop(ring2Scale, ring2Opacity, 1380), 1380);
    const t3 = setTimeout(floatLoop, 950);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.logoBadge} onPress={() => navigation.navigate('CommunityFeed')}>
          <CareIcon size={18} />
        </TouchableOpacity>
        <Text style={styles.logo}>선·퀘</Text>
      </View>

      <View style={styles.content}>
        <Animated.View style={{ width: 96, height: 96, alignItems: 'center', justifyContent: 'center', transform: [{ translateY: floatY }] }}>
          <Animated.View
            style={[
              styles.ripple,
              { opacity: ring1Opacity, transform: [{ scale: ring1Scale }] },
            ]}
          />
          <Animated.View
            style={[
              styles.ripple,
              { opacity: ring2Opacity, transform: [{ scale: ring2Scale }] },
            ]}
          />
          <Animated.View
            style={[
              styles.checkCircle,
              { opacity: circleOpacity, transform: [{ scale: circleScale }] },
            ]}
          >
            <Svg width={48} height={48} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round">
              <AnimatedPath d="M5 12.5 9.8 17.3 19 6.7" strokeDasharray={26} strokeDashoffset={checkDash} />
            </Svg>
          </Animated.View>
        </Animated.View>
        <Animated.View style={{ alignItems: 'center', opacity: textOpacity, transform: [{ translateY: textShift }] }}>
          <Text style={styles.title}>환영합니다!</Text>
          <Text style={styles.subtitle}>
            선·퀘 가입이 완료됐어요.{'\n'}지금 바로 첫 선행을 시작해보세요.
          </Text>
        </Animated.View>
      </View>

      <View style={styles.footer}>
        <TouchableOpacity
          activeOpacity={0.95}
          onPress={() => navigation.navigate('Login')}
          style={styles.nextButton}
        >
          <Text style={styles.nextButtonText}>로그인창으로 이동</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

