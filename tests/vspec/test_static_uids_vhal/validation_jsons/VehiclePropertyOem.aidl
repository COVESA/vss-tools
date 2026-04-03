package android.hardware.automotive.vehicle;

import android.hardware.automotive.vehicle.VehicleArea;
import android.hardware.automotive.vehicle.VehiclePropertyType;
import android.hardware.automotive.vehicle.VehiclePropertyGroup;

@VintfStability
@Backing(type="int")
enum VehiclePropertyOem {

	/**
	 * A new trip is considered to start when engine gets enabled (e.g. LowVoltageSystemState in ON or START mode). A trip is
	 * considered to end when engine is no longer enabled. The signal may however keep the value of the last trip until a new
	 * trip is started. Calculation of average speed may exclude periods when the vehicle for example is not moving or
	 * transmission is in neutral.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	AVERAGE_SPEED = 0x0017 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * The available volume for cargo or luggage. For automobiles, this is usually the trunk volume.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	CARGO_VOLUME = 0x0019 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * Vehicle curb weight, including all liquids and full tank of fuel, but no cargo or passengers.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	CURB_WEIGHT = 0x001c + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * Current altitude relative to WGS 84 reference ellipsoid, as measured at the position of GNSS receiver antenna.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	CURRENT_LOCATION_ALTITUDE = 0x002c + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * Fix status of GNSS receiver.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	CURRENT_LOCATION_GNSSRECEIVER_FIX_TYPE = 0x002e + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * Mounting position of GNSS receiver antenna relative to vehicle coordinate system. Axis definitions according to ISO
	 * 8855. Origin at center of (first) rear axle. Positive values = forward of rear axle. Negative values = backward of rear
	 * axle.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	CURRENT_LOCATION_GNSSRECEIVER_MOUNTING_POSITION_X = 0x002f + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * Mounting position of GNSS receiver antenna relative to vehicle coordinate system. Axis definitions according to ISO
	 * 8855. Origin at center of (first) rear axle. Positive values = left of origin. Negative values = right of origin.
	 * Left/Right is as seen from driver perspective, i.e. by a person looking forward.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	CURRENT_LOCATION_GNSSRECEIVER_MOUNTING_POSITION_Y = 0x0030 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * Mounting position of GNSS receiver on Z-axis. Axis definitions according to ISO 8855. Origin at center of (first) rear
	 * axle. Positive values = above center of rear axle. Negative values = below center of rear axle.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	CURRENT_LOCATION_GNSSRECEIVER_MOUNTING_POSITION_Z = 0x0031 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * Current heading relative to geographic north. 0 = North, 90 = East, 180 = South, 270 = West.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	CURRENT_LOCATION_HEADING = 0x002a + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * Accuracy of the latitude and longitude coordinates.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	CURRENT_LOCATION_HORIZONTAL_ACCURACY = 0x002b + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * Current latitude of vehicle in WGS 84 geodetic coordinates, as measured at the position of GNSS receiver antenna.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	CURRENT_LOCATION_LATITUDE = 0x0028 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * Current longitude of vehicle in WGS 84 geodetic coordinates, as measured at the position of GNSS receiver antenna.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	CURRENT_LOCATION_LONGITUDE = 0x0029 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * Timestamp from GNSS system for current location, formatted according to ISO 8601 with UTC time zone.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	CURRENT_LOCATION_TIMESTAMP = 0x0027 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * Accuracy of altitude.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	CURRENT_LOCATION_VERTICAL_ACCURACY = 0x002d + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * Current overall Vehicle weight. Including passengers, cargo and other load inside the car.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	CURRENT_OVERALL_WEIGHT = 0x001b + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * The CO2 emissions.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	EMISSIONS_CO2 = 0x001a + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * Curb weight of vehicle, including all liquids and full tank of fuel and full load of cargo and passengers.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	GROSS_WEIGHT = 0x001d + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * Overall vehicle height.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	HEIGHT = 0x0021 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * Actual criteria and method used to decide if a vehicle is broken down is implementation specific.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	IS_BROKEN_DOWN = 0x0015 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.BOOLEAN,

	/**
	 * Indicates whether the vehicle is stationary or moving.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	IS_MOVING = 0x0016 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.BOOLEAN,

	/**
	 * Overall vehicle length.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	LENGTH = 0x0020 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * State of the supply voltage of the control units (usually 12V).
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	LOW_VOLTAGE_SYSTEM_STATE = 0x000e + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * Maximum vertical weight on the tow ball of a trailer.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	MAX_TOW_BALL_WEIGHT = 0x001f + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * Maximum weight of trailer.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	MAX_TOW_WEIGHT = 0x001e + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * The accumulated energy from regenerative braking over lifetime.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_ACCUMULATED_BRAKING_ENERGY = 0x0032 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * Engine coolant level.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_COMBUSTION_ENGINE_ENGINE_COOLANT_LEVEL = 0x003c + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * Engine coolant temperature.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_COMBUSTION_ENGINE_ENGINE_COOLANT_TEMPERATURE = 0x003b + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * Engine oil capacity in liters.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_COMBUSTION_ENGINE_ENGINE_OIL_CAPACITY = 0x0038 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * Engine oil level.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_COMBUSTION_ENGINE_ENGINE_OIL_LEVEL = 0x0039 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * EOT, Engine oil temperature.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_COMBUSTION_ENGINE_ENGINE_OIL_TEMPERATURE = 0x003a + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * Engine Running. True if engine is rotating (Speed > 0).
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_COMBUSTION_ENGINE_IS_RUNNING = 0x0036 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.BOOLEAN,

	/**
	 * Engine speed measured as rotations per minute.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_COMBUSTION_ENGINE_SPEED = 0x0037 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * Current available fuel in the fuel tank expressed in liters.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_FUEL_SYSTEM_ABSOLUTE_LEVEL = 0x0041 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * Average consumption in liters per 100 km.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_FUEL_SYSTEM_AVERAGE_CONSUMPTION = 0x0046 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * Amount of fuel consumed since last refueling.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_FUEL_SYSTEM_CONSUMPTION_SINCE_LAST_REFUEL = 0x0048 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * A new trip is considered to start when engine gets enabled (e.g. LowVoltageSystemState in ON or START mode). A trip is
	 * considered to end when engine is no longer enabled. The signal may however keep the value of the last trip until a new
	 * trip is started.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_FUEL_SYSTEM_CONSUMPTION_SINCE_START = 0x0047 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * Defines the hybrid type of the vehicle.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_FUEL_SYSTEM_HYBRID_TYPE = 0x003f + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * Current consumption in liters per 100 km.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_FUEL_SYSTEM_INSTANT_CONSUMPTION = 0x0045 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * Indicates whether eco start stop is currently enabled.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_FUEL_SYSTEM_IS_ENGINE_STOP_START_ENABLED = 0x0049 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.BOOLEAN,

	/**
	 * Indicates that the fuel level is low (e.g. <50km range).
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_FUEL_SYSTEM_IS_FUEL_LEVEL_LOW = 0x004a + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.BOOLEAN,

	/**
	 * Status of the fuel port flap(s). True if at least one is open.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ_WRITE
	 * @version 1
	 */
	POWERTRAIN_FUEL_SYSTEM_IS_FUEL_PORT_FLAP_OPEN = 0x004c + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.BOOLEAN,

