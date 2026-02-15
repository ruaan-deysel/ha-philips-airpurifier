"""
Data-driven device model configurations.

This module converts the class hierarchy from philips.py into DeviceModelConfig
instances. Each model's capabilities are defined as data rather than through
class inheritance.
"""

from __future__ import annotations

from .const import FanModel, PhilipsApi, PresetMode
from .model import ApiGeneration, DeviceModelConfig

# =============================================================================
# Shared preset_modes / speeds configs for model families
# =============================================================================

# --- AC0850 Gen2 (AWS_Philips_AIR) family ---
_AC0850_GEN2_PRESET_MODES: dict[str, dict[str, str]] = {
    PresetMode.AUTO: {
        PhilipsApi.NEW_POWER: "ON",
        PhilipsApi.NEW_MODE: "Auto General",
    },
    PresetMode.TURBO: {PhilipsApi.NEW_POWER: "ON", PhilipsApi.NEW_MODE: "Turbo"},
    PresetMode.SLEEP: {PhilipsApi.NEW_POWER: "ON", PhilipsApi.NEW_MODE: "Sleep"},
}
_AC0850_GEN2_SPEEDS: dict[str, dict[str, str]] = {
    PresetMode.SLEEP: {PhilipsApi.NEW_POWER: "ON", PhilipsApi.NEW_MODE: "Sleep"},
    PresetMode.TURBO: {PhilipsApi.NEW_POWER: "ON", PhilipsApi.NEW_MODE: "Turbo"},
}

# --- AC0850 Gen3 (AWS_Philips_AIR_Combo) family ---
_AC0850_GEN3_PRESET_MODES: dict[str, dict[str, int]] = {
    PresetMode.AUTO: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 0,
    },
    PresetMode.TURBO: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 18},
    PresetMode.SLEEP: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 17},
}
_AC0850_GEN3_SPEEDS: dict[str, dict[str, int]] = {
    PresetMode.SLEEP: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 17},
    PresetMode.TURBO: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 18},
}

# --- AC0950 family ---
_AC0950_PRESET_MODES: dict[str, dict[str, int]] = {
    PresetMode.AUTO: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 0,
    },
    PresetMode.TURBO: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 18},
    PresetMode.MEDIUM: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 19},
    PresetMode.SLEEP: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 17},
}
_AC0950_SPEEDS: dict[str, dict[str, int]] = {
    PresetMode.SLEEP: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 17},
    PresetMode.MEDIUM: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 19},
    PresetMode.TURBO: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 18},
}

# --- AC29xx family ---
_AC29XX_PRESET_MODES: dict[str, dict[str, str]] = {
    PresetMode.AUTO: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "AG"},
    PresetMode.SLEEP: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "S"},
    PresetMode.GENTLE: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "GT"},
    PresetMode.TURBO: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "T"},
}
_AC29XX_SPEEDS: dict[str, dict[str, str]] = {
    PresetMode.SLEEP: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "S"},
    PresetMode.GENTLE: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "GT"},
    PresetMode.TURBO: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "T"},
}

# --- AC303x family ---
_AC303X_PRESET_MODES: dict[str, dict[str, str]] = {
    PresetMode.AUTO: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "AG"},
    PresetMode.SLEEP: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "S",
        PhilipsApi.SPEED: "s",
    },
    PresetMode.SLEEP_ALLERGY: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "AS",
        PhilipsApi.SPEED: "as",
    },
    PresetMode.SPEED_1: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "1",
    },
    PresetMode.SPEED_2: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "2",
    },
    PresetMode.TURBO: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "T",
        PhilipsApi.SPEED: "t",
    },
}
_AC303X_SPEEDS: dict[str, dict[str, str]] = {
    PresetMode.SLEEP: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "S",
        PhilipsApi.SPEED: "s",
    },
    PresetMode.SPEED_1: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "1",
    },
    PresetMode.SPEED_2: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "2",
    },
    PresetMode.TURBO: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "T",
        PhilipsApi.SPEED: "t",
    },
}

# --- AC305x family ---
_AC305X_PRESET_MODES: dict[str, dict[str, str]] = {
    PresetMode.AUTO: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "AG"},
    PresetMode.SLEEP: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "S",
        PhilipsApi.SPEED: "s",
    },
    PresetMode.SPEED_1: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "1",
    },
    PresetMode.SPEED_2: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "2",
    },
    PresetMode.TURBO: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "T",
        PhilipsApi.SPEED: "t",
    },
}
_AC305X_SPEEDS: dict[str, dict[str, str]] = {
    PresetMode.SLEEP: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "S",
        PhilipsApi.SPEED: "s",
    },
    PresetMode.SPEED_1: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "1",
    },
    PresetMode.SPEED_2: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "2",
    },
    PresetMode.TURBO: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "T",
        PhilipsApi.SPEED: "t",
    },
}

# --- AC32xx family ---
_AC32XX_PRESET_MODES: dict[str, dict[str, int]] = {
    PresetMode.AUTO: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 0,
    },
    PresetMode.MEDIUM: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 19,
    },
    PresetMode.TURBO: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 18,
    },
    PresetMode.SLEEP: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 17,
    },
}
_AC32XX_SPEEDS: dict[str, dict[str, int]] = {
    PresetMode.SPEED_1: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 1,
    },
    PresetMode.SPEED_2: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 2,
    },
    PresetMode.SPEED_3: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 3,
    },
    PresetMode.SPEED_4: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 4,
    },
    PresetMode.SPEED_5: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 5,
    },
}

# --- AC385x/50 family ---
_AC385X50_PRESET_MODES: dict[str, dict[str, str]] = {
    PresetMode.AUTO: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "AG"},
    PresetMode.SLEEP: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "S",
        PhilipsApi.SPEED: "s",
    },
    PresetMode.SPEED_1: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "1",
    },
    PresetMode.SPEED_2: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "2",
    },
    PresetMode.TURBO: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "T",
        PhilipsApi.SPEED: "t",
    },
}
_AC385X50_SPEEDS: dict[str, dict[str, str]] = {
    PresetMode.SLEEP: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "S",
        PhilipsApi.SPEED: "s",
    },
    PresetMode.SPEED_1: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "1",
    },
    PresetMode.SPEED_2: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "2",
    },
    PresetMode.TURBO: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "T",
        PhilipsApi.SPEED: "t",
    },
}

