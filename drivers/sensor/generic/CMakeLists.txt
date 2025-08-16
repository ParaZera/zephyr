# Copyright (c) 2025 Tim Schrader <tim.schrader92@gmail.com>
# SPDX-License-Identifier: Apache-2.0

# zephyr-keep-sorted-start
add_subdirectory_ifdef(CONFIG_CURRENT_AMP current_amp)
add_subdirectory_ifdef(CONFIG_HC_SR04 hc_sr04)
add_subdirectory_ifdef(CONFIG_LM35 lm35)
add_subdirectory_ifdef(CONFIG_LM75 lm75)
add_subdirectory_ifdef(CONFIG_LM77 lm77)
add_subdirectory_ifdef(CONFIG_NTC_THERMISTOR ntc_thermistor)
add_subdirectory_ifdef(CONFIG_VOLTAGE_DIVIDER voltage_divider)
# zephyr-keep-sorted-stop
