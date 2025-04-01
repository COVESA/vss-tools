public final class VehiclePropertyIdsVss {

	/** Average speed for the current trip. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_AVERAGE_SPEED_READ))
	public static final int AVERAGE_SPEED = 1096810519;

	/** The available volume for cargo or luggage. For automobiles, this is usually the trunk volume. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_CARGO_VOLUME_READ))
	public static final int CARGO_VOLUME = 1096810521;

	/** Vehicle curb weight, including all liquids and full tank of fuel, but no cargo or passengers. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_CURB_WEIGHT_READ))
	public static final int CURB_WEIGHT = 1094058012;

	/** Current altitude relative to WGS 84 reference ellipsoid, as measured at the position of GNSS receiver antenna. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_CURRENT_LOCATION_ALTITUDE_READ))
	public static final int CURRENT_LOCATION_ALTITUDE = 1098907692;

	/** Fix status of GNSS receiver. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_CURRENT_LOCATION_GNSSRECEIVER_FIX_TYPE_READ))
	public static final int CURRENT_LOCATION_GNSSRECEIVER_FIX_TYPE = 1091567662;

	/**
	 * Mounting position of GNSS receiver antenna relative to vehicle coordinate system. Axis definitions according to ISO
	 * 8855. Origin at center of (first) rear axle. Positive values = forward of rear axle. Negative values = backward of rear
	 * axle.
	 */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_CURRENT_LOCATION_GNSSRECEIVER_MOUNTING_POSITION_X_READ))
	public static final int CURRENT_LOCATION_GNSSRECEIVER_MOUNTING_POSITION_X = 1093926959;

	/**
	 * Mounting position of GNSS receiver antenna relative to vehicle coordinate system. Axis definitions according to ISO
	 * 8855. Origin at center of (first) rear axle. Positive values = left of origin. Negative values = right of origin.
	 * Left/Right is as seen from driver perspective, i.e. by a person looking forward.
	 */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_CURRENT_LOCATION_GNSSRECEIVER_MOUNTING_POSITION_Y_READ))
	public static final int CURRENT_LOCATION_GNSSRECEIVER_MOUNTING_POSITION_Y = 1093926960;

	/**
	 * Mounting position of GNSS receiver on Z-axis. Axis definitions according to ISO 8855. Origin at center of (first) rear
	 * axle. Positive values = above center of rear axle. Negative values = below center of rear axle.
	 */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_CURRENT_LOCATION_GNSSRECEIVER_MOUNTING_POSITION_Z_READ))
	public static final int CURRENT_LOCATION_GNSSRECEIVER_MOUNTING_POSITION_Z = 1093926961;

	/** Current heading relative to geographic north. 0 = North, 90 = East, 180 = South, 270 = West. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_CURRENT_LOCATION_HEADING_READ))
	public static final int CURRENT_LOCATION_HEADING = 1098907690;

	/** Accuracy of the latitude and longitude coordinates. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_CURRENT_LOCATION_HORIZONTAL_ACCURACY_READ))
	public static final int CURRENT_LOCATION_HORIZONTAL_ACCURACY = 1098907691;

	/** Current latitude of vehicle in WGS 84 geodetic coordinates, as measured at the position of GNSS receiver antenna. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_CURRENT_LOCATION_LATITUDE_READ))
	public static final int CURRENT_LOCATION_LATITUDE = 1098907688;

	/** Current longitude of vehicle in WGS 84 geodetic coordinates, as measured at the position of GNSS receiver antenna. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_CURRENT_LOCATION_LONGITUDE_READ))
	public static final int CURRENT_LOCATION_LONGITUDE = 1098907689;

	/** Timestamp from GNSS system for current location, formatted according to ISO 8601 with UTC time zone. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_CURRENT_LOCATION_TIMESTAMP_READ))
	public static final int CURRENT_LOCATION_TIMESTAMP = 1091567655;

	/** Accuracy of altitude. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_CURRENT_LOCATION_VERTICAL_ACCURACY_READ))
	public static final int CURRENT_LOCATION_VERTICAL_ACCURACY = 1098907693;

	/** Current overall Vehicle weight. Including passengers, cargo and other load inside the car. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_CURRENT_OVERALL_WEIGHT_READ))
	public static final int CURRENT_OVERALL_WEIGHT = 1094058011;

	/** The CO2 emissions. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_EMISSIONS_CO2_READ))
	public static final int EMISSIONS_CO2 = 1093926938;

	/** Curb weight of vehicle, including all liquids and full tank of fuel and full load of cargo and passengers. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_GROSS_WEIGHT_READ))
	public static final int GROSS_WEIGHT = 1094058013;

	/** Overall vehicle height. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_HEIGHT_READ))
	public static final int HEIGHT = 1094058017;

	/**
	 * Vehicle breakdown or any similar event causing vehicle to stop on the road, that might pose a risk to other road users.
	 * True = Vehicle broken down on the road, due to e.g. engine problems, flat tire, out of gas, brake problems. False =
	 * Vehicle not broken down.
	 */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_IS_BROKEN_DOWN_READ))
	public static final int IS_BROKEN_DOWN = 1092616213;

	/** Indicates whether the vehicle is stationary or moving. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_IS_MOVING_READ))
	public static final int IS_MOVING = 1092616214;

	/** Overall vehicle length. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_LENGTH_READ))
	public static final int LENGTH = 1094058016;

	/** State of the supply voltage of the control units (usually 12V). */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_LOW_VOLTAGE_SYSTEM_STATE_READ))
	public static final int LOW_VOLTAGE_SYSTEM_STATE = 1091567630;

	/** Maximum vertical weight on the tow ball of a trailer. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_MAX_TOW_BALL_WEIGHT_READ))
	public static final int MAX_TOW_BALL_WEIGHT = 1094058015;

	/** Maximum weight of trailer. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_MAX_TOW_WEIGHT_READ))
	public static final int MAX_TOW_WEIGHT = 1094058014;

	/** The accumulated energy from regenerative braking over lifetime. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_ACCUMULATED_BRAKING_ENERGY_READ))
	public static final int POWERTRAIN_ACCUMULATED_BRAKING_ENERGY = 1096810546;

	/** Engine coolant level. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_COMBUSTION_ENGINE_ENGINE_COOLANT_LEVEL_READ))
	public static final int POWERTRAIN_COMBUSTION_ENGINE_ENGINE_COOLANT_LEVEL = 1091567676;

	/** Engine coolant temperature. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_COMBUSTION_ENGINE_ENGINE_COOLANT_TEMPERATURE_READ))
	public static final int POWERTRAIN_COMBUSTION_ENGINE_ENGINE_COOLANT_TEMPERATURE = 1096810555;

	/** Engine oil capacity in liters. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_COMBUSTION_ENGINE_ENGINE_OIL_CAPACITY_READ))
	public static final int POWERTRAIN_COMBUSTION_ENGINE_ENGINE_OIL_CAPACITY = 1096810552;

	/** Engine oil level. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_COMBUSTION_ENGINE_ENGINE_OIL_LEVEL_READ))
	public static final int POWERTRAIN_COMBUSTION_ENGINE_ENGINE_OIL_LEVEL = 1091567673;

	/** EOT, Engine oil temperature. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_COMBUSTION_ENGINE_ENGINE_OIL_TEMPERATURE_READ))
	public static final int POWERTRAIN_COMBUSTION_ENGINE_ENGINE_OIL_TEMPERATURE = 1096810554;

	/** Engine Running. True if engine is rotating (Speed > 0). */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_COMBUSTION_ENGINE_IS_RUNNING_READ))
	public static final int POWERTRAIN_COMBUSTION_ENGINE_IS_RUNNING = 1092616246;

	/** Engine speed measured as rotations per minute. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_COMBUSTION_ENGINE_SPEED_READ))
	public static final int POWERTRAIN_COMBUSTION_ENGINE_SPEED = 1094058039;

	/** Current available fuel in the fuel tank expressed in liters. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_FUEL_SYSTEM_ABSOLUTE_LEVEL_READ))
	public static final int POWERTRAIN_FUEL_SYSTEM_ABSOLUTE_LEVEL = 1096810561;

	/** Average consumption in liters per 100 km. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_FUEL_SYSTEM_AVERAGE_CONSUMPTION_READ))
	public static final int POWERTRAIN_FUEL_SYSTEM_AVERAGE_CONSUMPTION = 1096810566;

	/** Fuel consumption since last refueling. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_FUEL_SYSTEM_CONSUMPTION_SINCE_LAST_REFUEL_READ))
	public static final int POWERTRAIN_FUEL_SYSTEM_CONSUMPTION_SINCE_LAST_REFUEL = 1096810568;

	/** Fuel amount in liters consumed since start of current trip. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_FUEL_SYSTEM_CONSUMPTION_SINCE_START_READ))
	public static final int POWERTRAIN_FUEL_SYSTEM_CONSUMPTION_SINCE_START = 1096810567;

	/** Defines the hybrid type of the vehicle. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_FUEL_SYSTEM_HYBRID_TYPE_READ))
	public static final int POWERTRAIN_FUEL_SYSTEM_HYBRID_TYPE = 1091567679;

	/** Current consumption in liters per 100 km. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_FUEL_SYSTEM_INSTANT_CONSUMPTION_READ))
	public static final int POWERTRAIN_FUEL_SYSTEM_INSTANT_CONSUMPTION = 1096810565;

	/** Indicates whether eco start stop is currently enabled. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_FUEL_SYSTEM_IS_ENGINE_STOP_START_ENABLED_READ))
	public static final int POWERTRAIN_FUEL_SYSTEM_IS_ENGINE_STOP_START_ENABLED = 1092616265;

	/** Indicates that the fuel level is low (e.g. <50km range). */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_FUEL_SYSTEM_IS_FUEL_LEVEL_LOW_READ))
	public static final int POWERTRAIN_FUEL_SYSTEM_IS_FUEL_LEVEL_LOW = 1092616266;

	/** Status of the fuel port flap(s). True if at least one is open. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_FUEL_SYSTEM_IS_FUEL_PORT_FLAP_OPEN_READ))
	@RequiresPermission.Write(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_FUEL_SYSTEM_IS_FUEL_PORT_FLAP_OPEN_WRITE))
	public static final int POWERTRAIN_FUEL_SYSTEM_IS_FUEL_PORT_FLAP_OPEN = 1092616268;

	/** Remaining range in meters using only liquid fuel. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_FUEL_SYSTEM_RANGE_READ))
	public static final int POWERTRAIN_FUEL_SYSTEM_RANGE = 1094844483;

	/** Position of refuel port(s). First part indicates side of vehicle, second part relative position on that side. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_FUEL_SYSTEM_REFUEL_PORT_POSITION_READ))
	public static final int POWERTRAIN_FUEL_SYSTEM_REFUEL_PORT_POSITION = 1091633227;

	/** Level in fuel tank as percent of capacity. 0 = empty. 100 = full. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_FUEL_SYSTEM_RELATIVE_LEVEL_READ))
	public static final int POWERTRAIN_FUEL_SYSTEM_RELATIVE_LEVEL = 1093795906;

	/**
	 * Detailed information on fuels supported by the vehicle. Identifiers originating from DIN EN 16942:2021-08, appendix B,
	 * with additional suffix for octane (RON) where relevant.
	 */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_FUEL_SYSTEM_SUPPORTED_FUEL_READ))
	public static final int POWERTRAIN_FUEL_SYSTEM_SUPPORTED_FUEL = 1091633214;

	/** High level information of fuel types supported */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_FUEL_SYSTEM_SUPPORTED_FUEL_TYPES_READ))
	public static final int POWERTRAIN_FUEL_SYSTEM_SUPPORTED_FUEL_TYPES = 1091633213;

	/** Capacity of the fuel tank in liters. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_FUEL_SYSTEM_TANK_CAPACITY_READ))
	public static final int POWERTRAIN_FUEL_SYSTEM_TANK_CAPACITY = 1096810560;

	/** Time remaining in seconds before the fuel tank is empty. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_FUEL_SYSTEM_TIME_REMAINING_READ))
	public static final int POWERTRAIN_FUEL_SYSTEM_TIME_REMAINING = 1094844484;

	/** Remaining range in meters using all energy sources available in the vehicle. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_RANGE_READ))
	public static final int POWERTRAIN_RANGE = 1094844467;

	/** Time remaining in seconds before all energy sources available in the vehicle are empty. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_TIME_REMAINING_READ))
	public static final int POWERTRAIN_TIME_REMAINING = 1094844468;

	/** Defines the powertrain type of the vehicle. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_POWERTRAIN_TYPE_READ))
	public static final int POWERTRAIN_TYPE = 1091567669;

	/** The permitted total weight of cargo and installations (e.g. a roof rack) on top of the vehicle. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_ROOF_LOAD_READ))
	public static final int ROOF_LOAD = 1093926936;

	/** Vehicle speed. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_SPEED_READ))
	public static final int SPEED = 1096810511;

	/** Start time of current or latest trip, formatted according to ISO 8601 with UTC time zone. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_START_TIME_READ))
	public static final int START_TIME = 1091567634;

	/** Signal indicating if trailer is connected or not. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_TRAILER_IS_CONNECTED_READ))
	public static final int TRAILER_IS_CONNECTED = 1092616230;

	/** Odometer reading, total distance traveled during the lifetime of the vehicle. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_TRAVELED_DISTANCE_READ))
	public static final int TRAVELED_DISTANCE = 1096810512;

	/** Distance traveled since start of current trip. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_TRAVELED_DISTANCE_SINCE_START_READ))
	public static final int TRAVELED_DISTANCE_SINCE_START = 1096810513;

	/** Duration of latest trip. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_TRIP_DURATION_READ))
	public static final int TRIP_DURATION = 1096810515;

	/** Trip meter reading. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_TRIP_METER_READING_READ))
	@RequiresPermission.Write(@RequiresPermission(VssPermissions.PERMISSION_VSS_TRIP_METER_READING_WRITE))
	public static final int TRIP_METER_READING = 1096810516;

	/** Minimum turning diameter, Wall-to-Wall, as defined by SAE J1100-2009 D102. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_TURNING_DIAMETER_READ))
	public static final int TURNING_DIAMETER = 1094058021;

	/** Indicates the design and body style of the vehicle (e.g. station wagon, hatchback, etc.). */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_VEHICLE_IDENTIFICATION_BODY_TYPE_READ))
	public static final int VEHICLE_IDENTIFICATION_BODY_TYPE = 1091567622;

	/** Vehicle brand or manufacturer. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_VEHICLE_IDENTIFICATION_BRAND_READ))
	public static final int VEHICLE_IDENTIFICATION_BRAND = 1091567619;

	/** The date in ISO 8601 format of the first registration of the vehicle with the respective public authorities. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_VEHICLE_IDENTIFICATION_DATE_VEHICLE_FIRST_REGISTERED_READ))
	public static final int VEHICLE_IDENTIFICATION_DATE_VEHICLE_FIRST_REGISTERED = 1091567623;

	/** The license plate of the vehicle. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_VEHICLE_IDENTIFICATION_LICENSE_PLATE_READ))
	public static final int VEHICLE_IDENTIFICATION_LICENSE_PLATE = 1091567624;

	/** Indicates that the vehicle meets the respective emission standard. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_VEHICLE_IDENTIFICATION_MEETS_EMISSION_STANDARD_READ))
	public static final int VEHICLE_IDENTIFICATION_MEETS_EMISSION_STANDARD = 1091567625;

	/** Vehicle model. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_VEHICLE_IDENTIFICATION_MODEL_READ))
	public static final int VEHICLE_IDENTIFICATION_MODEL = 1091567620;

	/** The date in ISO 8601 format of production of the item, e.g. vehicle. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_VEHICLE_IDENTIFICATION_PRODUCTION_DATE_READ))
	public static final int VEHICLE_IDENTIFICATION_PRODUCTION_DATE = 1091567626;

	/** The main color of the exterior within the basic color palette (eg. red, blue, black, white, ...). */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_VEHICLE_IDENTIFICATION_VEHICLE_EXTERIOR_COLOR_READ))
	public static final int VEHICLE_IDENTIFICATION_VEHICLE_EXTERIOR_COLOR = 1091567629;

	/**
	 * The release date in ISO 8601 format of a vehicle model (often used to differentiate versions of the same make and
	 * model).
	 */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_VEHICLE_IDENTIFICATION_VEHICLE_MODEL_DATE_READ))
	public static final int VEHICLE_IDENTIFICATION_VEHICLE_MODEL_DATE = 1091567627;

	/**
	 * The number of passengers that can be seated in the vehicle, both in terms of the physical space available, and in terms
	 * of limitations set by law.
	 */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_VEHICLE_IDENTIFICATION_VEHICLE_SEATING_CAPACITY_READ))
	public static final int VEHICLE_IDENTIFICATION_VEHICLE_SEATING_CAPACITY = 1094057996;

	/** 3-character World Manufacturer Identification (WMI) as defined by ISO 3780. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_VEHICLE_IDENTIFICATION_WMI_READ))
	public static final int VEHICLE_IDENTIFICATION_WMI = 1091567618;

	/** Model year of the vehicle. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_VEHICLE_IDENTIFICATION_YEAR_READ))
	public static final int VEHICLE_IDENTIFICATION_YEAR = 1094057989;

	/** Overall vehicle width excluding mirrors, as defined by SAE J1100-2009 W103. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_WIDTH_EXCLUDING_MIRRORS_READ))
	public static final int WIDTH_EXCLUDING_MIRRORS = 1094058018;

	/** Overall vehicle width with mirrors folded, as defined by SAE J1100-2009 W145. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_WIDTH_FOLDED_MIRRORS_READ))
	public static final int WIDTH_FOLDED_MIRRORS = 1094058020;

	/** Overall vehicle width including mirrors, as defined by SAE J1100-2009 W144. */
	@RequiresPermission.Read(@RequiresPermission(VssPermissions.PERMISSION_VSS_WIDTH_INCLUDING_MIRRORS_READ))
	public static final int WIDTH_INCLUDING_MIRRORS = 1094058019;

}