# --- AC385x/51 family ---
_AC385X51_PRESET_MODES: dict[str, dict[str, str]] = {
    PresetMode.AUTO: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "AG"},
    PresetMode.SLEEP: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "S",
        PhilipsApi.SPEED: "s",
    },
    PresetMode.SLEEP_ALLERGY: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "AS",
        PhilipsApi.SPEED: "as",
    },
    PresetMode.SPEED_1: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "1",
    },
    PresetMode.SPEED_2: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "2",
    },
    PresetMode.TURBO: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "T",
        PhilipsApi.SPEED: "t",
    },
}
_AC385X51_SPEEDS: dict[str, dict[str, str]] = {
    PresetMode.SLEEP: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "S",
        PhilipsApi.SPEED: "s",
    },
    PresetMode.SPEED_1: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "1",
    },
    PresetMode.SPEED_2: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "2",
    },
    PresetMode.TURBO: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "T",
        PhilipsApi.SPEED: "t",
    },
}

# --- AC4558 / AC4550 family ---
_AC4558_PRESET_MODES: dict[str, dict[str, str]] = {
    PresetMode.AUTO: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "AG",
        PhilipsApi.SPEED: "a",
    },
    PresetMode.GAS: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "F",
        PhilipsApi.SPEED: "a",
    },
    PresetMode.POLLUTION: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "P",
        PhilipsApi.SPEED: "a",
    },
    PresetMode.ALLERGEN: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "A",
        PhilipsApi.SPEED: "a",
    },
}
_AC4558_SPEEDS: dict[str, dict[str, str]] = {
    PresetMode.SLEEP: {PhilipsApi.POWER: "1", PhilipsApi.SPEED: "s"},
    PresetMode.SPEED_1: {PhilipsApi.POWER: "1", PhilipsApi.SPEED: "1"},
    PresetMode.SPEED_2: {PhilipsApi.POWER: "1", PhilipsApi.SPEED: "2"},
    PresetMode.TURBO: {PhilipsApi.POWER: "1", PhilipsApi.SPEED: "t"},
}

# --- AC5659 / AC5660 family ---
_AC5659_PRESET_MODES: dict[str, dict[str, str]] = {
    PresetMode.POLLUTION: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "P"},
    PresetMode.ALLERGEN: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "A"},
    PresetMode.BACTERIA: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "B"},
    PresetMode.SLEEP: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "s",
    },
    PresetMode.SPEED_1: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "1",
    },
    PresetMode.SPEED_2: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "2",
    },
    PresetMode.SPEED_3: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "3",
    },
    PresetMode.TURBO: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "t",
    },
}
_AC5659_SPEEDS: dict[str, dict[str, str]] = {
    PresetMode.SLEEP: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "s",
    },
    PresetMode.SPEED_1: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "1",
    },
    PresetMode.SPEED_2: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "2",
    },
    PresetMode.SPEED_3: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "3",
    },
    PresetMode.TURBO: {
        PhilipsApi.POWER: "1",
        PhilipsApi.MODE: "M",
        PhilipsApi.SPEED: "t",
    },
}

# --- AMFxxx family ---
_AMFXXX_PRESET_MODES: dict[str, dict[str, int]] = {
    PresetMode.AUTO: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 0,
    },
    PresetMode.SLEEP: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 17,
    },
    PresetMode.TURBO: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 18,
    },
}
_AMFXXX_SPEEDS: dict[str, dict[str, int]] = {
    PresetMode.SPEED_1: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 1,
    },
    PresetMode.SPEED_2: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 2,
    },
    PresetMode.SPEED_3: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 3,
    },
    PresetMode.SPEED_4: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 4,
    },
    PresetMode.SPEED_5: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 5,
    },
    PresetMode.SPEED_6: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 6,
    },
    PresetMode.SPEED_7: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 7,
    },
    PresetMode.SPEED_8: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 8,
    },
    PresetMode.SPEED_9: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 9,
    },
    PresetMode.SPEED_10: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 10,
    },
}

# --- HU1509/HU1510 family ---
_HU1509_PRESET_MODES: dict[str, dict[str, int]] = {
    PresetMode.AUTO: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 0,
    },
    PresetMode.SLEEP: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 17},
    PresetMode.MEDIUM: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 19},
    PresetMode.HIGH: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 65},
}
_HU1509_SPEEDS: dict[str, dict[str, int]] = {
    PresetMode.SLEEP: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 17},
    PresetMode.MEDIUM: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 19},
    PresetMode.HIGH: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 65},
}

# --- HU5710 family ---
_HU5710_PRESET_MODES: dict[str, dict[str, int]] = {
    PresetMode.AUTO: {
        PhilipsApi.NEW2_POWER: 1,
        PhilipsApi.NEW2_MODE_B: 0,
    },
    PresetMode.SLEEP: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 17},
    PresetMode.MEDIUM: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 19},
    PresetMode.HIGH: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 65},
}
_HU5710_SPEEDS: dict[str, dict[str, int]] = {
    PresetMode.SLEEP: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 17},
    PresetMode.MEDIUM: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 19},
    PresetMode.HIGH: {PhilipsApi.NEW2_POWER: 1, PhilipsApi.NEW2_MODE_B: 65},
}

# =============================================================================
# Shared DeviceModelConfig instances for identical models
# =============================================================================

