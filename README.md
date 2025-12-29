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

The exporter provides a layered metric structure optimized for Prometheus queries:

#### Value Metrics (minimal labels for efficient queries)
All value metrics use only `channel_uuid` and `channel_number` as labels, allowing efficient queries and joins:

- `dispatcharr_active_streams` - Total number of active streams
- `dispatcharr_stream_viewers` - Current number of viewers per stream (gauge)
- `dispatcharr_stream_uptime_seconds` - Stream uptime in seconds since started (counter)
- `dispatcharr_stream_active_clients` - Number of active clients connected (gauge)
- `dispatcharr_stream_fps` - Stream frames per second (gauge)
- `dispatcharr_stream_video_bitrate_kbps` - Source video bitrate in kbps (gauge)
- `dispatcharr_stream_transcode_bitrate_kbps` - Transcode output bitrate in kbps (gauge)
- `dispatcharr_stream_avg_bitrate_kbps` - Calculated average bitrate in kbps (gauge)
- `dispatcharr_stream_total_transfer_mb` - Total data transferred in megabytes (counter)
- `dispatcharr_stream_profile_connections` - Current connections for the M3U profile (gauge)
- `dispatcharr_stream_profile_max_connections` - Maximum connections allowed for the M3U profile (gauge)

#### Context Metrics (for enrichment via joins)

All context metrics use the same minimal labels (`channel_uuid`, `channel_number`) for consistency:

- `dispatcharr_stream_channel_number` - Channel number as a numeric gauge:
  - **Value**: The channel number (e.g., 1001.0, 1015.0)
  - Use for: Sorting channels, finding gaps, numeric operations

- `dispatcharr_stream_id` - Active stream ID:
  - **Value**: The database ID of the currently active stream
  - Use for: Tracking which specific stream is active, detecting stream changes

- `dispatcharr_stream_index` - Active stream index:
  - **Value**: The stream index (position in channel's stream list, 0-based)
  - Use to detect fallback: `dispatcharr_stream_index > 0` means backup stream is active

- `dispatcharr_stream_metadata` - Full stream metadata with all identifying labels:
  - `channel_uuid`, `channel_number`, `channel_name`
  - `stream_id`, `stream_name`
  - `provider`, `provider_type`
  - `state` (active, buffering, error, etc.)
  - `logo_url` - Channel logo URL
  - `profile_id`, `profile_name` - M3U profile information
  - `stream_profile` - Transcode profile name
  - `video_codec` - Video codec (h264, hevc, etc.)
  - `resolution` - Video resolution (1920x1080, etc.)
  - **Value**: Always 1 (info metric pattern)
  - **Output**: Always last for each stream

### Client Connection Metrics (Optional - Default: Disabled)

Individual client connection statistics:

- `dispatcharr_active_clients` - Total number of active client connections
- `dispatcharr_client_info` - Client metadata (info metric with IP, user agent, etc.)
- `dispatcharr_client_connection_duration_seconds` - How long the client has been connected (gauge)
- `dispatcharr_client_bytes_sent` - Total bytes sent to this client (counter)
- `dispatcharr_client_avg_transfer_rate_kbps` - Average transfer rate to client in kbps (gauge)
- `dispatcharr_client_current_transfer_rate_kbps` - Current transfer rate to client in kbps (gauge)

All client metrics use minimal labels (`client_id`, `channel_uuid`, `channel_number`) for efficient queries, with full metadata in `dispatcharr_client_info`.

#### Querying Stream Metrics

**Basic queries** (no joins needed):
```promql
# Current FPS for all streams
dispatcharr_stream_fps

# Uptime for specific channel
dispatcharr_stream_uptime_seconds{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1"}

# Total data transferred across all channels
sum(dispatcharr_stream_total_transfer_mb)

# Sort channels by channel number
sort(dispatcharr_stream_channel_number)

# Find channels with numbers over 2000
dispatcharr_stream_channel_number > 2000

# Detect stream fallback (backup stream active)
dispatcharr_stream_index > 0

# Track stream changes (value changes indicate stream switched)
dispatcharr_stream_id
```

**Client queries**:
```promql
# Connection duration for all clients
dispatcharr_client_connection_duration_seconds

# Clients with connection duration over 1 hour
dispatcharr_client_connection_duration_seconds > 3600

# Total bytes sent to all clients for a channel
sum by (channel_uuid) (dispatcharr_client_bytes_sent)

# Client info with IP addresses (requires include_client_stats enabled)
dispatcharr_client_info
```

**Enriched queries** (join with context metrics):
```promql
# Get uptime with stream index value
dispatcharr_stream_uptime_seconds 
  + on(channel_uuid, channel_number) 
  dispatcharr_stream_index

# Get FPS with provider information
dispatcharr_stream_fps 
  * on(channel_uuid, channel_number) group_left(stream_id, provider, stream_name) 
  dispatcharr_stream_metadata

# Get total transfer with full metadata (codec, resolution, logo)
dispatcharr_stream_total_transfer_mb 
  * on(channel_uuid, channel_number) group_left(logo_url, resolution, video_codec, provider) 
  dispatcharr_stream_metadata

# Client transfer rate with IP address and user agent
dispatcharr_client_avg_transfer_rate_kbps
  * on(client_id, channel_uuid, channel_number) group_left(ip_address, user_agent)
  dispatcharr_client_info

# Client transfer rate with channel name (join with stream metadata)
dispatcharr_client_avg_transfer_rate_kbps
  * on(client_id, channel_uuid, channel_number) group_left(ip_address)
  (dispatcharr_client_info
    * on(channel_uuid, channel_number) group_left(channel_name)
    dispatcharr_stream_metadata)

# Alert when stream falls back to backup provider
dispatcharr_stream_index > 0
```

**Why this structure?**
- Minimal labels on frequently-scraped value metrics = lower cardinality and better performance
- Context/metadata in separate metrics = join only when needed
- `channel_uuid` + `channel_number` as common join keys = simple, efficient queries
- Follows Prometheus best practices for info/metadata patterns

#### Legacy Metrics (Deprecated)

For backward compatibility with v1.1.0 and earlier dashboards, you can enable:

- `dispatcharr_stream_info` - All stream information with values as labels (NOT recommended)
  - Enable via "Include Legacy Metric Formats" setting
  - Creates new time series whenever any value changes
  - Use the new layered metrics instead for proper time series tracking

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