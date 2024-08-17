#!/usr/bin/env python3

import argparse
import subprocess

SERVICES = [
    "analytics_base_8_2_snapshot",
    "analytics_bnb_8_2_snapshot",
    "analytics_blast_8_2_snapshot",
    "analytics_mantle_8_2_snapshot",
    "analytics_arbitrum_8_2_snapshot",
    "analytics_server",
]


def run_command(command):
    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(e.stderr)


def start_services(services):
    for service in services:
        print(f"Starting {service}")
        run_command(["sudo", "systemctl", "start", f"{service}.service"])


def stop_services(services):
    for service in services:
        print(f"Stopping {service}")
        run_command(["sudo", "systemctl", "stop", f"{service}.service"])


def restart_services(services):
    for service in services:
        print(f"Restarting {service}")
        run_command(["sudo", "systemctl", "restart", f"{service}.service"])


def view_logs(services, follow):
    command = ["sudo", "journalctl"]
    for service in services:
        command.extend(["-u", f"{service}.service"])
    if follow:
        command.append("-f")
    run_command(command)


def main():
    parser = argparse.ArgumentParser(description="Manage Analytics Services")
    parser.add_argument("action", choices=["start", "stop", "restart", "logs"], help="Action to perform")
    parser.add_argument("--services", nargs="*", choices=SERVICES + ["all"], default="all",
                        help="Services to manage (default: all)")
    parser.add_argument("--follow", action="store_true", help="Follow logs in real-time")

    args = parser.parse_args()

    if args.services == "all" or "all" in args.services:
        selected_services = SERVICES
    else:
        selected_services = args.services

    if args.action == "start":
        start_services(selected_services)
    elif args.action == "stop":
        stop_services(selected_services)
    elif args.action == "restart":
        restart_services(selected_services)
    elif args.action == "logs":
        view_logs(selected_services, args.follow)


if __name__ == "__main__":
    main()
