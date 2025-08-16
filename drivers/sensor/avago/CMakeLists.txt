# Copyright (c) 2025 Tim Schrader <tim.schrader92@gmail.com>
# SPDX-License-Identifier: Apache-2.0

# zephyr-keep-sorted-start
add_subdirectory_ifdef(CONFIG_APDS9253 apds9253)
add_subdirectory_ifdef(CONFIG_APDS9306 apds9306)
add_subdirectory_ifdef(CONFIG_APDS9960 apds9960)
# zephyr-keep-sorted-stop
