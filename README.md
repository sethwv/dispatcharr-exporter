# Dispatcharr Prometheus Exporter Plugin

A Dispatcharr-compatible plugin that exposes metrics in Prometheus format for monitoring and alerting.

## Installation

### Download Latest Release

Download the latest version from the [GitHub Releases page](https://github.com/sethwv/dispatcharr-exporter/releases/latest).

Look for the asset named `dispatcharr-exporter-X.X.X.zip` and download it.

### Installing the Plugin

1. Download `dispatcharr-exporter-X.X.X.zip` from the [latest release](https://github.com/sethwv/dispatcharr-exporter/releases/latest)

2. In the Dispatcharr web UI, navigate to the **Plugins** page

3. Click the **"Import"** button and upload the downloaded zip file

4. Enable the plugin (you'll see a trust warning on first enable - this is normal)

5. Configure the plugin settings (see Configuration section below)

6. **⚠️ IMPORTANT: Restart Dispatcharr** after installing the plugin for it to fully initialize

### Alternative: Build from Source

1. Clone the repository and package the plugin:
   ```bash
   git clone https://github.com/sethwv/dispatcharr-exporter.git
   cd dispatcharr-exporter
   ./package.sh
   ```
   This creates `dispatcharr-exporter-dev-XXXXXXXX-XXXXXXXXXXXX.zip`

2. Import the zip file via the Plugins page in Dispatcharr UI

3. **⚠️ IMPORTANT: Restart Dispatcharr** after installation

## Usage

### Starting the Metrics Server

**Option 1: Auto-start (Recommended for Production)**
1. Set "Auto-start Server" to `true` in plugin settings
2. Save settings
3. Restart Dispatcharr
4. Server will start automatically on first plugin initialization

**Option 2: Manual Start**
1. Configure the port and host in plugin settings
2. Click "Start Metrics Server" action
3. Server will start in background

### Accessing Metrics

Once the server is started, metrics are available at:
(You may need to map this port if running in docker)
```
http://your-dispatcharr-host:9192/metrics
http://your-dispatcharr-host:9192/health
```

## Features

This plugin collects and exposes the following metrics from your Dispatcharr instance:

### Core Metrics
- `dispatcharr_info` - Dispatcharr version and instance information (includes timestamp for dev builds)

### M3U Account Metrics (Optional - Default: Enabled)
- `dispatcharr_m3u_accounts` - Total and active M3U accounts
- `dispatcharr_m3u_account_status` - Account status breakdown (idle, fetching, parsing, error, success, etc.)
- `dispatcharr_profile_connections` - Current connections per M3U profile
- `dispatcharr_profile_max_connections` - Maximum allowed connections per profile  
- `dispatcharr_profile_connection_usage` - Connection usage ratio (0.0 to 1.0)

### EPG Source Metrics (Optional - Default: Disabled)
- `dispatcharr_epg_sources` - Total and active EPG sources
- `dispatcharr_epg_source_status` - EPG source status breakdown

### Channel Metrics
- `dispatcharr_channels` - Total and enabled channels
- `dispatcharr_channel_groups` - Total number of channel groups

### Stream Metrics
- `dispatcharr_active_streams` - Total number of active streams
- `dispatcharr_stream_info` - Detailed information about each active stream with labels:
  - `stream_index` - Position of stream in channel's stream list
  - `channel_uuid` - Channel UUID
  - `channel_name` - Channel name
  - `channel_number` - Channel number
  - `stream_id` - Stream ID
  - `stream_name` - Stream name
  - `provider` - M3U account/provider name (optional)
  - `provider_type` - Provider type (STD/XC) (optional)
  - `profile_id` - M3U profile ID
  - `profile_name` - M3U profile name
  - `logo_url` - Channel logo URL (optional)

### VOD (Video on Demand) Metrics (Optional - Default: Disabled)
- `dispatcharr_vod_sessions` - Total number of VOD sessions
- `dispatcharr_vod_active_streams` - Total number of active VOD streams

## Configuration

### Plugin Settings

- **Auto-start Server** (boolean, default: `false`): Automatically start metrics server when Dispatcharr starts
  - Note: Auto-start behavior is locked in at Dispatcharr startup and cannot be changed at runtime
- **Metrics Server Port** (number, default: `9192`): Port for the HTTP metrics server
- **Metrics Server Host** (string, default: `0.0.0.0`): Host address to bind
  - `0.0.0.0` - Listen on all network interfaces (accessible remotely)
  - `127.0.0.1` - Listen only on localhost (local access only)

### Metric Visibility Controls

- **Include M3U Account Metrics** (boolean, default: `true`): Include M3U account and profile connection metrics
- **Include EPG Source Metrics** (boolean, default: `false`): Include EPG source status metrics
- **Include VOD Metrics** (boolean, default: `false`): Include VOD session and stream metrics
- **Include Source URLs** (boolean, default: `false`): Include provider/source URLs in stream metrics
  - Warning: May expose sensitive information in metrics

### Plugin Actions

- **Start Metrics Server**: Starts the HTTP server on the configured port
- **Stop Metrics Server**: Stops the HTTP server
- **Restart Metrics Server**: Restarts the server (useful after changing settings)
- **Check Server Status**: Shows if the server is running and the endpoint URL

## License

This plugin is provided as-is for use with Dispatcharr.