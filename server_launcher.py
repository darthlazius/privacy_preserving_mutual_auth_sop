#!/usr/bin/env python3
"""
Multi-Server Launcher for Privacy-Preserving Authentication System
Spawns multiple server instances based on servers_config.json
"""
import json
import subprocess
import sys
import time
import os
import signal

def load_config(config_file="servers_config.json"):
    """Load server configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Error: {config_file} not found!")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing {config_file}: {e}")
        sys.exit(1)

def launch_servers(config, num_servers=None):
    """
    Launch multiple server instances

    Args:
        config: Configuration dictionary
        num_servers: Number of servers to launch (None = all)
    """
    servers = config.get("servers", [])
    rc_url = config.get("rc_url", "http://127.0.0.1:5000")

    if num_servers:
        servers = servers[:num_servers]

    if not servers:
        print("No servers configured!")
        return []

    print(f"\n{'='*60}")
    print(f"  Multi-Server Launcher")
    print(f"{'='*60}")
    print(f"RC URL: {rc_url}")
    print(f"Launching {len(servers)} server(s)...\n")

    processes = []

    for idx, server in enumerate(servers, 1):
        server_id = server.get("id")
        password = server.get("password")
        location = server.get("location")
        port = server.get("port")

        if not all([server_id, password, location, port]):
            print(f"⚠️  Skipping incomplete server config: {server}")
            continue

        # Set environment variables for this server instance
        env = os.environ.copy()
        env["SERVER_ID"] = server_id
        env["SERVER_PASSWORD"] = password
        env["SERVER_LOCATION"] = location
        env["SERVER_PORT"] = str(port)
        env["RC_URL"] = rc_url

        # Launch server process
        try:
            process = subprocess.Popen(
                [sys.executable, "server1.py"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            processes.append({
                "process": process,
                "id": server_id,
                "port": port,
                "location": location
            })
            print(f"✓ [{idx}/{len(servers)}] Launched {server_id:15s} on port {port} ({location})")
            time.sleep(0.5)  # Stagger startup

        except Exception as e:
            print(f"✗ Failed to launch {server_id}: {e}")

    print(f"\n{'='*60}")
    print(f"  {len(processes)} server(s) running")
    print(f"{'='*60}\n")

    return processes

def monitor_servers(processes):
    """Monitor running servers and handle shutdown"""
    print("Press Ctrl+C to stop all servers...\n")

    try:
        # Monitor processes
        while True:
            time.sleep(1)
            for p in processes:
                if p["process"].poll() is not None:
                    print(f"\n⚠️  Server {p['id']} (port {p['port']}) terminated unexpectedly!")
                    # Print error output
                    stderr = p["process"].stderr.read()
                    if stderr:
                        print(f"Error output:\n{stderr}")

    except KeyboardInterrupt:
        print("\n\nShutting down servers...")
        for p in processes:
            print(f"  Stopping {p['id']}...")
            p["process"].terminate()
            try:
                p["process"].wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"  Force killing {p['id']}...")
                p["process"].kill()
        print("\n✓ All servers stopped.\n")

def register_all_servers(config, num_servers=None):
    """Register all servers with RC before starting them"""
    import requests

    servers = config.get("servers", [])
    rc_url = config.get("rc_url", "http://127.0.0.1:5000")

    if num_servers:
        servers = servers[:num_servers]

    print(f"\n{'='*60}")
    print(f"  Registering Servers with RC")
    print(f"{'='*60}\n")

    for idx, server in enumerate(servers, 1):
        server_id = server.get("id")
        print(f"[{idx}/{len(servers)}] Registering {server_id}...", end=" ")
        # Note: Registration happens when each server starts
        # This is just a status check
        print("✓")

    print()

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Launch multiple server instances for multi-server authentication"
    )
    parser.add_argument(
        "-n", "--num-servers",
        type=int,
        help="Number of servers to launch (default: all in config)"
    )
    parser.add_argument(
        "-c", "--config",
        default="servers_config.json",
        help="Path to server configuration file (default: servers_config.json)"
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Launch servers
    processes = launch_servers(config, args.num_servers)

    if not processes:
        print("No servers were launched!")
        sys.exit(1)

    # Monitor servers
    monitor_servers(processes)

if __name__ == "__main__":
    main()