	/**
	 * Remaining range in meters using only liquid fuel.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_FUEL_SYSTEM_RANGE = 0x0043 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * Position of refuel port(s). First part indicates side of vehicle, second part relative position on that side.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_FUEL_SYSTEM_REFUEL_PORT_POSITION = 0x004b + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * Level in fuel tank as percent of capacity. 0 = empty. 100 = full.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_FUEL_SYSTEM_RELATIVE_LEVEL = 0x0042 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * RON 95 is sometimes referred to as Super, RON 98 as Super Plus.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_FUEL_SYSTEM_SUPPORTED_FUEL = 0x003e + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * If a vehicle also has an electric drivetrain (e.g. hybrid) that will be obvious from the PowerTrain.Type signal.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_FUEL_SYSTEM_SUPPORTED_FUEL_TYPES = 0x003d + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * Capacity of the fuel tank in liters.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_FUEL_SYSTEM_TANK_CAPACITY = 0x0040 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * Time remaining in seconds before the fuel tank is empty.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_FUEL_SYSTEM_TIME_REMAINING = 0x0044 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * Remaining range in meters using all energy sources available in the vehicle.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_RANGE = 0x0033 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * Time remaining in seconds before all energy sources available in the vehicle are empty.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_TIME_REMAINING = 0x0034 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * For vehicles with a combustion engine (including hybrids) more detailed information on fuels supported can be found in
	 * FuelSystem.SupportedFuelTypes and FuelSystem.SupportedFuels.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	POWERTRAIN_TYPE = 0x0035 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * The permitted total weight of cargo and installations (e.g. a roof rack) on top of the vehicle.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	ROOF_LOAD = 0x0018 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * Vehicle speed.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	SPEED = 0x000f + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * This signal is supposed to be set whenever a new trip starts. A new trip is considered to start when engine gets enabled
	 * (e.g. LowVoltageSystemState in ON or START mode). A trip is considered to end when engine is no longer enabled. The
	 * default value indicates that the vehicle never has been started, or that latest start time is unknown.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	START_TIME = 0x0012 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * Signal indicating if trailer is connected or not.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	TRAILER_IS_CONNECTED = 0x0026 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.BOOLEAN,

	/**
	 * Odometer reading, total distance traveled during the lifetime of the vehicle.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	TRAVELED_DISTANCE = 0x0010 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * A new trip is considered to start when engine gets enabled (e.g. LowVoltageSystemState in ON or START mode). A trip is
	 * considered to end when engine is no longer enabled. The signal may however keep the value of the last trip until a new
	 * trip is started.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	TRAVELED_DISTANCE_SINCE_START = 0x0011 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * This signal is not assumed to be continuously updated, but instead set to 0 when a trip starts and set to the actual
	 * duration of the trip when a trip ends. A new trip is considered to start when engine gets enabled (e.g.
	 * LowVoltageSystemState in ON or START mode). A trip is considered to end when engine is no longer enabled.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	TRIP_DURATION = 0x0013 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * The trip meter is an odometer that can be manually reset by the driver. Trip meter reading.
	 *
	 * @change_mode VehiclePropertyChangeMode.ON_CHANGE
	 * @access VehiclePropertyAccess.READ_WRITE
	 * @version 1
	 */
	TRIP_METER_READING = 0x0014 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.FLOAT,

