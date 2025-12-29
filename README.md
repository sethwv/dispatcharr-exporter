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

### Updating the Plugin

> **Note:** The Dispatcharr plugin system is currently in early development. To update to a newer version:

1. In the Dispatcharr web UI, go to the **Plugins** page and disable/remove the plugin
2. Download the latest version from [releases](https://github.com/sethwv/dispatcharr-exporter/releases/latest)
3. Import the new version via the **"Import"** button
4. **⚠️ IMPORTANT: Restart Dispatcharr** for the update to take effect

### Uninstalling the Plugin

> **Note:** Due to the early state of the plugin system, you may need to manually remove files:

1. Stop Dispatcharr
2. Remove the plugin directory:
   ```bash
   rm -rf /path/to/dispatcharr/data/plugins/prometheus_exporter*
   ```
3. Start Dispatcharr
4. Go to the **Plugins** page and remove the plugin from the UI (if still listed)

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

This plugin exposes comprehensive Prometheus metrics for monitoring your Dispatcharr instance:

- **Core metrics** - Version and instance information
- **M3U account metrics** - Account status and connection tracking (enabled by default)
- **EPG source metrics** - EPG source status (optional)
- **Channel metrics** - Channel and group counts
- **Stream metrics** - Real-time stream statistics with optimized label structure
- **Client connection metrics** - Individual client tracking and transfer statistics (optional, privacy-focused)
- **VOD metrics** - Video on Demand session tracking (optional)

For a complete list of available metrics, query examples, and best practices, see **[METRICS.md](METRICS.md)**.

## Configuration

### Plugin Settings

- **Auto-start Server** (boolean, default: `false`): Automatically start metrics server when Dispatcharr starts
- **Metrics Server Port** (number, default: `9192`): Port for the HTTP metrics server
- **Metrics Server Host** (string, default: `0.0.0.0`): Host address to bind
  - `0.0.0.0` - Listen on all network interfaces (accessible remotely)
  - `127.0.0.1` - Listen only on localhost (local access only)

### Metric Visibility Controls

- **Include M3U Account Metrics** (boolean, default: `true`): Include M3U account and profile connection metrics
- **Include EPG Source Metrics** (boolean, default: `false`): Include EPG source status metrics
- **Include VOD Metrics** (boolean, default: `false`): Include VOD session and stream metrics
- **Include Client Connection Statistics** (boolean, default: `false`): Include individual client connection information
  - Warning: May expose sensitive information in metrics
- **Include Source URLs** (boolean, default: `false`): Include provider/source URLs in stream metrics
  - Warning: May expose sensitive information in metrics
- **Include Legacy Metric Formats** (boolean, default: `false`): Include backward-compatible metrics from v1.1.0 and earlier
  - Only enable if you have existing dashboards that need migration time
  - NOT recommended - use the new layered metrics instead for proper time series

### Plugin Actions

- **Start Metrics Server**: Starts the HTTP server on the configured port
- **Stop Metrics Server**: Stops the HTTP server
- **Restart Metrics Server**: Restarts the server (useful after changing settings)
- **Check Server Status**: Shows if the server is running and the endpoint URL

## License

This plugin is provided as-is for use with Dispatcharr.