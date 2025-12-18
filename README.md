# Dispatcharr Prometheus Exporter Plugin

A Dispatcharr-compatible plugin that exposes metrics in Prometheus format for monitoring and alerting.

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

## Installation

### Prerequisites

**No additional dependencies required!**

This plugin uses **gevent**, which is already installed as part of Dispatcharr's core dependencies.

### Method 1: Web UI Import (Recommended)

1. Package the plugin:
   ```bash
   ./package.sh
   ```
   This creates `prometheus_exporter.zip`

2. In the Dispatcharr web UI, navigate to the Plugins page

3. Click the "Import" button and upload `prometheus_exporter.zip`

4. Enable the plugin (you'll see a trust warning on first enable)

5. Configure the plugin settings (see Configuration section below)

### Method 2: Manual Installation

1. Copy the plugin directory to your Dispatcharr plugins folder:
   ```bash
   cp -r prometheus_exporter /path/to/dispatcharr/data/plugins/
   ```

2. In the Dispatcharr UI, navigate to the Plugins page and refresh

3. Enable the plugin and configure settings

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
- **Test Metrics Collection**: Returns a sample of metrics to verify collection is working

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
```
http://your-dispatcharr-host:9192/metrics
http://your-dispatcharr-host:9192/health
```

You can test it with curl:
```bash
curl http://localhost:9192/metrics
curl http://localhost:9192/health
```

## Prometheus Configuration

### Basic Setup

1. Add the following to your Prometheus configuration (`prometheus.yml`):

```yaml
scrape_configs:
  - job_name: 'dispatcharr'
    scrape_interval: 30s
    scrape_timeout: 10s
    static_configs:
      - targets: ['your-dispatcharr-host:9192']
        labels:
          instance: 'dispatcharr-main'
          environment: 'production'
```

2. Reload your Prometheus configuration:
   ```bash
   curl -X POST http://localhost:9090/-/reload
   # Or restart Prometheus
   systemctl restart prometheus
   ```

3. Verify metrics are being scraped in Prometheus UI:
   - Navigate to Status → Targets
   - Look for the `dispatcharr` job
   - Should show as "UP" with last scrape time

### Docker Compose Example

If running Prometheus in Docker:

```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    extra_hosts:
      - "host.docker.internal:host-gateway"

volumes:
  prometheus-data:
```

Use `host.docker.internal:9192` as the target if Dispatcharr is on the host machine.

## Example Metrics Output

```prometheus
# HELP dispatcharr_info Dispatcharr version and instance information
# TYPE dispatcharr_info gauge
dispatcharr_info{version="v0.14.0-20251215225427"} 1

# HELP dispatcharr_m3u_accounts Total number of M3U accounts
# TYPE dispatcharr_m3u_accounts gauge
dispatcharr_m3u_accounts{status="total"} 5
dispatcharr_m3u_accounts{status="active"} 4

# HELP dispatcharr_channels Total number of channels
# TYPE dispatcharr_channels gauge
dispatcharr_channels{status="total"} 150
dispatcharr_channels{status="enabled"} 142

# HELP dispatcharr_profile_connections Current connections per M3U profile
# TYPE dispatcharr_profile_connections gauge
dispatcharr_profile_connections{profile_id="1",profile_name="Default",account_name="Main IPTV"} 3

# HELP dispatcharr_profile_max_connections Maximum allowed connections per M3U profile
# TYPE dispatcharr_profile_max_connections gauge
dispatcharr_profile_max_connections{profile_id="1",profile_name="Default",account_name="Main IPTV"} 5

# HELP dispatcharr_profile_connection_usage Connection usage ratio per M3U profile
# TYPE dispatcharr_profile_connection_usage gauge
dispatcharr_profile_connection_usage{profile_id="1",profile_name="Default",account_name="Main IPTV"} 0.6000

# HELP dispatcharr_active_streams Total number of active streams
# TYPE dispatcharr_active_streams gauge
dispatcharr_active_streams 12

# HELP dispatcharr_stream_info Detailed information about active streams
# TYPE dispatcharr_stream_info gauge
dispatcharr_stream_info{stream_index="0",channel_uuid="abc-123",channel_name="ESPN",channel_number="501",stream_id="789",stream_name="ESPN HD",profile_id="1",profile_name="Default",logo_url="http://example.com/logo.png"} 1
```

## Example Prometheus Queries

### Connection Monitoring

```promql
# Alert when any profile reaches 90% of max connections
dispatcharr_profile_connection_usage > 0.9

# Profiles currently at capacity
dispatcharr_profile_connection_usage >= 1.0

# Average connection usage across all profiles
avg(dispatcharr_profile_connection_usage) * 100
```

### Stream Analytics

```promql
# Total active streams
dispatcharr_active_streams

# Streams by profile
count by (profile_name) (dispatcharr_stream_info)

# Channels with active streams
count(dispatcharr_stream_info) by (channel_name)
```

### M3U Account Health

```promql
# Count of M3U accounts by status
sum by (status) (dispatcharr_m3u_account_status)

# Accounts in error state
dispatcharr_m3u_account_status{status="error"}

# Active vs total accounts
dispatcharr_m3u_accounts{status="active"} / dispatcharr_m3u_accounts{status="total"}
```

### VOD Monitoring (if enabled)

```promql
# Total VOD sessions
dispatcharr_vod_sessions

# VOD stream activity
dispatcharr_vod_active_streams
```

## Alerting Rules

Example Prometheus alerting rules (`dispatcharr_alerts.yml`):

```yaml
groups:
  - name: dispatcharr
    interval: 30s
    rules:
      - alert: DispatcharrHighConnectionUsage
        expr: dispatcharr_profile_connection_usage > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High connection usage on {{ $labels.profile_name }}"
          description: "Profile {{ $labels.profile_name }} is at {{ $value | humanizePercentage }} capacity"

      - alert: DispatcharrProfileAtCapacity
        expr: dispatcharr_profile_connection_usage >= 1.0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Profile {{ $labels.profile_name }} at maximum capacity"
          description: "Cannot accept new connections on {{ $labels.profile_name }}"

      - alert: DispatcharrM3UAccountError
        expr: dispatcharr_m3u_account_status{status="error"} > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "M3U account errors detected"
          description: "{{ $value }} M3U accounts in error state"

      - alert: DispatcharrDown
        expr: up{job="dispatcharr"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Dispatcharr metrics endpoint down"
          description: "Cannot scrape metrics from Dispatcharr"
```

## Grafana Dashboard

### Quick Start Panel Examples

**Active Streams Gauge:**
```json
{
  "type": "stat",
  "targets": [{
    "expr": "dispatcharr_active_streams"
  }],
  "title": "Active Streams"
}
```

**Connection Usage Graph:**
```json
{
  "type": "timeseries",
  "targets": [{
    "expr": "dispatcharr_profile_connection_usage",
    "legendFormat": "{{profile_name}}"
  }],
  "title": "Profile Connection Usage",
  "fieldConfig": {
    "defaults": {
      "unit": "percentunit",
      "min": 0,
      "max": 1
    }
  }
}
```

**M3U Account Status Table:**
```json
{
  "type": "table",
  "targets": [{
    "expr": "dispatcharr_m3u_account_status",
    "format": "table"
  }],
  "title": "M3U Account Status"
}
```

## Troubleshooting

### Server Won't Start

- **Check port availability**: `netstat -tuln | grep 9192`
- **Verify gevent**: Should be installed with Dispatcharr
- **Check logs**: Look for errors in Dispatcharr logs
- **Try different port**: Change port in settings if 9192 is in use

### Metrics Endpoint Not Accessible

- **Verify server is running**: Use "Check Server Status" action
- **Check firewall**: Ensure port 9192 is open
- **Test locally first**: `curl http://localhost:9192/metrics`
- **Check host binding**: Use `0.0.0.0` to listen on all interfaces

### No Metrics Data / Empty Response

- **Test collection**: Use "Test Metrics Collection" action
- **Check Redis**: Ensure Redis is running (required for some metrics)
- **Enable metric categories**: Check M3U/EPG/VOD settings
- **Verify plugin enabled**: Plugin must be enabled in Dispatcharr

### Auto-start Not Working

- **Check setting**: Verify "Auto-start Server" is enabled
- **Restart Dispatcharr**: Auto-start only triggers on Dispatcharr startup
- **Check logs**: Look for auto-start messages in logs
- **Port conflict**: Auto-start will fail if port is already in use

### High Cardinality Warnings

If Prometheus shows high cardinality warnings:
- Disable "Include Source URLs" (contains unique values)
- Reduce number of enabled channels if possible
- Consider using recording rules to pre-aggregate metrics

## Technical Details

### Architecture

- **Server**: Lightweight gevent WSGI server (non-blocking, efficient)
- **Isolation**: Runs independently of Dispatcharr's main web server
- **Multi-worker Safe**: Uses Redis flags and file locking for coordination
- **Auto-start**: Single execution per Dispatcharr instance via Redis completion flag

### Metric Collection

- Metrics are generated fresh on each Prometheus scrape (no caching)
- Uses lazy-loaded Redis client for efficiency
- Conditional metric collection based on settings
- Optimized queries to minimize database load

### State Management

- **Redis Keys Used**:
  - `prometheus_exporter:server_running` - Server running flag
  - `prometheus_exporter:server_host` - Current server host
  - `prometheus_exporter:server_port` - Current server port
  - `prometheus_exporter:stop_requested` - Stop signal flag
  - `prometheus_exporter:autostart_completed` - Auto-start completion flag

- **Lock File**: `/tmp/prometheus_exporter_autostart.lock` - Prevents duplicate auto-starts

## Requirements

- Dispatcharr with plugin support
- Redis (for real-time metrics and state management)
- Prometheus server for scraping (optional, for full monitoring)

## Version

**Current Version**: 1.0.22

### Recent Changes
- Added full dev version support (includes timestamp)
- Improved auto-start behavior (locked at Dispatcharr startup)
- Fixed restart server stop signal handling
- Added stream index to stream metrics
- Enhanced server status URL reporting
- Reorganized settings for better UX

## License

This plugin is provided as-is for use with Dispatcharr.

## Support

For issues, feature requests, or questions:
- Check the Troubleshooting section above
- Review Dispatcharr logs for errors
- Verify Prometheus configuration
- Test metrics collection using plugin actions
