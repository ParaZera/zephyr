# Common

When there are sub-configs for a enable/disable toggle, the toggle should be a `menuconfig` item and the sub-configurations should be grouped in this menu

# Drivers

- a driver config option should have the the `driver` suffix
    - rationale: make it clear in searches that the config option enables a driver

- KConfig identifiers should be the same as the devicetree compatible string

## Sensor Drivers

- a sensor driver option should have the `sensor driver` suffix (lowercase)
    - rationale: same as for `driver`


- a sensor driver option name should be in the following style: `{SENSOR ABBREV} {MANUFACTURER} {SENSOR TYPE} sensor driver` where:
    - `{SENSOR ABBREV}` is a short abbreviation or name of the sensor (e.g. `BMP580` or `BMI430)
    - `{DESCRIPTOR}` is a short descriptor on what the sensor is measuring (e.g. `battery voltage`, `pressure`, `inertial measurement unit`, `IMU`)
    - `{MANUFACTURER}` is an optional field with the Name of the Manufacturer in braces (`()`). When there is only one manufacturer, it should be provided
    - Full examples: `BMP580 pressure sensor driver`, `BMI430 IMU sensor driver`, `NPM2100 battery boltage sensor driver`
    - the supported bus types should not be part of the name. (If several bus types are supported, there should be configs for tha)


- ? If there are many sensors from a
- ? Maybe Prefix the Manufacturer if there are many drivers from that brand? If yes, it should be


- Drivers should be enabled by a boolean value
    - The name of the


- When a driver has one or more configuration options (e.g. `XXX_THREAD_STACK_SIZE`), the config option to enable the driver should be a `menuconfig` with the config options grouped under it



# TODO!

- Merge AVAGO and BROADCOM Sensor definitions
- Move `apds9253`, `apds9306`, and `apds9960` sensor drivers into one `avago` directory
- Rename `ene_tach_kb1200` sensor driver
- `hc_sr04` sensor driver
- how to use
- `LM35`, `LM75` sensor driver are manufactured by several companies (or are they TI?), how do deal with the KConfig identifier?
- `LM77` is manufactured only by TI?!
- `sensor shell` and `sensor shell command` update naming to not assume dependency


- sensor driver: is the TLE9104_DIAGNOSTICS (infinion) right here?
- nordic temperature sensor naming as edge-case (or nuvoton NPCX)

- `stmemsc` from sensor/st/stmemsc directory to wherever else
