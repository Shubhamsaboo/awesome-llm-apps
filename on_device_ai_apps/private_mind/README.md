# Private Mind - local AI chat on your phone

Private Mind is an open-source mobile app that runs LLMs entirely on your phone. There is no cloud backend: models execute locally through [React Native ExecuTorch](https://github.com/software-mansion/react-native-executorch), so conversations never leave the device. No account, no subscription, no data collection.

Built by [Software Mansion](https://swmansion.com), the team behind React Native ExecuTorch, Reanimated, and Gesture Handler.

- Official repo: [software-mansion-labs/private-mind](https://github.com/software-mansion-labs/private-mind)
- [App Store](https://apps.apple.com/us/app/private-mind/id6746713439) | [Google Play](https://play.google.com/store/apps/details?id=com.swmansion.privatemind)

## Features

- Chat with LLMs fully offline. After a model is downloaded, the app works with no internet connection at all.
- Pick from the built-in model catalog or load your own ExecuTorch-exported model.
- Benchmark models on your own hardware to compare speed before committing to one.
- Everything is stored locally on the device. Nothing is collected or shared.
- Work with images and documents without sharing them with providers.

## How it works

The app is written in TypeScript with Expo (React Native). Inference runs through [react-native-executorch](https://github.com/software-mansion/react-native-executorch), a declarative API over PyTorch's [ExecuTorch](https://pytorch.org/executorch/) runtime, which executes quantized models directly on the phone's hardware. This is the same stack you would use to add on-device AI to your own React Native app, and Private Mind doubles as a full reference implementation for it.

## Run from source

If you just want to use the app, install it from the [App Store](https://apps.apple.com/us/app/private-mind/id6746713439) or [Google Play](https://play.google.com/store/apps/details?id=com.swmansion.privatemind). To build it yourself:

Prerequisites: Node.js, Yarn, and a working React Native environment (Xcode for iOS, Android Studio for Android).

```bash
git clone https://github.com/software-mansion-labs/private-mind.git
cd private-mind

# fetch the bundled model assets
node -e "require('./scripts/download-models.js').ensureModelAssets()"

yarn

# then either
yarn expo run:ios
# or
yarn expo run:android
```

The app is licensed under MIT. Issues and contributions go through the [official repo](https://github.com/software-mansion-labs/private-mind).
