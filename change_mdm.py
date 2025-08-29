#!/usr/bin/env python3
"""
Apple School Manager Device Management Script
This script changes the management server assignment for devices using the ASM API.
"""

import os
import sys
import json
import requests
from pathlib import Path

# Configuration - Update these values for your environment
ASM_API_BASE_URL = "https://api-school.apple.com/v1"
KEY_FILE_PATH = os.getenv("ASM_KEY_FILE", "asm_private_key.pem")
KEY_ID = os.getenv("ASM_KEY_ID")  # Your Key ID from Apple School Manager
ISSUER_ID = os.getenv("ASM_ISSUER_ID")  # Your Issuer ID from Apple School Manager

# Management server mappings - Update these with your actual server IDs
MDM_SERVERS = {
    "Mosyle Macs": "UDID_GOES_HERE",
    "Mosyle iPads": "UDID_GOES_HERE"
}

def load_private_key():
    """Load the private key from file."""
    try:
        key_path = Path(KEY_FILE_PATH)
        if not key_path.exists():
            print(f"Error: Private key file not found at {KEY_FILE_PATH}")
            print("Please set the ASM_KEY_FILE environment variable to point to your private key file.")
            sys.exit(1)
        
        with open(key_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading private key: {e}")
        sys.exit(1)

def check_environment():
    """Check if required environment variables are set."""
    if not KEY_ID:
        print("Error: ASM_KEY_ID environment variable not set")
        print("Please set it to your Apple School Manager API Key ID")
        sys.exit(1)
    
    if not ISSUER_ID:
        print("Error: ASM_ISSUER_ID environment variable not set")
        print("Please set it to your Apple School Manager Issuer ID")
        sys.exit(1)

def generate_jwt_token():
    """Generate JWT token for Apple School Manager API authentication."""
    try:
        import jwt
        from datetime import datetime, timedelta
    except ImportError:
        print("Error: PyJWT library not installed. Install it with: pip install PyJWT")
        sys.exit(1)
    
    private_key = load_private_key()
    
    # JWT payload
    now = datetime.utcnow()
    payload = {
        "iss": ISSUER_ID,
        "iat": now,
        "exp": now + timedelta(minutes=20),  # Token expires in 20 minutes
        "aud": "https://account.apple.com/auth/oauth2/v2/token"
    }
    
    # JWT header
    headers = {
        "kid": KEY_ID,
        "alg": "ES256"
    }
    
    # Generate token
    token = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)
    return token

def get_auth_headers():
    """Get authorization headers for API requests."""
    token = generate_jwt_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def search_device_by_serial(serial_number):
    """Search for a device by serial number."""
    headers = get_auth_headers()
    
    # Search for device by serial number
    url = f"{ASM_API_BASE_URL}/devices"
    params = {
        "filter[serialNumber]": serial_number
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        if data.get("data") and len(data["data"]) > 0:
            return data["data"][0]  # Return first matching device
        else:
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error searching for device: {e}")
        return None

def get_mdm_servers():
    """Get available MDM servers from the API."""
    headers = get_auth_headers()
    
    try:
        url = f"{ASM_API_BASE_URL}/device-management-servers"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        return data.get("data", [])
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching MDM servers: {e}")
        return []

def assign_device_to_server(device_id, server_id):
    """Assign a device to a specific MDM server."""
    headers = get_auth_headers()
    
    payload = {
        "data": {
            "type": "devices",
            "id": device_id,
            "attributes": {
                "deviceManagementServerId": server_id
            }
        }
    }
    
    try:
        url = f"{ASM_API_BASE_URL}/devices/{device_id}"
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error assigning device: {e}")
        return None

def select_management_server():
    """Prompt user to select a management server."""
    print("\nAvailable Management Servers:")
    servers = list(MDM_SERVERS.keys())
    
    for i, server in enumerate(servers, 1):
        print(f"{i}. {server}")
    
    while True:
        try:
            choice = input(f"\nSelect server (1-{len(servers)}): ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(servers):
                selected_server = servers[choice_num - 1]
                return selected_server, MDM_SERVERS[selected_server]
            else:
                print(f"Please enter a number between 1 and {len(servers)}")
                
        except ValueError:
            print("Please enter a valid number")

def main():
    """Main function to orchestrate the device management process."""
    print("Apple School Manager Device Management Script")
    print("=" * 50)
    
    # Check environment setup
    check_environment()
    
    # Get device serial number from user
    serial_number = input("Enter device serial number: ").strip().upper()
    
    if not serial_number:
        print("Error: Serial number cannot be empty")
        sys.exit(1)
    
    print(f"\nSearching for device with serial number: {serial_number}")
    
    # Search for device
    device = search_device_by_serial(serial_number)
    
    if not device:
        print(f"Error: Device with serial number {serial_number} not found")
        sys.exit(1)
    
    # Display device information
    device_id = device["id"]
    device_model = device["attributes"].get("model", "Unknown")
    current_server = device["attributes"].get("deviceManagementServerId", "Unassigned")
    
    print(f"\nDevice found:")
    print(f"  ID: {device_id}")
    print(f"  Model: {device_model}")
    print(f"  Current Server ID: {current_server}")
    
    # Select new management server
    server_name, server_id = select_management_server()
    
    print(f"\nSelected: {server_name} (ID: {server_id})")
    
    # Confirm assignment
    confirm = input(f"\nAssign device {serial_number} to {server_name}? (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("Operation cancelled")
        sys.exit(0)
    
    # Assign device to new server
    print(f"\nAssigning device to {server_name}...")
    
    result = assign_device_to_server(device_id, server_id)
    
    if result:
        print("✅ Device successfully assigned to new management server!")
        print(f"Device {serial_number} is now assigned to {server_name}")
    else:
        print("❌ Failed to assign device to management server")
        sys.exit(1)

if __name__ == "__main__":
    main()