# AC0850 Gen2 base config (shared by AC0850/11, /20, /31, /41, /70, /85)
_CONFIG_AC0850_GEN2 = DeviceModelConfig(
    api_generation=ApiGeneration.GEN2,
    preset_modes=_AC0850_GEN2_PRESET_MODES,
    speeds=_AC0850_GEN2_SPEEDS,
    # MRO: PhilipsAC085011 -> PhilipsNewGenericFan -> PhilipsGenericFanBase
    # switches from PhilipsNewGenericFan: []
    switches=[],
    # lights from PhilipsNewGenericFan: []
    lights=[],
    # selects from PhilipsNewGenericFan: [NEW_PREFERRED_INDEX]
    selects=[PhilipsApi.NEW_PREFERRED_INDEX],
    unavailable_filters=[PhilipsApi.FILTER_NANOPROTECT_PREFILTER],
)

# AC0850 Gen3 base config (shared by AC0850/11C, /20C, /31C, /41C, /70C, /81)
_CONFIG_AC0850_GEN3 = DeviceModelConfig(
    api_generation=ApiGeneration.GEN3,
    preset_modes=_AC0850_GEN3_PRESET_MODES,
    speeds=_AC0850_GEN3_SPEEDS,
    # MRO: PhilipsAC085011C -> PhilipsNew2GenericFan -> PhilipsGenericFanBase
    # switches from PhilipsNew2GenericFan: []
    switches=[],
    # lights from PhilipsNew2GenericFan: []
    lights=[],
    # selects from PhilipsNew2GenericFan: []
    selects=[],
    unavailable_filters=[PhilipsApi.FILTER_NANOPROTECT_PREFILTER],
)

# AC0950 config
_CONFIG_AC0950 = DeviceModelConfig(
    api_generation=ApiGeneration.GEN3,
    preset_modes=_AC0950_PRESET_MODES,
    speeds=_AC0950_SPEEDS,
    switches=[PhilipsApi.NEW2_CHILD_LOCK, PhilipsApi.NEW2_BEEP],
    lights=[PhilipsApi.NEW2_DISPLAY_BACKLIGHT3],
    selects=[PhilipsApi.NEW2_GAS_PREFERRED_INDEX, PhilipsApi.NEW2_TIMER2],
    unavailable_filters=[PhilipsApi.FILTER_NANOPROTECT_PREFILTER],
)

# AC29xx config (shared by AC2936, AC2939, AC2958, AC2959)
_CONFIG_AC29XX = DeviceModelConfig(
    api_generation=ApiGeneration.GEN1,
    preset_modes=_AC29XX_PRESET_MODES,
    speeds=_AC29XX_SPEEDS,
    switches=[PhilipsApi.CHILD_LOCK],
    lights=[PhilipsApi.DISPLAY_BACKLIGHT, PhilipsApi.LIGHT_BRIGHTNESS],
    selects=[PhilipsApi.PREFERRED_INDEX],
)

# AC303x config (shared by AC3033, AC3036, AC3039)
_CONFIG_AC303X = DeviceModelConfig(
    api_generation=ApiGeneration.GEN1,
    preset_modes=_AC303X_PRESET_MODES,
    speeds=_AC303X_SPEEDS,
    lights=[PhilipsApi.DISPLAY_BACKLIGHT, PhilipsApi.LIGHT_BRIGHTNESS],
    selects=[PhilipsApi.GAS_PREFERRED_INDEX],
)

# AC305x config (shared by AC3055, AC3059)
_CONFIG_AC305X = DeviceModelConfig(
    api_generation=ApiGeneration.GEN1,
    preset_modes=_AC305X_PRESET_MODES,
    speeds=_AC305X_SPEEDS,
    lights=[PhilipsApi.DISPLAY_BACKLIGHT, PhilipsApi.LIGHT_BRIGHTNESS],
    selects=[PhilipsApi.GAS_PREFERRED_INDEX],
)

# AC32xx base config
_CONFIG_AC32XX = DeviceModelConfig(
    api_generation=ApiGeneration.GEN3,
    preset_modes=_AC32XX_PRESET_MODES,
    speeds=_AC32XX_SPEEDS,
    lights=[PhilipsApi.NEW2_DISPLAY_BACKLIGHT3],
    switches=[
        PhilipsApi.NEW2_CHILD_LOCK,
        PhilipsApi.NEW2_BEEP,
        PhilipsApi.NEW2_AUTO_PLUS_AI,
    ],
    selects=[
        PhilipsApi.NEW2_TIMER2,
        PhilipsApi.NEW2_LAMP_MODE,
        PhilipsApi.NEW2_PREFERRED_INDEX,
    ],
)

# AC3210/AC3220/AC3221 config (overrides selects from AC32xx)
_CONFIG_AC3210 = DeviceModelConfig(
    api_generation=ApiGeneration.GEN3,
    preset_modes=_AC32XX_PRESET_MODES,
    speeds=_AC32XX_SPEEDS,
    lights=[PhilipsApi.NEW2_DISPLAY_BACKLIGHT3],
    switches=[
        PhilipsApi.NEW2_CHILD_LOCK,
        PhilipsApi.NEW2_BEEP,
        PhilipsApi.NEW2_AUTO_PLUS_AI,
    ],
    selects=[PhilipsApi.NEW_PREFERRED_INDEX],
)

# AC385x/50 config (shared by AC3854/50, AC3858/50)
_CONFIG_AC385X50 = DeviceModelConfig(
    api_generation=ApiGeneration.GEN1,
    preset_modes=_AC385X50_PRESET_MODES,
    speeds=_AC385X50_SPEEDS,
    lights=[PhilipsApi.DISPLAY_BACKLIGHT, PhilipsApi.LIGHT_BRIGHTNESS],
    selects=[PhilipsApi.GAS_PREFERRED_INDEX],
)

# AC385x/51 config (shared by AC3854/51, AC3858/51, AC3858/83, AC3858/86)
_CONFIG_AC385X51 = DeviceModelConfig(
    api_generation=ApiGeneration.GEN1,
    preset_modes=_AC385X51_PRESET_MODES,
    speeds=_AC385X51_SPEEDS,
    switches=[PhilipsApi.CHILD_LOCK],
    lights=[PhilipsApi.DISPLAY_BACKLIGHT, PhilipsApi.LIGHT_BRIGHTNESS],
    selects=[PhilipsApi.GAS_PREFERRED_INDEX],
)

