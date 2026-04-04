import { StatusBar } from 'expo-status-bar';
import { Stack } from 'expo-router';

const HEADER_BG = '#0f172a';

export default function RootLayout() {
  return (
    <>
      <StatusBar style="light" translucent backgroundColor="transparent" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: HEADER_BG },
          headerTintColor: '#fff',
          headerTitleStyle: { fontWeight: 'bold', fontSize: 18 },
          contentStyle: { backgroundColor: HEADER_BG },
          headerShadowVisible: false,
          animation: 'slide_from_right',
          headerBackTitleVisible: false,
        }}
      >
        <Stack.Screen
          name="index"
          options={{
            title: 'TeamGenie AI',
            headerLargeTitle: true,
          }}
        />
        <Stack.Screen
          name="generate"
          options={{
            title: 'Generate Team',
            presentation: 'modal',
          }}
        />
        <Stack.Screen
          name="history"
          options={{ title: 'My Teams' }}
        />
        <Stack.Screen
          name="settings"
          options={{ title: 'Settings' }}
        />
      </Stack>
    </>
  );
}
