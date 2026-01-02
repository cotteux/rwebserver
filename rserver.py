#!/usr/bin/env python3

import RNS
import sys
import time
import threading

import config
from content import ensure_public_directory
from reticulum import get_or_create_identity, create_destination, start_link_server
from http import http_handler


def main():
    try:
        print("RServer - Reticulum Web Server")
        print("=" * 40)

        print("Initializing Reticulum...")

        # Initialize Reticulum with default config
        reticulum = RNS.Reticulum()
        print("✓ Reticulum initialized successfully")

        # Display basic status using correct API
        print(f"✓ Transport enabled: {RNS.Reticulum.transport_enabled()}")
        print(f"✓ Instance ready: {RNS.Reticulum.get_instance() is not None}")

        # Load or create server identity
        identity, was_created = get_or_create_identity()
        print(f"✓ {'Created' if was_created else 'Loaded'} server identity: {RNS.prettyhexrep(identity.hash)}")

        # Create destination for this server
        destination = create_destination(identity)
        app_name, aspect = config.app_context()

        print(f"✓ Server destination: {RNS.prettyhexrep(destination.hash)}")
        print(f"✓ App context: {app_name}.{aspect}")

        # Ensure public directory exists with default content
        print(f"✓ Public directory: {config.public_dir()}")

        created = ensure_public_directory()
        if created:
            print(f"✓ Created public directory: {config.public_dir()}")
            print(f"✓ Created default file: {config.default_file()}")

        # Start Link server with HTTP handler
        start_link_server(destination, http_handler)

        # Start periodic announcer
        start_announcer(destination)

        print("\nRServer is running. Press Ctrl+C to exit.")
        print()

        # Keep the program running (use timeout-based wait so Ctrl+C is handled)
        stop_event = threading.Event()
        while not stop_event.wait(timeout=1):
            # loop wakes every second to allow KeyboardInterrupt handling
            continue

    except KeyboardInterrupt:
        print("\nShutting down RServer...")
        RNS.exit()
        sys.exit(0)

    except Exception as e:
        print(f"✗ Error initializing Reticulum: {e}")
        sys.exit(1)


def start_announcer(destination):
    """Start a daemon thread that periodically calls `destination.announce()`.
    """
    interval = config.announce_interval()
    app_data = config.server_name().encode("utf-8")

    def _announcer():
        # Announce immediately, then every `interval` seconds
        while True:
            try:
                destination.announce(app_data=app_data)
                print("✓ Server announced on Reticulum network")
            except Exception as ae:
                print(f"✗ Announcement failed: {ae}")
            time.sleep(interval)

    t = threading.Thread(target=_announcer, daemon=True)
    t.start()
    return t


if __name__ == "__main__":
    main()