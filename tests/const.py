"""Constants for Philips AirPurifier tests."""

DOMAIN = "philips_airpurifier_coap"

TEST_HOST = "192.168.1.100"
TEST_MODEL = "AC3858/51"
TEST_NAME = "Living Room"
TEST_DEVICE_ID = "aabbccddeeff"
TEST_MAC = "b0f893123456"  # MAC address must be lowercase without colons for DHCP

# Gen1 device status (AC3858/51 pattern)
MOCK_STATUS_GEN1: dict = {
    "pwr": "1",
    "mode": "AG",
    "om": "a",
    "aqil": 100,
    "uil": "1",
    "ddp": "1",
    "rddp": "1",
    "cl": False,
    "dt": 0,
    "err": 0,
    "DeviceId": TEST_DEVICE_ID,
    "name": TEST_NAME,
    "modelid": TEST_MODEL,
    "WifiVersion": "AWS_Philips_AIR@1.0.0",
    "Runtime": 7200000,
    # Sensors
    "pm25": 12,
    "iaql": 3,
    "rh": 50,
    "temp": 22,
    # Filters
    "fltsts0": 200,
    "flttotal0": 2400,
    "fltsts1": 1000,
    "flttotal1": 4800,
    "fltsts2": 500,
    "flttotal2": 2400,
    "fltt1": "A3",
    "fltt2": "C7",
}
