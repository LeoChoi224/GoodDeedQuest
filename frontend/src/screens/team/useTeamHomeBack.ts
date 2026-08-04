import { useCallback, useEffect } from 'react';
import { BackHandler, Platform } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';

type InnerBackHandler = () => boolean;

export default function useTeamHomeBack(
  navigation: any,
  onInnerBack?: InnerBackHandler,
) {
  const goTeamHome = useCallback(() => {
    navigation.reset({
      index: 0,
      routes: [
        {
          name: 'TeamHome',
        },
      ],
    });
  }, [navigation]);

  const handleBack = useCallback(() => {
    if (onInnerBack?.()) {
      return;
    }

    goTeamHome();
  }, [goTeamHome, onInnerBack]);

  useEffect(() => {
    // iOS 스와이프 뒤로가기로 이전 중간 화면이 다시 나타나지 않도록 막습니다.
    navigation.setOptions({
      gestureEnabled: false,
    });
  }, [navigation]);

  useFocusEffect(
    useCallback(() => {
      if (Platform.OS !== 'android') {
        return undefined;
      }

      const subscription = BackHandler.addEventListener(
        'hardwareBackPress',
        () => {
          handleBack();
          return true;
        },
      );

      return () => subscription.remove();
    }, [handleBack]),
  );

  return {
    goTeamHome,
    handleBack,
  };
}