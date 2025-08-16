.. _kconfig_style:

Kconfig Style Guidelines
########################

General Recommendations
***********************

  * Line length of 100 columns or fewer.
  * Indent with tabs, except for ``help`` entry text which should be placed at
    one tab plus two extra spaces.
  * Leave a single empty line between option declarations.
  * Use Statements like ``select`` carefully, see
    :ref:`kconfig_tips_and_tricks` for more information.
  * Format comments as ``# Comment`` rather than ``#Comment``
  * Insert an empty line before/after each top-level ``if`` and ``endif``
    statement.


Subtree Specific Recommendations
*****************************

Some subtrees of the KConfig tree have have additional style recommendations to
promote a more consistent code basis.


Drivers
=======

Sensor Drivers
--------------

* When creating a KConfig symbol to enable a sensor driver, the symbol itself
  **should** follow the format of ``{MANUFACTURER}_{SENSOR_NAME}``
  (e.g. ``BOSCH_BMI160`` in the examples). When creating symbols to configure
  the driver, use this as a prefix for the configuration options.

   * *rationale*:
     * Prevent accidental duplication of a KConfig symbol.
     * Can simply be acquired from the devicetree compatible and is already
       used in the auto-generated ``DT_HAS_XX_ENABLED`` symbol.
* The prompt to select the symbol **should** be in the style of
  ``{SENSOR_NAME} ({MANUFACTURER}) {SENSOR_TYPE} sensor driver``

   * *rationale*:

      * Display most important driver information to the user, namely the
        drivers name, manufacturer and type.
      * The *sensor driver* suffix enables limiting search results to all
        sensor drivers.
* When the sensor driver does not require additional KConfig symbols, use a
  simple *config* entry. When it does, use a *menuconfig* entry with sub-options
  framed with an *if XXX* block.

   * *rationale*: Group related configuration options together for better
     organization and usability.
* Group sensor driver files in a directory structure of
  *{MANUFACTURER}/{SENSOR_NAME}*, When there is no or many manufacturers, use
  *generic* as a placeholder.

   * *rationale*: Use a consistent directory structure.

.. code-block:: kconfig
   :caption: Example Kconfig for a simple sensor driver

   config BOSCH_BMI160
      bool "BMI160 (Bosch) IMU sensor driver"
      default y
      depends on DT_HAS_BOSCH_BMI160_ENABLED
      select I2C if $(dt_compat_on_bus,$(DT_COMPAT_BOSCH_BMI160),i2c)
      select SPI if $(dt_compat_on_bus,$(DT_COMPAT_BOSCH_BMI160),spi)
      help
        Enable Bosch BMI160 inertial measurement unit that provides acceleration
        and angular rate measurements.

.. code-block:: kconfig
   :caption: Example Kconfig for a sensor driver with configuration options

   menuconfig BOSCH_BMI160
      bool "BMI160 (Bosch) IMU sensor driver"
      default y
      depends on DT_HAS_BOSCH_BMI160_ENABLED
      select I2C if $(dt_compat_on_bus,$(DT_COMPAT_BOSCH_BMI160),i2c)
      select SPI if $(dt_compat_on_bus,$(DT_COMPAT_BOSCH_BMI160),spi)
      help
        Enable Bosch BMI160 inertial measurement unit that provides acceleration
        and angular rate measurements.

   if BOSCH_BMI160

   choice
      prompt "Trigger mode"
      default BMI160_TRIGGER_GLOBAL_THREAD
      help
        Specify the type of triggering to be used by the driver.

   config BMI160_TRIGGER_NONE
      bool "No trigger"

   config BMI160_TRIGGER_GLOBAL_THREAD
      bool "Use global thread"
      depends on GPIO
      depends on $(dt_compat_any_has_prop,\
         $(DT_COMPAT_BOSCH_BMI160),int-gpios)
   select BMI160_TRIGGER

   config BMI160_TRIGGER_OWN_THREAD
      bool "Use own thread"
      depends on GPIO
      depends on $(dt_compat_any_has_prop,$(DT_COMPAT_BOSCH_BMI160),int-gpios)
      select BMI160_TRIGGER
   endchoice

   config BMI160_TRIGGER
      bool

   config BMI160_THREAD_PRIORITY
      int "Own thread priority"
      depends on BMI160_TRIGGER_OWN_THREAD
      default 10
      help
        The priority of the thread used for handling interrupts.

   config BMI160_THREAD_STACK_SIZE
      int "Own thread stack size"
      depends on BMI160_TRIGGER_OWN_THREAD
      default 1024
      help
        The thread stack size.

   endif # BOSCH_BMI160
