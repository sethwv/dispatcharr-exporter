# Dispatcharr Exporter Metrics Reference

Complete reference for all metrics exposed by the Dispatcharr Prometheus Exporter plugin.

## Table of Contents

- [Core Metrics](#core-metrics)
- [Exporter Metrics](#exporter-metrics)
- [M3U Account Metrics](#m3u-account-metrics)
- [EPG Source Metrics](#epg-source-metrics)
- [Channel Metrics](#channel-metrics)
- [Stream Metrics](#stream-metrics)
- [Profile Metrics](#profile-metrics)
- [VOD Metrics](#vod-metrics)
- [Legacy Metrics](#legacy-metrics)

---

## Core Metrics

### `dispatcharr_info`
**Type:** gauge  
**Value:** Always 1  
**Labels:**
- `version` - Dispatcharr version (includes timestamp for dev builds)

**Description:** Provides version information about the Dispatcharr instance.

**Example:**
```
dispatcharr_info{version="v0.1.0-20251222123417"} 1
```

---

## Exporter Metrics

### `dispatcharr_exporter_info`
**Type:** gauge  
**Value:** Always 1  
**Labels:**
- `version` - Exporter plugin version

**Description:** Provides version information about the exporter plugin.

**Example:**
```
dispatcharr_exporter_info{version="1.2.0"} 1
```

### `dispatcharr_exporter_settings_info`
**Type:** gauge  
**Value:** Always 1  
**Labels:** All plugin settings as labels (for debugging/support)
- `auto_start` - Auto-start enabled (true/false)
- `suppress_access_logs` - Access log suppression (true/false)
- `disable_update_notifications` - Update notifications disabled (true/false)
- `port` - Metrics server port
- `host` - Metrics server host
- `base_url` - Dispatcharr base URL
- `include_m3u_stats` - M3U stats included (true/false)
- `include_epg_stats` - EPG stats included (true/false)
- `include_vod_stats` - VOD stats included (true/false)
- `include_client_stats` - Client stats included (true/false)
- `include_source_urls` - Source URLs included (true/false)
- `include_legacy_metrics` - Legacy metrics included (true/false)

**Description:** Info metric showing all exporter configuration settings.

**Example:**
```
dispatcharr_exporter_settings_info{auto_start="true",suppress_access_logs="true",disable_update_notifications="false",port="9192",host="0.0.0.0",base_url="",include_m3u_stats="true",include_epg_stats="false",include_vod_stats="false",include_client_stats="false",include_source_urls="false",include_legacy_metrics="false"} 1
```

### `dispatcharr_exporter_port`
**Type:** gauge  
**Value:** The configured port number  
**Labels:** None

**Description:** The port number the metrics server is configured to run on.

**Example:**
```
dispatcharr_exporter_port 9192
```

---

## M3U Account Metrics

*Optional metrics - enabled by default via `include_m3u_stats` setting*

### `dispatcharr_m3u_accounts`
**Type:** gauge  
**Value:** Account count  
**Labels:**
- `status` - "total" or "active"

**Description:** Total number of M3U accounts and active M3U accounts.

**Example:**
```
dispatcharr_m3u_accounts{status="total"} 5
dispatcharr_m3u_accounts{status="active"} 4
```

### `dispatcharr_m3u_account_status`
**Type:** gauge  
**Value:** Count of accounts with this status  
**Labels:**
- `status` - Account status (idle, fetching, parsing, error, success, etc.)

**Description:** Breakdown of M3U account counts by status.

**Example:**
```
dispatcharr_m3u_account_status{status="success"} 3
dispatcharr_m3u_account_status{status="error"} 1
dispatcharr_m3u_account_status{status="idle"} 1
```

### `dispatcharr_m3u_account_stream_count`
**Type:** gauge  
**Value:** Number of streams configured for this account  
**Labels:**
- `account_id` - Account database ID
- `account_name` - Account name
- `account_type` - Account type (XC, STD, etc.)
- `status` - Account status
- `is_active` - Active state (true/false)
- `username` - XC username (optional, only if `include_source_urls=true`)
- `server_url` - Server URL (optional, only if `include_source_urls=true`)

**Description:** Number of streams configured for each M3U account.

**Example:**
```
dispatcharr_m3u_account_stream_count{account_id="1",account_name="Provider A",account_type="XC",status="success",is_active="true"} 150
```

---

## EPG Source Metrics

*Optional metrics - disabled by default via `include_epg_stats` setting*

### `dispatcharr_epg_sources`
**Type:** gauge  
**Value:** Source count  
**Labels:**
- `status` - "total" or "active"

**Description:** Total number of EPG sources and active EPG sources.

**Example:**
```
dispatcharr_epg_sources{status="total"} 3
dispatcharr_epg_sources{status="active"} 2
```

### `dispatcharr_epg_source_status`
**Type:** gauge  
**Value:** Count of sources with this status  
**Labels:**
- `status` - EPG source status

**Description:** Breakdown of EPG source counts by status.

**Example:**
```
dispatcharr_epg_source_status{status="success"} 2
dispatcharr_epg_source_status{status="error"} 1
```

### `dispatcharr_epg_source_priority`
**Type:** gauge  
**Value:** Priority value (lower is higher priority)  
**Labels:**
- `source_id` - EPG source database ID
- `source_name` - EPG source name
- `source_type` - Source type (xmltv, m3u, etc.)
- `status` - Source status
- `is_active` - Active state (true/false)
- `url` - Source URL (optional, only if `include_source_urls=true`)

**Description:** Priority value for each EPG source.

**Example:**
```
dispatcharr_epg_source_priority{source_id="1",source_name="EPG Source 1",source_type="xmltv",status="success",is_active="true"} 1
```

---

## Channel Metrics

### `dispatcharr_channels`
**Type:** gauge  
**Value:** Channel count  
**Labels:**
- `status` - "total"

**Description:** Total number of channels.

**Example:**
```
dispatcharr_channels{status="total"} 250
```

### `dispatcharr_channel_groups`
**Type:** gauge  
**Value:** Channel group count  
**Labels:** None

**Description:** Total number of channel groups.

**Example:**
```
dispatcharr_channel_groups 15
```

---

## Stream Metrics

### Value Metrics (Minimal Labels)

All value metrics use only `channel_uuid` and `channel_number` as labels for efficient querying and joining.

#### `dispatcharr_active_streams`
**Type:** gauge  
**Value:** Count of active streams  
**Labels:** None

**Description:** Total number of currently active streams.

**Example:**
```
dispatcharr_active_streams 12
```

#### `dispatcharr_stream_uptime_seconds_total`
**Type:** counter  
**Value:** Seconds since stream started  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Stream uptime in seconds. Resets when stream restarts.

**Example:**
```
dispatcharr_stream_uptime_seconds_total{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 3847
```

#### `dispatcharr_stream_active_clients`
**Type:** gauge  
**Value:** Number of connected clients  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Number of active clients connected to this stream.

**Example:**
```
dispatcharr_stream_active_clients{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 1
```

#### `dispatcharr_stream_fps`
**Type:** gauge  
**Value:** Frames per second  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Current stream frames per second.

**Example:**
```
dispatcharr_stream_fps{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 59.94
```

#### `dispatcharr_stream_video_bitrate_bps`
**Type:** gauge  
**Value:** Bitrate in bits per second  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Source video bitrate in bits per second. Use Grafana's "bits/sec" unit for automatic formatting.

**Example:**
```
dispatcharr_stream_video_bitrate_bps{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 8500000
```

#### `dispatcharr_stream_transcode_bitrate_bps`
**Type:** gauge  
**Value:** Bitrate in bits per second  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Transcode output bitrate in bits per second. Use Grafana's "bits/sec" unit for automatic formatting.

**Example:**
```
dispatcharr_stream_transcode_bitrate_bps{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 5383400
```

#### `dispatcharr_stream_avg_bitrate_bps`
**Type:** gauge  
**Value:** Bitrate in bits per second  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Calculated average bitrate in bits per second (total bytes * 8 / uptime). Use Grafana's "bits/sec" unit for automatic formatting.

**Example:**
```
dispatcharr_stream_avg_bitrate_bps{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 5200500
```

#### `dispatcharr_stream_current_bitrate_bps`
**Type:** gauge  
**Value:** Bitrate in bits per second  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Current bitrate in bits per second (sum of all connected client transfer rates). Matches the "current bitrate" shown in Dispatcharr UI. Use Grafana's "bits/sec" unit for automatic formatting.

**Example:**
```
dispatcharr_stream_current_bitrate_bps{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 4820000
```

#### `dispatcharr_stream_total_transfer_mb`
**Type:** counter  
**Value:** Total megabytes transferred  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Total data transferred by this stream in megabytes.

**Example:**
```
dispatcharr_stream_total_transfer_mb{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 4096.25
```

### Context Metrics (For Enrichment)

All context metrics use minimal labels (`channel_uuid`, `channel_number`) for consistency.

#### `dispatcharr_stream_channel_number`
**Type:** gauge  
**Value:** The channel number  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Channel number as a numeric value for sorting and filtering.

**Example:**
```
dispatcharr_stream_channel_number{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 1001.0
```

#### `dispatcharr_stream_id`
**Type:** gauge  
**Value:** The stream database ID  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Database ID of the currently active stream. Value changes indicate stream switched.

**Example:**
```
dispatcharr_stream_id{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 2954
```

#### `dispatcharr_stream_index`
**Type:** gauge  
**Value:** The stream index (0-based)  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Position of active stream in channel's stream list. 0 = primary stream, >0 = fallback/backup stream.

**Example:**
```
dispatcharr_stream_index{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 0
```

#### `dispatcharr_stream_available_streams`
**Type:** gauge  
**Value:** Total number of streams configured  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Total number of streams configured for this channel. Useful with `dispatcharr_stream_index` to detect when channel is on its last available stream.

**Example:**
```
dispatcharr_stream_available_streams{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 3
```

**Useful queries:**
```promql
# Remaining backup streams available
dispatcharr_stream_available_streams - dispatcharr_stream_index - 1

# Alert when on last stream
dispatcharr_stream_index >= dispatcharr_stream_available_streams - 1
```

#### `dispatcharr_stream_metadata`
**Type:** gauge  
**Value:** Always 1  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number
- `channel_name` - Channel name
- `channel_group` - Channel group name (or "none" if not assigned)
- `stream_id` - Stream database ID
- `stream_name` - Stream name
- `provider` - M3U account/provider name
- `provider_type` - Provider type (XC, STD, etc.)
- `state` - Stream state (active, waiting_for_clients, buffering, error, etc.)
- `logo_url` - Channel logo URL
- `profile_id` - M3U profile database ID
- `profile_name` - M3U profile name
- `stream_profile` - Transcode profile name
- `video_codec` - Video codec (h264, hevc, etc.)
- `resolution` - Video resolution (1920x1080, etc.)

**Description:** Full metadata for the active stream. Always output last for each stream. Use for joining to enrich other metrics.

**Example:**
```
dispatcharr_stream_metadata{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0",channel_name="CBC Toronto",stream_id="2954",stream_name="CBC Toronto",provider="Provider A",provider_type="XC",state="active",logo_url="/api/channels/logos/1/cache/",profile_id="3",profile_name="Default",stream_profile="ffmpeg",video_codec="h264",resolution="1920x1080"} 1
```

#### `dispatcharr_stream_programming`
**Type:** gauge  
**Value:** Current program progress (0.0 to 1.0), or 0.0 if no current program  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number
- `previous_title` - Previous program title (empty string if none)
- `previous_subtitle` - Previous program subtitle/episode (empty string if none)
- `previous_description` - Previous program description (empty string if none)
- `previous_start_time` - Previous program start time in ISO format (empty string if none)
- `previous_end_time` - Previous program end time in ISO format (empty string if none)
- `current_title` - Current program title (empty string if none)
- `current_subtitle` - Current program subtitle/episode (empty string if none)
- `current_description` - Current program description (empty string if none)
- `current_start_time` - Current program start time in ISO format (empty string if none)
- `current_end_time` - Current program end time in ISO format (empty string if none)
- `next_title` - Next program title (empty string if none)
- `next_subtitle` - Next program subtitle/episode (empty string if none)
- `next_description` - Next program description (empty string if none)
- `next_start_time` - Next program start time in ISO format (empty string if none)
- `next_end_time` - Next program end time in ISO format (empty string if none)

**Description:** EPG program schedule information for the active stream. Only present if channel has EPG data assigned. The metric value represents how far into the current program we are (0.0 = just started, 1.0 = about to end). Labels provide previous, current, and next program information.

> **Note:** This metric only works with actual EPG data. Channels using placeholder or dummy EPG sources will not have this metric.

**Example:**
```
dispatcharr_stream_programming{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0",previous_title="Afternoon News",previous_subtitle="",previous_description="Local and national news coverage",previous_start_time="2026-01-02T17:00:00+00:00",previous_end_time="2026-01-02T18:00:00+00:00",current_title="The Evening News",current_subtitle="Special Report",current_description="Breaking news and analysis",current_start_time="2026-01-02T18:00:00+00:00",current_end_time="2026-01-02T19:00:00+00:00",next_title="Prime Time Drama",next_subtitle="Season 3 Episode 5",next_description="An exciting episode",next_start_time="2026-01-02T19:00:00+00:00",next_end_time="2026-01-02T20:00:00+00:00"} 0.5833
```

**Useful queries:**
```promql
# Time remaining in current program (minutes)
(1 - dispatcharr_stream_programming) * 
  (timestamp(dispatcharr_stream_programming{current_end_time!=""}) - 
   timestamp(dispatcharr_stream_programming{current_start_time!=""})) / 60

# Combine title and subtitle for display
label_join(
  dispatcharr_stream_programming,
  "program_full",
  " ",
  "current_title",
  "current_subtitle"
)

# Join with stream metadata for enriched dashboard
dispatcharr_stream_programming
* on(channel_uuid, channel_number) group_left(channel_name, logo_url, state)
  dispatcharr_stream_metadata
```

---

## Client Connection Metrics

*Optional metrics - disabled by default via `include_client_stats` setting*

### `dispatcharr_active_clients`
**Type:** gauge  
**Value:** Count of active client connections  
**Labels:** None

**Description:** Total number of currently active client connections across all streams.

**Example:**
```
dispatcharr_active_clients 15
```

### `dispatcharr_client_info`
**Type:** gauge  
**Value:** Always 1  
**Labels:**
- `client_id` - Unique client connection ID
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number
- `ip_address` - Client IP address
- `user_agent` - Client user agent string
- `worker_id` - Dispatcharr worker ID handling the connection

**Description:** Metadata for each connected client. Use for enrichment joins with other client metrics. Join with `dispatcharr_stream_metadata` to get channel name.

**Example:**
```
dispatcharr_client_info{client_id="client_1735492847123_4567",channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0",ip_address="192.168.1.100",user_agent="VLC/3.0.16 LibVLC/3.0.16",worker_id="worker_1"} 1
```

### `dispatcharr_client_connection_duration_seconds`
**Type:** gauge  
**Value:** Duration in seconds since client connected  
**Labels:**
- `client_id` - Unique client connection ID
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** How long this client has been connected to the stream.

**Example:**
```
dispatcharr_client_connection_duration_seconds{client_id="client_1735492847123_4567",channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 3847
```

### `dispatcharr_client_bytes_sent`
**Type:** counter  
**Value:** Total bytes sent to client  
**Labels:**
- `client_id` - Unique client connection ID
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Cumulative bytes transferred to this client connection.

**Example:**
```
dispatcharr_client_bytes_sent{client_id="client_1735492847123_4567",channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 524288000
```

### `dispatcharr_client_avg_transfer_rate_bps`
**Type:** gauge  
**Value:** Average transfer rate in bits per second  
**Labels:**
- `client_id` - Unique client connection ID
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Average data transfer rate to this client over the connection lifetime. Use Grafana's "bits/sec" unit for automatic formatting.

**Example:**
```
dispatcharr_client_avg_transfer_rate_bps{client_id="client_1735492847123_4567",channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 41604000
```

### `dispatcharr_client_current_transfer_rate_bps`
**Type:** gauge  
**Value:** Current transfer rate in bits per second  
**Labels:**
- `client_id` - Unique client connection ID
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Current/recent data transfer rate to this client. Use Grafana's "bits/sec" unit for automatic formatting.

**Example:**
```
dispatcharr_client_current_transfer_rate_bps{client_id="client_1735492847123_4567",channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 43201600
```

---

## Profile Metrics

*Optional metrics - enabled by default via `include_m3u_stats` setting*

### `dispatcharr_profile_connections`
**Type:** gauge  
**Value:** Current connection count  
**Labels:**
- `profile_id` - Profile database ID
- `profile_name` - Profile name
- `account_name` - M3U account name

**Description:** Current number of connections for this M3U profile.

**Example:**
```
dispatcharr_profile_connections{profile_id="3",profile_name="Default",account_name="Provider A"} 5
```

### `dispatcharr_profile_max_connections`
**Type:** gauge  
**Value:** Maximum allowed connections  
**Labels:**
- `profile_id` - Profile database ID
- `profile_name` - Profile name
- `account_name` - M3U account name

**Description:** Maximum allowed connections for this M3U profile (0 = unlimited).

**Example:**
```
dispatcharr_profile_max_connections{profile_id="3",profile_name="Default",account_name="Provider A"} 10
```

### `dispatcharr_profile_connection_usage`
**Type:** gauge  
**Value:** Usage ratio (0.0 to 1.0)  
**Labels:**
- `profile_id` - Profile database ID
- `profile_name` - Profile name
- `account_name` - M3U account name

**Description:** Connection usage ratio (current/max). Only present if max_connections > 0.

**Example:**
```
dispatcharr_profile_connection_usage{profile_id="3",profile_name="Default",account_name="Provider A"} 0.5
```

### `dispatcharr_stream_profile_connections`
**Type:** gauge  
**Value:** Current connection count  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Current connections for the M3U profile used by this specific stream.

**Example:**
```
dispatcharr_stream_profile_connections{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 0
```

### `dispatcharr_stream_profile_max_connections`
**Type:** gauge  
**Value:** Maximum allowed connections  
**Labels:**
- `channel_uuid` - Channel UUID
- `channel_number` - Channel number

**Description:** Maximum allowed connections for the M3U profile used by this stream.

**Example:**
```
dispatcharr_stream_profile_max_connections{channel_uuid="12572661-bc4b-4937-8501-665c8a4ca1e1",channel_number="1001.0"} 0
```

---

## VOD Metrics

*Optional metrics - disabled by default via `include_vod_stats` setting*

### `dispatcharr_vod_sessions`
**Type:** gauge  
**Value:** Session count  
**Labels:** None

**Description:** Total number of active VOD (Video on Demand) sessions.

**Example:**
```
dispatcharr_vod_sessions 3
```

### `dispatcharr_vod_active_streams`
**Type:** gauge  
**Value:** Active stream count  
**Labels:** None

**Description:** Total number of active VOD streams.

**Example:**
```
dispatcharr_vod_active_streams 3
```

---

## Legacy Metrics

*Deprecated metrics - disabled by default via `include_legacy_metrics` setting*

**Warning:** These metrics are from v1.1.0 and earlier. They are NOT recommended as they create new time series whenever any value changes. Use the new layered metrics instead.

### `dispatcharr_stream_info`
**Type:** gauge  
**Value:** Always 1  
**Labels:** ALL stream information as labels (values and metadata mixed)

**Description:** Legacy format with all stream statistics as labels. Creates high cardinality and new series on every value change.

**Migration:** Use the new layered metrics:
- Use `dispatcharr_stream_metadata` for static metadata
- Use separate value metrics (`dispatcharr_stream_fps`, `dispatcharr_stream_uptime_seconds`, etc.) for dynamic values
- Join metrics using `channel_uuid` and `channel_number`

### `dispatcharr_m3u_account_info`
**Type:** gauge  
**Value:** Always 1  
**Labels:** Account information with `stream_count` as a label

**Description:** Legacy format with stream count as a label.

**Migration:** Use `dispatcharr_m3u_account_stream_count` for the stream count as a proper gauge value.

### `dispatcharr_epg_source_info`
**Type:** gauge  
**Value:** Always 1  
**Labels:** EPG source information with `priority` as a label

**Description:** Legacy format with priority as a label.

**Migration:** Use `dispatcharr_epg_source_priority` for the priority as a proper gauge value.

---

## Common PromQL Query Patterns

### Basic Queries
```promql
# All active streams
dispatcharr_active_streams

# All active clients
dispatcharr_active_clients

# FPS for specific channel
dispatcharr_stream_fps{channel_uuid="..."}

# Detect fallback (backup stream active)
dispatcharr_stream_index > 0

# Sort channels by number
sort(dispatcharr_stream_channel_number)

# Client connection durations
dispatcharr_client_connection_duration_seconds

# Clients connected for over 1 hour
dispatcharr_client_connection_duration_seconds > 3600
```

### Client Queries
```promql
# Total bytes sent to all clients
sum(dispatcharr_client_bytes_sent_total)

# Total bytes sent per channel
sum by (channel_uuid, channel_number) (dispatcharr_client_bytes_sent_total)

# Average transfer rate across all clients (in bps)
avg(dispatcharr_client_avg_transfer_rate_bps)

# Average transfer rate in Mbps for display
avg(dispatcharr_client_avg_transfer_rate_bps) / 1000000

# Client connection duration with IP and user agent
dispatcharr_client_connection_duration_seconds
  * on(client_id, channel_uuid, channel_number) group_left(ip_address, user_agent)
  dispatcharr_client_info

# Client info with channel name (double join)
dispatcharr_client_info
  * on(channel_uuid, channel_number) group_left(channel_name, provider)
  dispatcharr_stream_metadata
```

### Enriched Queries (with joins)
```promql
# FPS with provider information
dispatcharr_stream_fps
  * on(channel_uuid, channel_number) group_left(provider, stream_name)
  dispatcharr_stream_metadata

# Total transfer with full metadata
dispatcharr_stream_transfer_bytes_total
  * on(channel_uuid, channel_number) group_left(logo_url, resolution, video_codec)
  dispatcharr_stream_metadata

# Stream uptime with index
dispatcharr_stream_uptime_seconds_total
  + on(channel_uuid, channel_number)
  dispatcharr_stream_index
```

### Alerts
```promql
# Alert on stream fallback
dispatcharr_stream_index > 0

# Alert on high profile usage
dispatcharr_profile_connection_usage > 0.9

# Alert on M3U account errors
dispatcharr_m3u_account_status{status="error"} > 0
```
