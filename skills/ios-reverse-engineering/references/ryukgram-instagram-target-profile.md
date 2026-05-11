# RyukGram / Instagram Target Profile

This reference file defines the default target profile for Radan IPA Symbol Architect when analyzing Instagram iOS binaries for RyukGram-style tweak work.

## Main binaries of interest

Typical IPA paths:

```text
Payload/Instagram.app/Instagram
Payload/Instagram.app/Frameworks/FBSharedFramework.framework/FBSharedFramework
Payload/Instagram.app/Frameworks/SharedModules.framework/SharedModules
Payload/Instagram.app/Frameworks/*.framework/*
Payload/Instagram.app/Frameworks/*.dylib
```

## MobileConfig and EasyGating C targets

```text
_IGMobileConfigBooleanValueForInternalUse
_IGMobileConfigDoubleValueForInternalUse
_IGMobileConfigIntegerValueForInternalUse
_IGMobileConfigStringValueForInternalUse
_IGMobileConfigSessionlessBooleanValueForInternalUse
_IGMobileConfigForceUpdateConfigs
_IGMobileConfigSetConfigOverrides
_IGMobileConfigTryUpdateConfigsWithCompletion
_MCIMobileConfigGetBoolean
_MCIExperimentCacheGetMobileConfigBoolean
_MCIExtensionExperimentCacheGetMobileConfigBoolean
_METAExtensionsExperimentGetBoolean
_METAExtensionsExperimentGetBooleanWithoutExposure
_MSGCSessionedMobileConfigGetBoolean
_EasyGatingPlatformGetBoolean
_EasyGatingGetBoolean_Internal_DoNotUseOrMock
_EasyGatingGetBooleanUsingAuthDataContext_Internal_DoNotUseOrMock
_MCQEasyGatingGetBooleanInternalDoNotUseOrMock
```

## ObjC getter selectors

```text
getBool
getBool:
getBool:withDefault:
getBool:withOptions:
getBool:withOptions:withDefault:
getBoolWithoutLogging
getInt64
getInt64:withDefault:
getDouble
getDouble:withDefault:
getString
getString:withDefault:
_getTranslatedSpecifier:
getStableIdFromParamSpecifier:
```

## Dogfooding and internal UI

```text
_IGAppIsInstagramInternalAppsInstalledAndNotHiddenAfteriOS18
IGDogfoodingSettings
IGDogfoodingSettingsViewController
IGDogfoodingSettingsSelectionViewController
IGDogfoodingSettingsOptions
IGDogfoodingSettingsSection
IGDogfoodingSettingsItem
openWithConfig:onViewController:userSession:
```

## Direct Notes / QuickSnap

```text
IGDirectNotesDogfoodingSettings
IGDirectNotesDogfoodingSettingsStaticFuncs
notesDogfoodingSettingsOpenOnViewController:userSession:
IGQuickSnapExperimentationHelper
isQuicksnapEnabled:
isQuicksnapEnabledInInbox:
isQuicksnapEnabledAsPeek:
IGNotesTrayController
_isEligibleForQuicksnapCornerStackTransitionDialog
isQPEnabled:
```

## MetaLocalExperiment

```text
MetaLocalExperimentListViewController
MetaLocalExperimentDetailViewController
MetaLocalExperiment
FamilyLocalExperiment
LIDLocalExperiment
LIDExperimentGenerator
FDIDExperimentGenerator
initWithExperimentConfigs:experimentGenerator:
overrideGroupTo:
IGExperimentalNavigationSelectionViewController
```

## LiquidGlass / TabBar

```text
_METAIsLiquidGlassEnabled
_IGTabBarStyleForLauncherSet
IGTabBarDynamicSizingEnabled
IGTabBarIsFloatingStyle
IGTabBarHomecomingWithFloatingTabEnabled
IGTabBarViewPointFixEnabled
IGLiquidGlassInteractiveTabBar
setBarAppearance
IGLiquidGlassTabBarIndicatorView
setAppearance:
IGDSColorLiquidGlassElevatedSeparator
IGDSColorElevatedSeparator
```

## Risk rules

- `DoNotUseOrMock` symbols are high-risk. Prefer observing, not overriding.
- `tryUpdateConfigs` / force update / set overrides paths are high-risk during app startup.
- Default-on observer hooks can make the app slow or crash.
- Prefer per-value override keys and explicit user toggles.
- A selector/string hit is not proof of a callable hook. Confirm owner and callsite.
- A symbol-table hit is not proof that an offline patch is safe. Confirm prologue bytes and function semantics.
- A decoded MobileConfig ID is not a feature name unless verified by mapping/runtime/callsite.