# AC4220/AC4221 config (same as AC32xx but with explicit selects)
_CONFIG_AC4220 = DeviceModelConfig(
    api_generation=ApiGeneration.GEN3,
    preset_modes=_AC32XX_PRESET_MODES,
    speeds=_AC32XX_SPEEDS,
    lights=[PhilipsApi.NEW2_DISPLAY_BACKLIGHT3],
    switches=[
        PhilipsApi.NEW2_CHILD_LOCK,
        PhilipsApi.NEW2_BEEP,
        PhilipsApi.NEW2_AUTO_PLUS_AI,
    ],
    selects=[
        PhilipsApi.NEW2_TIMER2,
        PhilipsApi.NEW2_LAMP_MODE,
        PhilipsApi.NEW2_PREFERRED_INDEX,
    ],
)

# AC4558/AC4550 config
_CONFIG_AC4558 = DeviceModelConfig(
    api_generation=ApiGeneration.GEN1,
    preset_modes=_AC4558_PRESET_MODES,
    speeds=_AC4558_SPEEDS,
    switches=[PhilipsApi.CHILD_LOCK],
    lights=[PhilipsApi.DISPLAY_BACKLIGHT, PhilipsApi.LIGHT_BRIGHTNESS],
    selects=[PhilipsApi.PREFERRED_INDEX],
)

# AC5659/AC5660 config
_CONFIG_AC5659 = DeviceModelConfig(
    api_generation=ApiGeneration.GEN1,
    preset_modes=_AC5659_PRESET_MODES,
    speeds=_AC5659_SPEEDS,
    lights=[PhilipsApi.DISPLAY_BACKLIGHT, PhilipsApi.LIGHT_BRIGHTNESS],
    selects=[PhilipsApi.PREFERRED_INDEX],
)

# HU1509/HU1510 config (both map to PhilipsHU1510 class in model_to_class)
_CONFIG_HU1509 = DeviceModelConfig(
    api_generation=ApiGeneration.GEN3,
    preset_modes=_HU1509_PRESET_MODES,
    speeds=_HU1509_SPEEDS,
    create_fan=False,
    switches=[
        PhilipsApi.NEW2_BEEP,
        PhilipsApi.NEW2_STANDBY_SENSORS,
    ],
    lights=[PhilipsApi.NEW2_DISPLAY_BACKLIGHT4],
    selects=[
        PhilipsApi.NEW2_TIMER2,
        PhilipsApi.NEW2_LAMP_MODE2,
        PhilipsApi.NEW2_AMBIENT_LIGHT_MODE,
    ],
    binary_sensors=[PhilipsApi.NEW2_ERROR_CODE],
    humidifiers=[PhilipsApi.NEW2_HUMIDITY_TARGET2],
)

# =============================================================================
# DEVICE_MODELS: The main mapping
# =============================================================================

