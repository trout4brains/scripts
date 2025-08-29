#!/bin/bash

# ==============================================================================
# set_wifi_priority.sh
#
# Description:
#   A bash script for macOS to disable auto-join for two specified Wi-Fi
#   networks by removing them from the preferred networks list. It then
#   recycles the Wi-Fi adapter to connect to the highest priority network.
#
# Usage:
#   1. Edit the CONFIGURATION variables below to match your needs.
#   2. Make the script executable: chmod +x set_wifi_priority.sh
#   3. Run the script with sudo: sudo ./set_wifi_priority.sh
#
# ==============================================================================

# --- CONFIGURATION ---

# Set the SSID for the FIRST network for which auto-join will be DISABLED.
DISABLE_AUTOJOIN_SSID_1="SSID-NUMBER-ONE-GOES-HERE"

# Set the SSID for the SECOND network for which auto-join will be DISABLED.
# Comment this variable out if you only have 1 SSID to disable.
DISABLE_AUTOJOIN_SSID_2="SSID-NUMBER-TWO-GOES-HERE"


# --- SCRIPT LOGIC (No need to edit below this line) ---

# 1. Check for root privileges.
# The networksetup command requires administrator access to modify settings.
if [[ $EUID -ne 0 ]]; then
   echo "Error: This script must be run as root."
   echo "Please run with sudo: sudo ./remove_ssid_from_preferred_list.sh"
   exit 1
fi

# 2. Automatically find the primary Wi-Fi hardware port (e.g., en0).
# This makes the script work on any Mac without manual configuration.
WIFI_DEVICE=$(networksetup -listallhardwareports | awk '/Hardware Port: Wi-Fi/{getline; print $2}')

if [ -z "$WIFI_DEVICE" ]; then
    echo "Error: Could not find a Wi-Fi device."
    exit 1
fi
echo "Detected Wi-Fi device: $WIFI_DEVICE"
echo "---"

# 3. Display the current network order for reference.
echo "Current preferred network list (before changes):"
networksetup -listpreferredwirelessnetworks "$WIFI_DEVICE"
echo "---"

# 4. Disable auto-join on the first network by removing it from the list.
# A network not on the preferred list will not be auto-joined. You can still
# connect to it manually if it is in range.
echo "Disabling auto-join for '$DISABLE_AUTOJOIN_SSID_1' by removing it from the preferred list..."
networksetup -removepreferredwirelessnetwork "$WIFI_DEVICE" "$DISABLE_AUTOJOIN_SSID_1" > /dev/null 2>&1


# 5. Disable auto-join on the second network by removing it from the list.
# Comment this section out if you only have 1 SSID to disable.
echo "Disabling auto-join for '$DISABLE_AUTOJOIN_SSID_2' by removing it from the preferred list..."
networksetup -removepreferredwirelessnetwork "$WIFI_DEVICE" "$DISABLE_AUTOJOIN_SSID_2" > /dev/null 2>&1


# 6. Display the new list for confirmation.
echo "---"
echo "Successfully updated preferred network list:"
networksetup -listpreferredwirelessnetworks "$WIFI_DEVICE"
echo "---"

# 7. Cycle the Wi-Fi adapter to force reconnection.
echo "Toggling Wi-Fi off and on to apply changes..."
networksetup -setairportpower "$WIFI_DEVICE" off
# Wait for 3 seconds to ensure the adapter is fully powered down.
sleep 3
networksetup -setairportpower "$WIFI_DEVICE" on
echo "Wi-Fi has been re-enabled."
echo "---"
echo "Done."

exit 0