	/**
	 * Minimum turning diameter, Wall-to-Wall, as defined by SAE J1100-2009 D102.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	TURNING_DIAMETER = 0x0025 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * Indicates the design and body style of the vehicle (e.g. station wagon, hatchback, etc.).
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	VEHICLE_IDENTIFICATION_BODY_TYPE = 0x0006 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * Vehicle brand or manufacturer.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	VEHICLE_IDENTIFICATION_BRAND = 0x0003 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * The date in ISO 8601 format of the first registration of the vehicle with the respective public authorities.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	VEHICLE_IDENTIFICATION_DATE_VEHICLE_FIRST_REGISTERED = 0x0007 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * Depending on the context, this attribute might not be up to date or might be misconfigured, and therefore should be
	 * considered untrustworthy in the absence of another method of verification.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	VEHICLE_IDENTIFICATION_LICENSE_PLATE = 0x0008 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * Indicates that the vehicle meets the respective emission standard.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	VEHICLE_IDENTIFICATION_MEETS_EMISSION_STANDARD = 0x0009 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * Vehicle model.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	VEHICLE_IDENTIFICATION_MODEL = 0x0004 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * The date in ISO 8601 format of production of the item, e.g. vehicle.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	VEHICLE_IDENTIFICATION_PRODUCTION_DATE = 0x000a + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * The main color of the exterior within the basic color palette (eg. red, blue, black, white, ...).
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	VEHICLE_IDENTIFICATION_VEHICLE_EXTERIOR_COLOR = 0x000d + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * The release date in ISO 8601 format of a vehicle model (often used to differentiate versions of the same make and
	 * model).
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	VEHICLE_IDENTIFICATION_VEHICLE_MODEL_DATE = 0x000b + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * The number of passengers that can be seated in the vehicle, both in terms of the physical space available, and in terms
	 * of limitations set by law.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	VEHICLE_IDENTIFICATION_VEHICLE_SEATING_CAPACITY = 0x000c + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * 17-character Vehicle Identification Number (VIN) as defined by ISO 3779.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	VEHICLE_IDENTIFICATION_VIN = 0x0001 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * 3-character World Manufacturer Identification (WMI) as defined by ISO 3780.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	VEHICLE_IDENTIFICATION_WMI = 0x0002 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.STRING,

	/**
	 * Model year of the vehicle.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	VEHICLE_IDENTIFICATION_YEAR = 0x0005 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * Overall vehicle width excluding mirrors, as defined by SAE J1100-2009 W103.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	WIDTH_EXCLUDING_MIRRORS = 0x0022 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * Overall vehicle width with mirrors folded, as defined by SAE J1100-2009 W145.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	WIDTH_FOLDED_MIRRORS = 0x0024 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

	/**
	 * Overall vehicle width including mirrors, as defined by SAE J1100-2009 W144.
	 *
	 * @change_mode VehiclePropertyChangeMode.STATIC
	 * @access VehiclePropertyAccess.READ
	 * @version 1
	 */
	WIDTH_INCLUDING_MIRRORS = 0x0023 + VehiclePropertyGroup.VSS + VehicleArea.GLOBAL + VehiclePropertyType.INT32,

}