DEVICE_MODELS: dict[str, DeviceModelConfig] = {
    # =========================================================================
    # AC0650 family (e.g. AC0650/10)
    # =========================================================================
    FanModel.AC0650: _CONFIG_AC0850_GEN2,
    # =========================================================================
    # AC0850 family
    # =========================================================================
    FanModel.AC0850_11: _CONFIG_AC0850_GEN2,
    FanModel.AC0850_11C: _CONFIG_AC0850_GEN3,
    FanModel.AC0850_20: _CONFIG_AC0850_GEN2,
    FanModel.AC0850_20C: _CONFIG_AC0850_GEN3,
    FanModel.AC0850_31: _CONFIG_AC0850_GEN2,
    FanModel.AC0850_31C: _CONFIG_AC0850_GEN3,
    FanModel.AC0850_41: _CONFIG_AC0850_GEN2,
    FanModel.AC0850_41C: _CONFIG_AC0850_GEN3,
    FanModel.AC0850_70: _CONFIG_AC0850_GEN2,
    FanModel.AC0850_70C: _CONFIG_AC0850_GEN3,
    FanModel.AC0850_81: _CONFIG_AC0850_GEN3,
    FanModel.AC0850_85: _CONFIG_AC0850_GEN2,
    # =========================================================================
    # AC0950 family
    # =========================================================================
    FanModel.AC0950: _CONFIG_AC0950,
    FanModel.AC0951: _CONFIG_AC0950,
    # =========================================================================
    # AC1214
    # =========================================================================
    FanModel.AC1214: DeviceModelConfig(
        api_generation=ApiGeneration.GEN1,
        preset_modes={
            PresetMode.AUTO: {PhilipsApi.MODE: "P"},
            PresetMode.ALLERGEN: {PhilipsApi.MODE: "A"},
            PresetMode.NIGHT: {PhilipsApi.MODE: "N"},
            PresetMode.SPEED_1: {PhilipsApi.MODE: "M", PhilipsApi.SPEED: "1"},
            PresetMode.SPEED_2: {PhilipsApi.MODE: "M", PhilipsApi.SPEED: "2"},
            PresetMode.SPEED_3: {PhilipsApi.MODE: "M", PhilipsApi.SPEED: "3"},
            PresetMode.TURBO: {PhilipsApi.MODE: "M", PhilipsApi.SPEED: "t"},
        },
        speeds={
            PresetMode.NIGHT: {PhilipsApi.MODE: "N"},
            PresetMode.SPEED_1: {PhilipsApi.MODE: "M", PhilipsApi.SPEED: "1"},
            PresetMode.SPEED_2: {PhilipsApi.MODE: "M", PhilipsApi.SPEED: "2"},
            PresetMode.SPEED_3: {PhilipsApi.MODE: "M", PhilipsApi.SPEED: "3"},
            PresetMode.TURBO: {PhilipsApi.MODE: "M", PhilipsApi.SPEED: "t"},
        },
        switches=[PhilipsApi.CHILD_LOCK],
        lights=[PhilipsApi.DISPLAY_BACKLIGHT, PhilipsApi.LIGHT_BRIGHTNESS],
        selects=[PhilipsApi.PREFERRED_INDEX],
        requires_mode_cycling=True,
    ),
    # =========================================================================
    # AC1715
    # =========================================================================
    FanModel.AC1715: DeviceModelConfig(
        api_generation=ApiGeneration.GEN2,
        preset_modes={
            PresetMode.AUTO: {
                PhilipsApi.NEW_POWER: "ON",
                PhilipsApi.NEW_MODE: "Auto General",
            },
            PresetMode.SPEED_1: {
                PhilipsApi.NEW_POWER: "ON",
                PhilipsApi.NEW_MODE: "Gentle/Speed 1",
            },
            PresetMode.SPEED_2: {
                PhilipsApi.NEW_POWER: "ON",
                PhilipsApi.NEW_MODE: "Speed 2",
            },
            PresetMode.TURBO: {
                PhilipsApi.NEW_POWER: "ON",
                PhilipsApi.NEW_MODE: "Turbo",
            },
            PresetMode.SLEEP: {
                PhilipsApi.NEW_POWER: "ON",
                PhilipsApi.NEW_MODE: "Sleep",
            },
        },
        speeds={
            PresetMode.SLEEP: {
                PhilipsApi.NEW_POWER: "ON",
                PhilipsApi.NEW_MODE: "Sleep",
            },
            PresetMode.SPEED_1: {
                PhilipsApi.NEW_POWER: "ON",
                PhilipsApi.NEW_MODE: "Gentle/Speed 1",
            },
            PresetMode.SPEED_2: {
                PhilipsApi.NEW_POWER: "ON",
                PhilipsApi.NEW_MODE: "Speed 2",
            },
            PresetMode.TURBO: {
                PhilipsApi.NEW_POWER: "ON",
                PhilipsApi.NEW_MODE: "Turbo",
            },
        },
        # MRO: PhilipsAC1715 -> PhilipsNewGenericFan
        # lights override from AC1715: [NEW_DISPLAY_BACKLIGHT]
        lights=[PhilipsApi.NEW_DISPLAY_BACKLIGHT],
        # switches from PhilipsNewGenericFan: []
        switches=[],
        # selects from PhilipsNewGenericFan: [NEW_PREFERRED_INDEX]
        selects=[PhilipsApi.NEW_PREFERRED_INDEX],
    ),
    # =========================================================================
    # AC2729
    # =========================================================================
    FanModel.AC2729: DeviceModelConfig(
        api_generation=ApiGeneration.GEN1,
        preset_modes={
            PresetMode.AUTO: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "P"},
            PresetMode.ALLERGEN: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "A"},
            PresetMode.NIGHT: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "S",
                PhilipsApi.SPEED: "s",
            },
            PresetMode.SPEED_1: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "1",
            },
            PresetMode.SPEED_2: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "2",
            },
            PresetMode.SPEED_3: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "3",
            },
            PresetMode.TURBO: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "t",
            },
        },
        speeds={
            PresetMode.NIGHT: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "S",
                PhilipsApi.SPEED: "s",
            },
            PresetMode.SPEED_1: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "1",
            },
            PresetMode.SPEED_2: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "2",
            },
            PresetMode.SPEED_3: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "3",
            },
            PresetMode.TURBO: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "t",
            },
        },
        switches=[PhilipsApi.CHILD_LOCK, PhilipsApi.BEEP],
        lights=[PhilipsApi.DISPLAY_BACKLIGHT, PhilipsApi.LIGHT_BRIGHTNESS],
        selects=[PhilipsApi.PREFERRED_INDEX],
        humidifiers=[PhilipsApi.HUMIDITY_TARGET],
        binary_sensors=[PhilipsApi.ERROR_CODE],
    ),
    # =========================================================================
    # AC2889
    # =========================================================================
    FanModel.AC2889: DeviceModelConfig(
        api_generation=ApiGeneration.GEN1,
        preset_modes={
            PresetMode.AUTO: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "P"},
            PresetMode.ALLERGEN: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "A"},
            PresetMode.BACTERIA: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "B"},
            PresetMode.SLEEP: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "s",
            },
            PresetMode.SPEED_1: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "1",
            },
            PresetMode.SPEED_2: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "2",
            },
            PresetMode.SPEED_3: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "3",
            },
            PresetMode.TURBO: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "t",
            },
        },
        speeds={
            PresetMode.SLEEP: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "s",
            },
            PresetMode.SPEED_1: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "1",
            },
            PresetMode.SPEED_2: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "2",
            },
            PresetMode.SPEED_3: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "3",
            },
            PresetMode.TURBO: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "t",
            },
        },
        # AC2889 has no AVAILABLE_SWITCHES defined, inherits [] from PhilipsGenericFan
        switches=[],
        lights=[PhilipsApi.DISPLAY_BACKLIGHT, PhilipsApi.LIGHT_BRIGHTNESS],
        selects=[PhilipsApi.PREFERRED_INDEX],
    ),
    # =========================================================================
    # AC29xx family
    # =========================================================================
    FanModel.AC2936: _CONFIG_AC29XX,
    FanModel.AC2939: _CONFIG_AC29XX,
    FanModel.AC2958: _CONFIG_AC29XX,
    FanModel.AC2959: _CONFIG_AC29XX,
    # =========================================================================
    # AC303x family
    # =========================================================================
    FanModel.AC3033: _CONFIG_AC303X,
    FanModel.AC3036: _CONFIG_AC303X,
    FanModel.AC3039: _CONFIG_AC303X,
    # =========================================================================
    # AC305x family
    # =========================================================================
    FanModel.AC3055: _CONFIG_AC305X,
    FanModel.AC3059: _CONFIG_AC305X,
    # =========================================================================
    # AC32xx family
    # =========================================================================
    FanModel.AC3210: _CONFIG_AC3210,
    FanModel.AC3220: _CONFIG_AC3210,
    FanModel.AC3221: _CONFIG_AC3210,
    # =========================================================================
    # AC3259
    # =========================================================================
    FanModel.AC3259: DeviceModelConfig(
        api_generation=ApiGeneration.GEN1,
        preset_modes={
            PresetMode.AUTO: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "P"},
            PresetMode.ALLERGEN: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "A"},
            PresetMode.BACTERIA: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "B"},
            PresetMode.SLEEP: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "s",
            },
            PresetMode.SPEED_1: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "1",
            },
            PresetMode.SPEED_2: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "2",
            },
            PresetMode.SPEED_3: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "3",
            },
            PresetMode.TURBO: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "t",
            },
        },
        speeds={
            PresetMode.SLEEP: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "s",
            },
            PresetMode.SPEED_1: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "1",
            },
            PresetMode.SPEED_2: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "2",
            },
            PresetMode.SPEED_3: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "3",
            },
            PresetMode.TURBO: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "t",
            },
        },
        lights=[PhilipsApi.DISPLAY_BACKLIGHT, PhilipsApi.LIGHT_BRIGHTNESS],
        selects=[PhilipsApi.GAS_PREFERRED_INDEX],
    ),
    # =========================================================================
    # AC3420 / AC3421
    # =========================================================================
    FanModel.AC3420: DeviceModelConfig(
        api_generation=ApiGeneration.GEN3,
        preset_modes=_AC0950_PRESET_MODES,
        speeds=_AC0950_SPEEDS,
        # MRO: PhilipsAC3420 -> PhilipsAC0950 -> PhilipsNew2GenericFan
        # switches from AC0950: [NEW2_CHILD_LOCK, NEW2_BEEP]
        switches=[PhilipsApi.NEW2_CHILD_LOCK, PhilipsApi.NEW2_BEEP],
        # lights from AC0950: [NEW2_DISPLAY_BACKLIGHT3]
        lights=[PhilipsApi.NEW2_DISPLAY_BACKLIGHT3],
        # selects override from AC3420: [NEW2_LAMP_MODE]
        selects=[PhilipsApi.NEW2_LAMP_MODE],
        unavailable_filters=[PhilipsApi.FILTER_NANOPROTECT_PREFILTER],
        humidifiers=[PhilipsApi.NEW2_HUMIDITY_TARGET],
        binary_sensors=["AC3420_WATER_LEVEL"],
    ),
    FanModel.AC3421: DeviceModelConfig(
        api_generation=ApiGeneration.GEN3,
        preset_modes=_AC0950_PRESET_MODES,
        speeds=_AC0950_SPEEDS,
        switches=[PhilipsApi.NEW2_CHILD_LOCK, PhilipsApi.NEW2_BEEP],
        lights=[PhilipsApi.NEW2_DISPLAY_BACKLIGHT3],
        selects=[PhilipsApi.NEW2_LAMP_MODE],
        unavailable_filters=[PhilipsApi.FILTER_NANOPROTECT_PREFILTER],
        humidifiers=[PhilipsApi.NEW2_HUMIDITY_TARGET],
        binary_sensors=["AC3420_WATER_LEVEL"],
    ),
    # =========================================================================
    # AC3737
    # =========================================================================
    FanModel.AC3737: DeviceModelConfig(
        api_generation=ApiGeneration.GEN3,
        preset_modes={
            PresetMode.AUTO: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 2,
                PhilipsApi.NEW2_MODE_B: 0,
            },
            PresetMode.SLEEP: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 2,
                PhilipsApi.NEW2_MODE_B: 17,
            },
            PresetMode.TURBO: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 3,
                PhilipsApi.NEW2_MODE_B: 18,
            },
        },
        speeds={
            PresetMode.SLEEP: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 2,
                PhilipsApi.NEW2_MODE_B: 17,
            },
            PresetMode.SPEED_1: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 2,
                PhilipsApi.NEW2_MODE_B: 1,
            },
            PresetMode.SPEED_2: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 2,
                PhilipsApi.NEW2_MODE_B: 2,
            },
            PresetMode.TURBO: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 3,
                PhilipsApi.NEW2_MODE_B: 18,
            },
        },
        lights=[PhilipsApi.NEW2_DISPLAY_BACKLIGHT2],
        switches=[PhilipsApi.NEW2_CHILD_LOCK],
        unavailable_sensors=[PhilipsApi.NEW2_FAN_SPEED],
        binary_sensors=[PhilipsApi.NEW2_ERROR_CODE, PhilipsApi.NEW2_MODE_A],
        humidifiers=[PhilipsApi.NEW2_HUMIDITY_TARGET],
    ),
    # =========================================================================
    # AC3829
    # =========================================================================
    FanModel.AC3829: DeviceModelConfig(
        api_generation=ApiGeneration.GEN1,
        preset_modes={
            PresetMode.AUTO: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "P"},
            PresetMode.ALLERGEN: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "A"},
            PresetMode.SLEEP: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "S",
                PhilipsApi.SPEED: "s",
            },
            PresetMode.SPEED_1: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "1",
            },
            PresetMode.SPEED_2: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "2",
            },
            PresetMode.SPEED_3: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "3",
            },
            PresetMode.TURBO: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "t",
            },
        },
        speeds={
            PresetMode.SLEEP: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "S",
                PhilipsApi.SPEED: "s",
            },
            PresetMode.SPEED_1: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "1",
            },
            PresetMode.SPEED_2: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "2",
            },
            PresetMode.SPEED_3: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "3",
            },
            PresetMode.TURBO: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "t",
            },
        },
        switches=[PhilipsApi.CHILD_LOCK],
        lights=[PhilipsApi.DISPLAY_BACKLIGHT, PhilipsApi.LIGHT_BRIGHTNESS],
        selects=[PhilipsApi.GAS_PREFERRED_INDEX],
        binary_sensors=[PhilipsApi.ERROR_CODE],
        humidifiers=[PhilipsApi.HUMIDITY_TARGET],
    ),
    # =========================================================================
    # AC3836
    # =========================================================================
    FanModel.AC3836: DeviceModelConfig(
        api_generation=ApiGeneration.GEN1,
        preset_modes={
            PresetMode.AUTO: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "AG",
                PhilipsApi.SPEED: "1",
            },
            PresetMode.SLEEP: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "S",
                PhilipsApi.SPEED: "s",
            },
            PresetMode.TURBO: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "T",
                PhilipsApi.SPEED: "t",
            },
        },
        speeds={
            PresetMode.SLEEP: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "S",
                PhilipsApi.SPEED: "s",
            },
            PresetMode.TURBO: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "T",
                PhilipsApi.SPEED: "t",
            },
        },
        lights=[PhilipsApi.DISPLAY_BACKLIGHT, PhilipsApi.LIGHT_BRIGHTNESS],
        selects=[PhilipsApi.GAS_PREFERRED_INDEX],
    ),
    # =========================================================================
    # AC385x/50 family
    # =========================================================================
    FanModel.AC3854_50: _CONFIG_AC385X50,
    FanModel.AC3858_50: _CONFIG_AC385X50,
    # =========================================================================
    # AC385x/51 family
    # =========================================================================
    FanModel.AC3854_51: _CONFIG_AC385X51,
    FanModel.AC3858_51: _CONFIG_AC385X51,
    FanModel.AC3858_83: _CONFIG_AC385X51,
    FanModel.AC3858_86: _CONFIG_AC385X51,
    # =========================================================================
    # AC4220 / AC4221
    # =========================================================================
    FanModel.AC4220: _CONFIG_AC4220,
    FanModel.AC4221: _CONFIG_AC4220,
    # =========================================================================
    # AC4236
    # =========================================================================
    FanModel.AC4236: DeviceModelConfig(
        api_generation=ApiGeneration.GEN1,
        preset_modes={
            PresetMode.AUTO: {PhilipsApi.POWER: "1", PhilipsApi.MODE: "AG"},
            PresetMode.SLEEP: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "S",
                PhilipsApi.SPEED: "s",
            },
            PresetMode.SLEEP_ALLERGY: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "AS",
                PhilipsApi.SPEED: "as",
            },
            PresetMode.SPEED_1: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "1",
            },
            PresetMode.SPEED_2: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "2",
            },
            PresetMode.TURBO: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "T",
                PhilipsApi.SPEED: "t",
            },
        },
        speeds={
            PresetMode.SLEEP: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "S",
                PhilipsApi.SPEED: "s",
            },
            PresetMode.SPEED_1: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "1",
            },
            PresetMode.SPEED_2: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "M",
                PhilipsApi.SPEED: "2",
            },
            PresetMode.TURBO: {
                PhilipsApi.POWER: "1",
                PhilipsApi.MODE: "T",
                PhilipsApi.SPEED: "t",
            },
        },
        switches=[PhilipsApi.CHILD_LOCK],
        lights=[PhilipsApi.DISPLAY_BACKLIGHT, PhilipsApi.LIGHT_BRIGHTNESS],
        selects=[PhilipsApi.PREFERRED_INDEX],
    ),
    # =========================================================================
    # AC4550 / AC4558
    # =========================================================================
    FanModel.AC4550: _CONFIG_AC4558,
    FanModel.AC4558: _CONFIG_AC4558,
    # =========================================================================
    # AC5659 / AC5660
    # =========================================================================
    FanModel.AC5659: _CONFIG_AC5659,
    FanModel.AC5660: _CONFIG_AC5659,
    # =========================================================================
    # AMF765
    # =========================================================================
    FanModel.AMF765: DeviceModelConfig(
        api_generation=ApiGeneration.GEN3,
        preset_modes=_AMFXXX_PRESET_MODES,
        speeds=_AMFXXX_SPEEDS,
        lights=[PhilipsApi.NEW2_DISPLAY_BACKLIGHT],
        switches=[
            PhilipsApi.NEW2_CHILD_LOCK,
            PhilipsApi.NEW2_BEEP,
            PhilipsApi.NEW2_STANDBY_SENSORS,
            PhilipsApi.NEW2_AUTO_PLUS_AI,
        ],
        # AMF765 overrides selects from AMFxxx
        selects=[PhilipsApi.NEW2_CIRCULATION],
        numbers=[PhilipsApi.NEW2_OSCILLATION],
        unavailable_sensors=[PhilipsApi.NEW2_GAS],
    ),
    # =========================================================================
    # AMF870
    # =========================================================================
    FanModel.AMF870: DeviceModelConfig(
        api_generation=ApiGeneration.GEN3,
        preset_modes=_AMFXXX_PRESET_MODES,
        speeds=_AMFXXX_SPEEDS,
        lights=[PhilipsApi.NEW2_DISPLAY_BACKLIGHT],
        switches=[
            PhilipsApi.NEW2_CHILD_LOCK,
            PhilipsApi.NEW2_BEEP,
            PhilipsApi.NEW2_STANDBY_SENSORS,
            PhilipsApi.NEW2_AUTO_PLUS_AI,
        ],
        # AMF870 overrides selects from AMFxxx
        selects=[
            PhilipsApi.NEW2_GAS_PREFERRED_INDEX,
            PhilipsApi.NEW2_HEATING,
        ],
        # AMF870 overrides numbers from AMFxxx
        numbers=[PhilipsApi.NEW2_TARGET_TEMP],
    ),
    # =========================================================================
    # CX3120
    # =========================================================================
    FanModel.CX3120: DeviceModelConfig(
        api_generation=ApiGeneration.GEN3,
        preset_modes={
            PresetMode.AUTO_PLUS: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 3,
                PhilipsApi.NEW2_MODE_B: 0,
            },
            PresetMode.VENTILATION: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 1,
                PhilipsApi.NEW2_MODE_B: -127,
            },
            PresetMode.LOW: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 3,
                PhilipsApi.NEW2_MODE_B: 66,
            },
            PresetMode.MEDIUM: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 3,
                PhilipsApi.NEW2_MODE_B: 67,
            },
            PresetMode.HIGH: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 3,
                PhilipsApi.NEW2_MODE_B: 65,
            },
        },
        speeds={
            PresetMode.LOW: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 3,
                PhilipsApi.NEW2_MODE_B: 66,
            },
            PresetMode.MEDIUM: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 3,
                PhilipsApi.NEW2_MODE_B: 67,
            },
            PresetMode.HIGH: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 3,
                PhilipsApi.NEW2_MODE_B: 65,
            },
        },
        oscillation={
            PhilipsApi.NEW2_OSCILLATION: PhilipsApi.OSCILLATION_MAP3,
        },
        unavailable_sensors=[PhilipsApi.NEW2_FAN_SPEED, PhilipsApi.NEW2_GAS],
        selects=[PhilipsApi.NEW2_TIMER2],
        numbers=[PhilipsApi.NEW2_TARGET_TEMP],
        switches=[PhilipsApi.NEW2_CHILD_LOCK],
        heaters=[PhilipsApi.NEW2_TARGET_TEMP],
    ),
    # =========================================================================
    # CX5120
    # =========================================================================
    FanModel.CX5120: DeviceModelConfig(
        api_generation=ApiGeneration.GEN3,
        preset_modes={
            PresetMode.AUTO: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 3,
                PhilipsApi.NEW2_MODE_B: 0,
            },
            PresetMode.VENTILATION: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 1,
                PhilipsApi.NEW2_MODE_B: -127,
            },
            PresetMode.LOW: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 3,
                PhilipsApi.NEW2_MODE_B: 66,
            },
            PresetMode.HIGH: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 3,
                PhilipsApi.NEW2_MODE_B: 65,
            },
        },
        speeds={
            PresetMode.LOW: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 3,
                PhilipsApi.NEW2_MODE_B: 66,
            },
            PresetMode.HIGH: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 3,
                PhilipsApi.NEW2_MODE_B: 65,
            },
        },
        oscillation={
            PhilipsApi.NEW2_OSCILLATION: PhilipsApi.OSCILLATION_MAP2,
        },
        lights=[PhilipsApi.NEW2_DISPLAY_BACKLIGHT2],
        switches=[PhilipsApi.NEW2_BEEP],
        unavailable_sensors=[PhilipsApi.NEW2_FAN_SPEED, PhilipsApi.NEW2_GAS],
        selects=[PhilipsApi.NEW2_TIMER2],
        numbers=[PhilipsApi.NEW2_TARGET_TEMP],
        heaters=[PhilipsApi.NEW2_TARGET_TEMP],
    ),
    # =========================================================================
    # CX3550
    # =========================================================================
    FanModel.CX3550: DeviceModelConfig(
        api_generation=ApiGeneration.GEN3,
        preset_modes={
            PresetMode.SPEED_1: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 1,
                PhilipsApi.NEW2_MODE_B: 1,
                PhilipsApi.NEW2_MODE_C: 1,
            },
            PresetMode.SPEED_2: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 1,
                PhilipsApi.NEW2_MODE_B: 2,
                PhilipsApi.NEW2_MODE_C: 2,
            },
            PresetMode.SPEED_3: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 1,
                PhilipsApi.NEW2_MODE_B: 3,
                PhilipsApi.NEW2_MODE_C: 3,
            },
            PresetMode.NATURAL: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 1,
                PhilipsApi.NEW2_MODE_B: -126,
                PhilipsApi.NEW2_MODE_C: 1,
            },
            PresetMode.SLEEP: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 1,
                PhilipsApi.NEW2_MODE_B: 17,
                PhilipsApi.NEW2_MODE_C: 2,
            },
        },
        speeds={
            PresetMode.SPEED_1: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 1,
                PhilipsApi.NEW2_MODE_B: 1,
                PhilipsApi.NEW2_MODE_C: 1,
            },
            PresetMode.SPEED_2: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 1,
                PhilipsApi.NEW2_MODE_B: 2,
                PhilipsApi.NEW2_MODE_C: 2,
            },
            PresetMode.SPEED_3: {
                PhilipsApi.NEW2_POWER: 1,
                PhilipsApi.NEW2_MODE_A: 1,
                PhilipsApi.NEW2_MODE_B: 3,
                PhilipsApi.NEW2_MODE_C: 3,
            },
        },
        oscillation={
            PhilipsApi.NEW2_OSCILLATION: PhilipsApi.OSCILLATION_MAP2,
        },
        switches=[PhilipsApi.NEW2_BEEP],
        selects=[PhilipsApi.NEW2_TIMER2],
    ),
    # =========================================================================
    # HU1509 / HU1510
    # =========================================================================
    FanModel.HU1509: _CONFIG_HU1509,
    FanModel.HU1510: _CONFIG_HU1509,
    # =========================================================================
    # HU5710
    # =========================================================================
    FanModel.HU5710: DeviceModelConfig(
        api_generation=ApiGeneration.GEN3,
        preset_modes=_HU5710_PRESET_MODES,
        speeds=_HU5710_SPEEDS,
        create_fan=False,
        switches=[
            PhilipsApi.NEW2_CHILD_LOCK,
            PhilipsApi.NEW2_BEEP,
            PhilipsApi.NEW2_QUICKDRY_MODE,
            PhilipsApi.NEW2_AUTO_QUICKDRY_MODE,
            PhilipsApi.NEW2_STANDBY_SENSORS,
        ],
        lights=[PhilipsApi.NEW2_DISPLAY_BACKLIGHT4],
        selects=[
            PhilipsApi.NEW2_TIMER2,
            PhilipsApi.NEW2_LAMP_MODE2,
            PhilipsApi.NEW2_AMBIENT_LIGHT_MODE,
        ],
        binary_sensors=[PhilipsApi.NEW2_ERROR_CODE],
        humidifiers=[PhilipsApi.NEW2_HUMIDITY_TARGET2],
    ),
}
