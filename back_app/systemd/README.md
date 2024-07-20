## Setup

```
sudo ./setup_services user
```

### Restart all services
```
sudo systemctl restart analytics.target
```

### Get info
```
sudo systemctl status analytics*
sudo systemctl status analytics*|grep active|nl
```

## Manage

# Analytics Service Manager

## Overview

The Analytics Service Manager is a Python script designed to manage systemd services for an analytics system. It provides functionality to start, stop, restart, and view logs for various analytics services.

## Features

- Start all or specific analytics services
- Stop all or specific analytics services
- Restart all or specific analytics services
- View logs for all or specific services
- Option to follow logs in real-time

## Requirements

- Python 3.x
- sudo privileges to run systemctl commands

## Usage

The general syntax for using the script is:

```
./analytics_manager.py <action> [--services <service_names>] [--follow]
```

### Actions

- `start`: Start services
- `stop`: Stop services
- `restart`: Restart services
- `logs`: View service logs

### Options

- `--services`: Specify which services to manage. Can be one or more of the following:
    - `analytics_base_8_2_snapshot`
    - `analytics_bnb_8_2_snapshot`
    - `analytics_blast_8_2_snapshot`
    - `analytics_mantle_8_2_snapshot`
    - `analytics_arbitrum_8_2_snapshot`
    - `analytics_server`
    - `all` (default)
- `--follow`: Follow logs in real-time (only applicable with the `logs` action)

## Examples

1. Start all services:
   ```
   ./analytics_manager.py start
   ```

2. Stop specific services:
   ```
   ./analytics_manager.py stop --services analytics_base_8_2_snapshot analytics_server
   ```

3. Restart specific services:
   ```
   ./analytics_manager.py restart --services analytics_arbitrum_8_2_snapshot analytics_server
   ```

4. View logs for all services:
   ```
   ./analytics_manager.py logs
   ```

5. Follow logs for specific services:
   ```
   ./analytics_manager.py logs --services analytics_arbitrum_8_2_snapshot analytics_server --follow
   ```

- The script uses `sudo` to run systemctl commands, so you'll need to run it with appropriate permissions.
- If you add or remove services, update the `SERVICES` list in the script accordingly.

## Troubleshooting
- If you encounter permission errors, make sure you have sudo privileges.
- If a service fails to start, stop, or restart, check the system logs for more detailed error messages.
