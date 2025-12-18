"""
Dispatcharr Prometheus Exporter Plugin

Exposes Dispatcharr metrics in Prometheus format for monitoring:
- Active streams and connections
- M3U account statistics
- Channel statistics
- Profile connection usage
- VOD sessions and streams

Runs a lightweight gevent WSGI server on a configurable port to serve
Prometheus metrics independently of Dispatcharr's main web server.
"""

import logging
import threading
import time
from typing import Dict, Any
from core.utils import RedisClient
from apps.proxy.ts_proxy.constants import ChannelMetadataField

logger = logging.getLogger(__name__)

# Plugin configuration - update all settings here
PLUGIN_CONFIG = {
    "version": "-dev-43b4885f-20251218115631",
    "name": "Dispatcharr Exporter",
    "author": "SethWV",
    "description": "Expose Dispatcharr metrics in Prometheus exporter-compatible format for monitoring. Configuration changes require a restart of the metrics server. https://github.com/sethwv/dispatcharr-exporter/releases/",
    "default_port": 9192,
    "default_host": "0.0.0.0",
    "auto_start_default": False,
}

# Global server instance
_metrics_server = None
_auto_start_attempted = False  # Track if auto-start has been attempted in this process


class PrometheusMetricsCollector:
    """Collects and formats metrics from Dispatcharr in Prometheus exposition format"""

    def __init__(self):
        self.redis_client = None  # Lazy-load Redis when needed

    def collect_metrics(self, settings: dict = None) -> str:
        """Collect all metrics and return in Prometheus text format"""
        # Get Redis client now, when we actually need it
        if self.redis_client is None:
            try:
                self.redis_client = RedisClient.get_client()
            except Exception as e:
                logger.warning(f"Could not connect to Redis: {e}")
        
        metrics = []
        settings = settings or {}
        
        # Get Dispatcharr version
        dispatcharr_version = "unknown"
        dispatcharr_timestamp = None
        try:
            # Try importing version module (add /app to path if needed)
            import sys
            if '/app' not in sys.path:
                sys.path.insert(0, '/app')
            import version
            dispatcharr_version = getattr(version, '__version__', 'unknown')
            dispatcharr_timestamp = getattr(version, '__timestamp__', None)
        except Exception:
            try:
                # Try reading from file directly
                with open('/app/version.py', 'r') as f:
                    content = f.read()
                    import re
                    version_match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", content)
                    if version_match:
                        dispatcharr_version = version_match.group(1)
                    timestamp_match = re.search(r"__timestamp__\s*=\s*['\"]([^'\"]+)['\"]", content)
                    if timestamp_match:
                        dispatcharr_timestamp = timestamp_match.group(1)
            except Exception:
                pass
        
        # Format version with timestamp if available (dev builds)
        full_version = dispatcharr_version
        if dispatcharr_timestamp:
            full_version = f"v{dispatcharr_version}-{dispatcharr_timestamp}"
        
        # Add metadata
        metrics.append("# HELP dispatcharr_info Dispatcharr version and instance information")
        metrics.append("# TYPE dispatcharr_info gauge")
        metrics.append(f'dispatcharr_info{{version="{full_version}"}} 1')
        metrics.append("")

        # M3U Account metrics (optional, enabled by default)
        if not settings or settings.get('include_m3u_stats', True):
            metrics.extend(self._collect_m3u_account_metrics(settings))
        
        # EPG Source metrics (optional, disabled by default)
        if settings and settings.get('include_epg_stats', False):
            metrics.extend(self._collect_epg_metrics(settings))
        
        # Channel metrics
        metrics.extend(self._collect_channel_metrics())
        
        # Profile connection metrics (part of M3U stats)
        if not settings or settings.get('include_m3u_stats', True):
            metrics.extend(self._collect_profile_metrics())
        
        # Stream metrics with detailed info
        metrics.extend(self._collect_stream_metrics())
        
        # VOD metrics (optional, disabled by default)
        if settings and settings.get('include_vod_stats', False):
            metrics.extend(self._collect_vod_metrics())

        return "\n".join(metrics)
    
    def _collect_m3u_account_metrics(self, settings: dict = None) -> list:
        """Collect M3U account statistics"""
        from apps.m3u.models import M3UAccount
        
        metrics = []
        metrics.append("# HELP dispatcharr_m3u_accounts Total number of M3U accounts")
        metrics.append("# TYPE dispatcharr_m3u_accounts gauge")
        
        include_urls = settings and settings.get('include_source_urls', False)
        
        try:
            # Filter out the default "custom" account
            all_accounts = M3UAccount.objects.exclude(name__iexact="custom")
            total_accounts = all_accounts.count()
            active_accounts = all_accounts.filter(is_active=True).count()
            
            metrics.append(f"dispatcharr_m3u_accounts{{status=\"total\"}} {total_accounts}")
            metrics.append(f"dispatcharr_m3u_accounts{{status=\"active\"}} {active_accounts}")
            
            # Account status breakdown (excluding custom)
            metrics.append("# HELP dispatcharr_m3u_account_status M3U account status breakdown")
            metrics.append("# TYPE dispatcharr_m3u_account_status gauge")
            
            for status_choice in M3UAccount.Status.choices:
                status_value = status_choice[0]
                count = all_accounts.filter(status=status_value).count()
                metrics.append(f'dispatcharr_m3u_account_status{{status="{status_value}"}} {count}')
            
            # Individual account metrics
            metrics.append("# HELP dispatcharr_m3u_account_info Information about each M3U account")
            metrics.append("# TYPE dispatcharr_m3u_account_info gauge")
            
            for account in all_accounts:
                account_name = account.name.replace('"', '\\"').replace('\\', '\\\\')
                account_type = account.account_type or 'unknown'
                status = account.status
                is_active = str(account.is_active).lower()
                
                # Count streams from this account
                stream_count = account.streams.count() if hasattr(account, 'streams') else 0
                
                # Build labels
                labels = [
                    f'account_id="{account.id}"',
                    f'account_name="{account_name}"',
                    f'account_type="{account_type}"',
                    f'status="{status}"',
                    f'is_active="{is_active}"',
                    f'stream_count="{stream_count}"'
                ]
                
                # Add username for XC-type accounts
                if account_type == 'XC' and hasattr(account, 'username') and account.username:
                    username = account.username.replace('"', '\\"').replace('\\', '\\\\')
                    labels.append(f'username="{username}"')
                
                # Optionally add server URL
                if include_urls and account.server_url:
                    server_url = account.server_url.replace('"', '\\"').replace('\\', '\\\\')
                    labels.append(f'server_url="{server_url}"')
                
                metrics.append(f'dispatcharr_m3u_account_info{{{','.join(labels)}}} 1')
            
        except Exception as e:
            logger.error(f"Error collecting M3U account metrics: {e}")
        
        metrics.append("")
        return metrics

    def _collect_channel_metrics(self) -> list:
        """Collect channel statistics"""
        from apps.channels.models import Channel, ChannelGroup
        
        metrics = []
        metrics.append("# HELP dispatcharr_channels Total number of channels")
        metrics.append("# TYPE dispatcharr_channels gauge")
        
        try:
            total_channels = Channel.objects.count()
            
            metrics.append(f"dispatcharr_channels{{status=\"total\"}} {total_channels}")
            
            # Channel groups
            metrics.append("# HELP dispatcharr_channel_groups Total number of channel groups")
            metrics.append("# TYPE dispatcharr_channel_groups gauge")
            channel_groups = ChannelGroup.objects.count()
            metrics.append(f"dispatcharr_channel_groups {channel_groups}")
            
            # Active viewers per channel (from Redis)
            # metrics.append("# HELP dispatcharr_channel_viewers Current viewers per channel")
            # metrics.append("# TYPE dispatcharr_channel_viewers gauge")
            
            if self.redis_client:
                for channel in Channel.objects.all():
                    try:
                        viewers = int(self.redis_client.get(f"channel:{channel.uuid}:viewers") or 0)
                        if viewers > 0:
                            channel_name = channel.name.replace('"', '\\"')
                            metrics.append(f'dispatcharr_channel_viewers{{channel_id="{channel.uuid}",channel_name="{channel_name}"}} {viewers}')
                    except Exception as e:
                        logger.debug(f"Error getting viewers for channel {channel.uuid}: {e}")
            
        except Exception as e:
            logger.error(f"Error collecting channel metrics: {e}")
        
        metrics.append("")
        return metrics

    def _collect_profile_metrics(self) -> list:
        """Collect M3U profile connection statistics"""
        from apps.m3u.models import M3UAccountProfile
        
        metrics = []
        profile_data = []
        
        try:
            if self.redis_client:
                for profile in M3UAccountProfile.objects.filter(is_active=True):
                    try:
                        # Skip 'custom' account
                        if profile.m3u_account.name.lower() == 'custom':
                            continue
                        
                        current_connections = int(self.redis_client.get(f"profile_connections:{profile.id}") or 0)
                        max_connections = profile.max_streams
                        
                        profile_name = profile.name.replace('"', '\\"')
                        account_name = profile.m3u_account.name.replace('"', '\\"')
                        
                        profile_data.append(f'dispatcharr_profile_connections{{profile_id="{profile.id}",profile_name="{profile_name}",account_name="{account_name}"}} {current_connections}')
                        profile_data.append(f'dispatcharr_profile_max_connections{{profile_id="{profile.id}",profile_name="{profile_name}",account_name="{account_name}"}} {max_connections}')
                        
                        # Calculate usage ratio (0.0 to 1.0, or 0 if unlimited)
                        if max_connections > 0:
                            usage = current_connections / max_connections
                            profile_data.append(f'dispatcharr_profile_connection_usage{{profile_id="{profile.id}",profile_name="{profile_name}",account_name="{account_name}"}} {usage:.4f}')
                        
                    except Exception as e:
                        logger.debug(f"Error getting connections for profile {profile.id}: {e}")
        except Exception as e:
            logger.error(f"Error collecting profile metrics: {e}")
        
        # Only add headers and data if we have profiles to report
        if profile_data:
            metrics.append("# HELP dispatcharr_profile_connections Current connections per M3U profile")
            metrics.append("# TYPE dispatcharr_profile_connections gauge")
            metrics.append("# HELP dispatcharr_profile_max_connections Maximum allowed connections per M3U profile")
            metrics.append("# TYPE dispatcharr_profile_max_connections gauge")
            metrics.append("# HELP dispatcharr_profile_connection_usage Connection usage ratio per M3U profile")
            metrics.append("# TYPE dispatcharr_profile_connection_usage gauge")
            metrics.extend(profile_data)
        
        metrics.append("")
        return metrics

    def _collect_stream_metrics(self) -> list:
        """Collect active stream statistics from Redis"""
        from apps.channels.models import Channel, Stream
        from apps.m3u.models import M3UAccount, M3UAccountProfile
        
        metrics = []
        metrics.append("# HELP dispatcharr_active_streams Total number of active streams")
        metrics.append("# TYPE dispatcharr_active_streams gauge")
        metrics.append("# HELP dispatcharr_stream_info Detailed information about active streams")
        metrics.append("# TYPE dispatcharr_stream_info gauge")
        
        try:
            if self.redis_client:
                # Count active channel streams and collect detailed info
                active_streams = 0
                stream_details = []
                pattern = "channel_stream:*"
                
                try:
                    for key in self.redis_client.scan_iter(match=pattern):
                        active_streams += 1
                        
                        # Extract channel ID from key (format: "channel_stream:channel_id")
                        try:
                            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                            channel_id = key_str.split(':', 1)[1]
                            
                            # Get stream ID from Redis
                            stream_id = self.redis_client.get(key)
                            if stream_id:
                                stream_id = int(stream_id.decode('utf-8') if isinstance(stream_id, bytes) else stream_id)
                                
                                # Get channel details
                                try:
                                    channel = Channel.objects.select_related('logo').get(id=int(channel_id))
                                    channel_uuid = str(channel.uuid)
                                    channel_name = channel.name.replace('"', '\\"').replace('\\', '\\\\')
                                    channel_number = getattr(channel, 'channel_number', 'N/A')
                                    
                                    # Get logo URL
                                    logo_url = ""
                                    if hasattr(channel, 'logo') and channel.logo:
                                        try:
                                            logo_url = channel.logo.url if hasattr(channel.logo, 'url') else str(channel.logo)
                                        except Exception:
                                            logo_url = ""
                                    logo_url = logo_url.replace('"', '\\"').replace('\\', '\\\\')
                                    
                                    # Get viewer count
                                    viewers = int(self.redis_client.get(f"channel:{channel_uuid}:viewers") or 0)
                                    
                                    # Get detailed stream stats from Redis metadata (uses UUID, not ID!)
                                    metadata_key = f"ts_proxy:channel:{channel_uuid}:metadata"
                                    metadata = self.redis_client.hgetall(metadata_key) or {}
                                    
                                    def get_metadata(field, default="0"):
                                        val = metadata.get(field.encode('utf-8') if isinstance(field, str) else field, b'0')
                                        return val.decode('utf-8') if isinstance(val, bytes) else default
                                    
                                    # Calculate uptime
                                    init_time = float(get_metadata(ChannelMetadataField.INIT_TIME, '0'))
                                    uptime_seconds = int(time.time() - init_time) if init_time > 0 else 0
                                    
                                    # Get stream profile name (lookup from database)
                                    stream_profile_id = get_metadata(ChannelMetadataField.STREAM_PROFILE, '0')
                                    stream_profile_name = 'Unknown'
                                    if stream_profile_id and stream_profile_id != '0':
                                        try:
                                            from core.models import StreamProfile
                                            profile = StreamProfile.objects.get(id=int(stream_profile_id))
                                            stream_profile_name = profile.name.replace('"', '\\"').replace('\\', '\\\\')
                                        except Exception:
                                            stream_profile_name = f'Profile-{stream_profile_id}'
                                    
                                    # Get video stats
                                    video_codec = get_metadata(ChannelMetadataField.VIDEO_CODEC, 'unknown')
                                    resolution = get_metadata(ChannelMetadataField.RESOLUTION, 'unknown')
                                    source_fps = get_metadata(ChannelMetadataField.SOURCE_FPS, '0')
                                    video_bitrate = get_metadata(ChannelMetadataField.VIDEO_BITRATE, '0')
                                    ffmpeg_output_bitrate = get_metadata(ChannelMetadataField.FFMPEG_OUTPUT_BITRATE, '0')
                                    
                                    # Get total transfer
                                    total_bytes = int(get_metadata(ChannelMetadataField.TOTAL_BYTES, '0'))
                                    total_mb = round(total_bytes / 1024 / 1024, 2)
                                    
                                    # Calculate average bitrate
                                    avg_bitrate_kbps = round((total_bytes * 8 / 1024 / uptime_seconds), 2) if uptime_seconds > 0 else 0
                                    
                                    # Get client count from Redis (also uses UUID)
                                    client_set_key = f"ts_proxy:channel:{channel_uuid}:clients"
                                    active_clients = self.redis_client.scard(client_set_key) or 0
                                    
                                    # Get state
                                    state = get_metadata(ChannelMetadataField.STATE, 'unknown')
                                    
                                    # Get stream details
                                    try:
                                        stream = Stream.objects.select_related('m3u_account').get(id=stream_id)
                                        stream_name = stream.name.replace('"', '\\"').replace('\\', '\\\\')
                                        provider = stream.m3u_account.name.replace('"', '\\"').replace('\\', '\\\\') if stream.m3u_account else "Unknown"
                                        stream_type = stream.m3u_account.account_type if stream.m3u_account else "Unknown"
                                        
                                        # Get stream index from ChannelStream through table
                                        stream_index = 0
                                        try:
                                            from apps.channels.models import ChannelStream
                                            channel_stream = ChannelStream.objects.get(channel_id=channel.id, stream_id=stream_id)
                                            stream_index = channel_stream.order
                                        except Exception:
                                            pass
                                        
                                        # Get profile information from the stream's M3U account
                                        profile_id = None
                                        profile_name = "Unknown"
                                        profile_connections = 0
                                        profile_max = 0
                                        
                                        # Get the actual M3U profile ID from channel metadata (already fetched above)
                                        m3u_profile_id = get_metadata(ChannelMetadataField.M3U_PROFILE, None)
                                        if m3u_profile_id and m3u_profile_id != '0':
                                            try:
                                                profile_id = int(m3u_profile_id)
                                                active_profile = M3UAccountProfile.objects.get(id=profile_id)
                                                profile_name = active_profile.name.replace('"', '\\"').replace('\\', '\\\\')
                                                profile_connections = int(self.redis_client.get(f"profile_connections:{profile_id}") or 0)
                                                profile_max = active_profile.max_streams
                                            except Exception as e:
                                                logger.debug(f"Error getting M3U profile {profile_id}: {e}")
                                        
                                        # Build metric labels
                                        labels = [
                                            f'channel_uuid="{channel_uuid}"',
                                            f'channel_name="{channel_name}"',
                                            f'channel_number="{channel_number}"',
                                            f'logo_url="{logo_url}"',
                                            f'stream_id="{stream_id}"',
                                            f'stream_index="{stream_index}"',
                                            f'stream_name="{stream_name}"',
                                            f'provider="{provider}"',
                                            f'provider_type="{stream_type}"',
                                            f'profile_id="{profile_id if profile_id else "none"}"',
                                            f'profile_name="{profile_name}"',
                                            f'profile_connections="{profile_connections}"',
                                            f'profile_max_connections="{profile_max}"',
                                        ]
                                        
                                        # Only add viewers if > 0
                                        if viewers > 0:
                                            labels.append(f'viewers="{viewers}"')
                                        
                                        # Add stream stats
                                        labels.extend([
                                            f'stream_profile="{stream_profile_name}"',
                                            f'video_codec="{video_codec}"',
                                            f'resolution="{resolution}"',
                                            f'fps="{source_fps}"',
                                            f'video_bitrate_kbps="{video_bitrate}"',
                                            f'transcode_bitrate_kbps="{ffmpeg_output_bitrate}"',
                                            f'avg_bitrate_kbps="{avg_bitrate_kbps}"',
                                            f'total_transfer_mb="{total_mb}"',
                                            f'uptime_seconds="{uptime_seconds}"',
                                            f'active_clients="{active_clients}"',
                                            f'state="{state}"'
                                        ])
                                        
                                        # Build metric with rich labels including stream stats
                                        stream_details.append(
                                            f'dispatcharr_stream_info{{{",".join(labels)}}} 1'
                                        )
                                        
                                    except Stream.DoesNotExist:
                                        logger.debug(f"Stream {stream_id} not found in database")
                                    
                                except Channel.DoesNotExist:
                                    logger.debug(f"Channel {channel_id} not found in database")
                                    
                        except Exception as e:
                            logger.debug(f"Error processing stream key {key}: {e}")
                            
                except Exception as e:
                    logger.debug(f"Error scanning stream keys: {e}")
                
                # Add total count
                metrics.append(f"dispatcharr_active_streams {active_streams}")
                
                # Add detailed stream info
                for detail in stream_details:
                    metrics.append(detail)
                    
        except Exception as e:
            logger.error(f"Error collecting stream metrics: {e}")
        
        metrics.append("")
        return metrics
    
    def _collect_epg_metrics(self, settings: dict = None) -> list:
        """Collect EPG source statistics"""
        from apps.epg.models import EPGSource
        
        metrics = []
        include_urls = settings and settings.get('include_source_urls', False)
        
        try:
            # Total EPG sources
            total_sources = EPGSource.objects.count()
            active_sources = EPGSource.objects.filter(is_active=True).count()
            
            metrics.append("# HELP dispatcharr_epg_sources Total number of EPG sources")
            metrics.append("# TYPE dispatcharr_epg_sources gauge")
            metrics.append(f'dispatcharr_epg_sources{{status="total"}} {total_sources}')
            metrics.append(f'dispatcharr_epg_sources{{status="active"}} {active_sources}')
            
            # EPG source status breakdown
            metrics.append("# HELP dispatcharr_epg_source_status EPG source status breakdown")
            metrics.append("# TYPE dispatcharr_epg_source_status gauge")
            
            for status_choice in EPGSource.STATUS_CHOICES:
                status_value = status_choice[0]
                count = EPGSource.objects.filter(status=status_value).count()
                metrics.append(f'dispatcharr_epg_source_status{{status="{status_value}"}} {count}')
            
            # Individual EPG source info
            metrics.append("# HELP dispatcharr_epg_source_info Information about each EPG source")
            metrics.append("# TYPE dispatcharr_epg_source_info gauge")
            
            for source in EPGSource.objects.all():
                source_name = source.name.replace('"', '\\"').replace('\\', '\\\\')
                source_type = source.source_type or 'unknown'
                status = source.status
                is_active = str(source.is_active).lower()
                priority = source.priority
                
                # Build labels
                labels = [
                    f'source_id="{source.id}"',
                    f'source_name="{source_name}"',
                    f'source_type="{source_type}"',
                    f'status="{status}"',
                    f'is_active="{is_active}"',
                    f'priority="{priority}"'
                ]
                
                # Optionally add source URL
                if include_urls and source.url:
                    source_url = source.url.replace('"', '\\"').replace('\\', '\\\\')
                    labels.append(f'url="{source_url}"')
                
                metrics.append(f'dispatcharr_epg_source_info{{{','.join(labels)}}} 1')
        
        except Exception as e:
            logger.error(f"Error collecting EPG metrics: {e}")
        
        metrics.append("")
        return metrics

    def _collect_vod_metrics(self) -> list:
        """Collect VOD (Video on Demand) statistics"""
        metrics = []
        metrics.append("# HELP dispatcharr_vod_sessions Total number of VOD sessions")
        metrics.append("# TYPE dispatcharr_vod_sessions gauge")
        metrics.append("# HELP dispatcharr_vod_active_streams Total number of active VOD streams")
        metrics.append("# TYPE dispatcharr_vod_active_streams gauge")
        
        try:
            if self.redis_client:
                # Count VOD sessions
                vod_sessions = 0
                active_vod_streams = 0
                
                pattern = "vod_session:*"
                try:
                    for key in self.redis_client.scan_iter(match=pattern):
                        vod_sessions += 1
                        # Try to get active streams count from session data
                        try:
                            session_data = self.redis_client.hgetall(key)
                            if session_data:
                                active_streams = int(session_data.get(b'active_streams', 0))
                                active_vod_streams += active_streams
                        except Exception as e:
                            logger.debug(f"Error reading session data for {key}: {e}")
                except Exception as e:
                    logger.debug(f"Error scanning VOD session keys: {e}")
                
                metrics.append(f"dispatcharr_vod_sessions {vod_sessions}")
                metrics.append(f"dispatcharr_vod_active_streams {active_vod_streams}")
        except Exception as e:
            logger.error(f"Error collecting VOD metrics: {e}")
        
        metrics.append("")
        return metrics


class MetricsServer:
    """Lightweight HTTP server to expose Prometheus metrics using gevent"""
    
    def __init__(self, collector, port=None, host=None):
        self.collector = collector
        self.port = port if port is not None else PLUGIN_CONFIG["default_port"]
        self.host = host if host is not None else PLUGIN_CONFIG["default_host"]
        self.server_thread = None
        self.server = None
        self.running = False
        self.settings = {}
        
    def wsgi_app(self, environ, start_response):
        """WSGI application for serving metrics"""
        path = environ.get('PATH_INFO', '/')
        
        if path == '/metrics':
            try:
                metrics_text = self.collector.collect_metrics(settings=self.settings)
                status = '200 OK'
                headers = [('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')]
                start_response(status, headers)
                return [metrics_text.encode('utf-8')]
            except Exception as e:
                logger.error(f"Error generating metrics: {e}", exc_info=True)
                status = '500 Internal Server Error'
                headers = [('Content-Type', 'text/plain')]
                start_response(status, headers)
                return [f"# Error: {str(e)}\n".encode('utf-8')]
        
        elif path == '/health':
            status = '200 OK'
            headers = [('Content-Type', 'text/plain')]
            start_response(status, headers)
            return [b"OK\n"]
        
        else:
            status = '404 Not Found'
            headers = [('Content-Type', 'text/plain')]
            start_response(status, headers)
            return [b"Not Found\n"]
    
    def start(self, settings=None):
        """Start the metrics server in a background thread"""
        global _metrics_server
        
        if self.running:
            logger.warning("Metrics server is already running")
            return False
        
        # Check if another instance is running via Redis
        try:
            from core.utils import RedisClient
            redis_client = RedisClient.get_client()
            running_flag = redis_client.get("prometheus_exporter:server_running") if redis_client else None
            if running_flag == "1" or running_flag == b"1":
                logger.warning("Another metrics server instance is already running (detected via Redis)")
                return False
        except Exception as e:
            logger.debug(f"Could not check Redis for running server: {e}")
        
        # Check if another instance is running in this process
        if _metrics_server and _metrics_server.is_running():
            logger.warning("Another metrics server instance is already running")
            return False
        
        # Check if port is already in use
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host, self.port))
            sock.close()
        except OSError as e:
            logger.error(f"Port {self.port} is already in use: {e}")
            return False
        
        self.settings = settings or {}
        
        try:
            from gevent import pywsgi
            
            def run_server():
                try:
                    logger.info(f"Starting gevent WSGI server on {self.host}:{self.port}")
                    self.server = pywsgi.WSGIServer((self.host, self.port), self.wsgi_app)
                    # Mark as running only after successful bind
                    self.running = True
                    
                    # Set Redis flag so all workers know server is running
                    try:
                        from core.utils import RedisClient
                        redis_client = RedisClient.get_client()
                        if redis_client:
                            redis_client.set("prometheus_exporter:server_running", "1")
                            redis_client.set("prometheus_exporter:server_host", self.host)
                            redis_client.set("prometheus_exporter:server_port", str(self.port))
                    except Exception as e:
                        logger.warning(f"Could not set Redis flag: {e}")
                    
                    logger.info(f"Metrics server started on http://{self.host}:{self.port}/metrics")
                    
                    # Start the server in a separate greenlet so we can monitor for stop signals
                    from gevent import spawn, sleep
                    server_greenlet = spawn(self.server.serve_forever)
                    
                    # Monitor for stop signal via Redis
                    while self.running:
                        try:
                            from core.utils import RedisClient
                            redis_client = RedisClient.get_client()
                            if redis_client:
                                stop_flag = redis_client.get("prometheus_exporter:stop_requested")
                                # If stop requested, shut down
                                if stop_flag == "1" or stop_flag == b"1":
                                    logger.info("Stop signal detected via Redis, shutting down metrics server")
                                    self.running = False
                                    self.server.stop()
                                    break
                        except Exception as e:
                            logger.debug(f"Error checking stop signal: {e}")
                        
                        sleep(1)  # Check every second
                    
                    # Clean up Redis flags and lock file after actually stopping
                    try:
                        from core.utils import RedisClient
                        redis_client = RedisClient.get_client()
                        if redis_client:
                            redis_client.delete("prometheus_exporter:server_running")
                            redis_client.delete("prometheus_exporter:server_host")
                            redis_client.delete("prometheus_exporter:server_port")
                            redis_client.delete("prometheus_exporter:stop_requested")
                    except Exception as e:
                        logger.warning(f"Could not clear Redis flags on shutdown: {e}")
                    
                    # Remove lock file
                    try:
                        import os
                        lock_file = "/tmp/prometheus_exporter_autostart.lock"
                        if os.path.exists(lock_file):
                            os.remove(lock_file)
                            logger.info("Removed auto-start lock file")
                    except Exception as e:
                        logger.debug(f"Could not remove lock file on shutdown: {e}")
                    
                    logger.info("Metrics server stopped and cleaned up")
                    
                except Exception as e:
                    logger.error(f"Error running metrics server: {e}", exc_info=True)
                    self.running = False
            
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
            # Give it a moment to bind and set running=True
            import time
            time.sleep(0.5)
            
            if self.running:
                _metrics_server = self
                return True
            else:
                return False
            
        except ImportError:
            logger.error("gevent is not installed")
            return False
    
    def stop(self):
        """Stop the metrics server"""
        global _metrics_server
        
        if not self.running:
            return False
        
        logger.info("Stopping metrics server...")
        
        if self.server:
            try:
                self.server.stop()
            except Exception as e:
                logger.debug(f"Error stopping server: {e}")
        
        self.running = False
        _metrics_server = None
        
        # Clear Redis flags
        try:
            from core.utils import RedisClient
            redis_client = RedisClient.get_client()
            if redis_client:
                redis_client.delete("prometheus_exporter:server_running")
                redis_client.delete("prometheus_exporter:server_host")
                redis_client.delete("prometheus_exporter:server_port")
        except Exception as e:
            logger.warning(f"Could not clear Redis flags: {e}")
        
        # Clean up lock file
        try:
            import os
            lock_file = "/tmp/prometheus_exporter_autostart.lock"
            if os.path.exists(lock_file):
                os.remove(lock_file)
        except Exception as e:
            logger.debug(f"Error removing lock file: {e}")
        
        return True
    
    def is_running(self):
        """Check if server is running"""
        return self.running and self.server_thread and self.server_thread.is_alive()


class Plugin:
    """Dispatcharr Plugin for Prometheus metrics export using gevent"""
    
    name = PLUGIN_CONFIG["name"]
    description = PLUGIN_CONFIG["description"]
    version = PLUGIN_CONFIG["version"]
    author = PLUGIN_CONFIG["author"]
    
    fields = [
        {
            "id": "auto_start",
            "label": "Auto-Start Metrics Server",
            "type": "boolean",
            "default": PLUGIN_CONFIG["auto_start_default"],
            "help_text": "Automatically start the metrics server when plugin loads (recommended)"
        },
        {
            "id": "port",
            "label": "Metrics Server Port",
            "type": "number",
            "default": PLUGIN_CONFIG["default_port"],
            "help_text": "Port for the metrics HTTP server"
        },
        {
            "id": "host",
            "label": "Metrics Server Host",
            "type": "string",
            "default": PLUGIN_CONFIG["default_host"],
            "help_text": "Host address to bind to (0.0.0.0 for all interfaces, 127.0.0.1 for localhost only)"
        },
        {
            "id": "include_m3u_stats",
            "label": "Include M3U Account Statistics",
            "type": "boolean",
            "default": True,
            "help_text": "Include M3U account and profile metrics in the output"
        },
        {
            "id": "include_epg_stats",
            "label": "Include EPG Source Statistics",
            "type": "boolean",
            "default": False,
            "help_text": "Include EPG source and status metrics in the output"
        },
        {
            "id": "include_vod_stats",
            "label": "Include VOD Statistics",
            "type": "boolean",
            "default": False,
            "help_text": "Include VOD session and stream metrics in the output"
        },
        {
            "id": "include_source_urls",
            "label": "Include Provider/Source Information",
            "type": "boolean",
            "default": False,
            "help_text": "Include server URLs & XC usernames in M3U account and EPG source metrics. Ensure this is DISABLED if sharing output in Discord for troubleshooting."
        }
    ]

    actions = [
        {
            "id": "start_server",
            "label": "Start Metrics Server",
            "description": "Start the HTTP metrics server"
        },
        {
            "id": "stop_server",
            "label": "Stop Metrics Server",
            "description": "Stop the HTTP metrics server"
        },
        {
            "id": "restart_server",
            "label": "Restart Metrics Server",
            "description": "Restart the HTTP metrics server"
        },
        {
            "id": "server_status",
            "label": "Server Status",
            "description": "Check if the metrics server is running and get endpoint URL"
        }
    ]

    def __init__(self):
        self.collector = PrometheusMetricsCollector()
        
        # Don't check Redis here - it may not be ready during startup
        # File-based locking will prevent duplicate auto-start attempts
        
        # Attempt delayed auto-start with file-based lock to prevent multiple workers from racing
        # Only attempt once per process to avoid multiple threads competing
        global _metrics_server, _auto_start_attempted
        
        if _auto_start_attempted:
            logger.debug("Prometheus exporter: Auto-start already attempted in this process, skipping")
            return
        
        logger.debug("Prometheus exporter: Initializing plugin and starting auto-start thread")
        
        def delayed_auto_start():
            import time
            import os
            import fcntl
            
            global _auto_start_attempted
            
            lock_file = "/tmp/prometheus_exporter_autostart.lock"
            max_retries = 5
            retry_delay = 2
            
            logger.debug("Prometheus exporter: Auto-start thread started, attempting to acquire lock")
            
            # Try to acquire lock - only ONE worker across all processes should succeed
            try:
                # Create lock file with open permissions so it can be accessed by all workers
                lock_fd = open(lock_file, 'w')
                try:
                    os.chmod(lock_file, 0o666)  # Make it readable/writable by all
                except OSError:
                    # chmod might fail if we don't own the file, that's okay
                    pass
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                logger.debug("Prometheus exporter: Lock acquired, checking config for auto-start")
                
                # We got the lock - we're the chosen worker for auto-start
                # Check if auto-start was already completed in this Dispatcharr instance
                try:
                    from core.utils import RedisClient
                    redis_client = RedisClient.get_client()
                    if redis_client:
                        # Check if auto-start was already attempted
                        autostart_completed = redis_client.get("prometheus_exporter:autostart_completed")
                        if autostart_completed == "1" or autostart_completed == b"1":
                            logger.debug("Prometheus exporter: Auto-start already completed in this instance, skipping")
                            _auto_start_attempted = True
                            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
                            lock_fd.close()
                            return
                        
                        # Also check if server is already running
                        running_flag = redis_client.get("prometheus_exporter:server_running")
                        if running_flag == "1" or running_flag == b"1":
                            logger.debug("Prometheus exporter: Server already running (detected via Redis), skipping auto-start")
                            _auto_start_attempted = True
                            # Mark auto-start as completed
                            redis_client.set("prometheus_exporter:autostart_completed", "1")
                            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
                            lock_fd.close()
                            return
                except Exception as e:
                    logger.debug(f"Could not check Redis for running server: {e}")
                
                # Capture the INITIAL auto-start setting to lock in behavior at Dispatcharr startup
                # This prevents runtime setting changes from triggering auto-start
                initial_auto_start_enabled = False
                try:
                    from apps.plugins.models import PluginConfig
                    config = PluginConfig.objects.filter(key='prometheus_exporter').first()
                    settings_dict = config.settings if config and config.settings else {}
                    initial_auto_start_enabled = config and config.enabled and settings_dict.get('auto_start', PLUGIN_CONFIG["auto_start_default"])
                    logger.debug(f"Prometheus exporter: Initial auto-start setting captured: enabled={initial_auto_start_enabled}")
                except Exception as e:
                    logger.debug(f"Could not read initial auto-start setting: {e}")
                
                # Mark auto-start as completed immediately to prevent any future attempts
                try:
                    from core.utils import RedisClient
                    redis_client = RedisClient.get_client()
                    if redis_client:
                        redis_client.set("prometheus_exporter:autostart_completed", "1")
                        logger.debug("Prometheus exporter: Marked auto-start as completed for this Dispatcharr instance")
                except Exception as e:
                    logger.debug(f"Could not set auto-start completion flag: {e}")
                
                # If auto-start was not enabled initially, exit now
                if not initial_auto_start_enabled:
                    logger.debug("Prometheus exporter: Auto-start disabled at startup, will not auto-start")
                    _auto_start_attempted = True
                    fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
                    lock_fd.close()
                    return
                
                for attempt in range(max_retries):
                    try:
                        time.sleep(retry_delay * (attempt + 1))
                        
                        from apps.plugins.models import PluginConfig
                        config = PluginConfig.objects.filter(key='prometheus_exporter').first()
                        
                        # Handle case where settings might be None
                        settings_dict = config.settings if config and config.settings else {}
                        
                        logger.debug(f"Prometheus exporter: Attempt {attempt + 1}/{max_retries} - using initial auto_start={initial_auto_start_enabled}")
                        
                        # Only auto-start if it was enabled at startup (using captured initial value)
                        if config and config.enabled and initial_auto_start_enabled:
                            port = int(settings_dict.get('port', PLUGIN_CONFIG["default_port"]))
                            host = settings_dict.get('host', PLUGIN_CONFIG["default_host"])
                            
                            logger.info(f"Auto-start is enabled, attempting to start on {host}:{port}")
                            
                            # Check if port is available before trying to start
                            import socket
                            try:
                                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                                sock.bind((host, port))
                                sock.close()
                            except OSError:
                                # Port already in use - stop retrying
                                logger.info(f"Port {port} already in use, cannot auto-start metrics server")
                                _auto_start_attempted = True
                                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
                                lock_fd.close()
                                return
                            
                            server = MetricsServer(self.collector, port=port, host=host)
                            if server.start(settings=settings_dict):
                                logger.info(f"Auto-start successful on http://{host}:{port}/metrics")
                                _auto_start_attempted = True  # Mark as attempted after successful start
                                # Keep lock held to prevent other workers from trying
                                return
                            else:
                                # Start failed but port check passed - unexpected, stop retrying
                                logger.warning(f"Auto-start failed unexpectedly on attempt {attempt + 1}")
                                _auto_start_attempted = True  # Mark as attempted even on failure
                                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
                                lock_fd.close()
                                return

                    except Exception as e:
                        logger.warning(f"Prometheus exporter: Auto-start attempt {attempt + 1} failed: {e}")
                        # On any exception, continue to next retry unless it's the last one
                        if attempt == max_retries - 1:
                            logger.warning("Prometheus exporter: Auto-start failed after all retries. Use 'Start Metrics Server' button to start manually.")
                            _auto_start_attempted = True
                            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
                            lock_fd.close()
                            return
                        continue  # Try next attempt
                        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
                        lock_fd.close()
                        return
                
                # Release lock if we somehow get here
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
                lock_fd.close()
                
            except BlockingIOError:
                # Another worker already has the lock and is handling auto-start
                logger.debug("Prometheus exporter: Auto-start already being handled by another worker")
            except Exception as e:
                logger.warning(f"Prometheus exporter: Auto-start lock acquisition failed: {e}")
        
        # Start in daemon thread - only the worker that gets the lock will actually start the server
        import threading
        threading.Thread(target=delayed_auto_start, daemon=True, name="prometheus-auto-start").start()

    def run(self, action: str, params: dict, context: dict):
        """Execute plugin actions"""
        global _metrics_server
        
        # Get logger with context
        logger_ctx = context.get("logger", logger)
        settings = context.get("settings", {})
        
        # Check Redis for server state (works across all workers)
        try:
            from core.utils import RedisClient
            redis_client = RedisClient.get_client()
            running_flag = redis_client.get("prometheus_exporter:server_running") if redis_client else None
            server_running_redis = running_flag == "1" or running_flag == b"1"
            if server_running_redis:
                host_val = redis_client.get("prometheus_exporter:server_host")
                port_val = redis_client.get("prometheus_exporter:server_port")
                server_host = (host_val.decode('utf-8') if isinstance(host_val, bytes) else host_val) or PLUGIN_CONFIG["default_host"]
                server_port = (port_val.decode('utf-8') if isinstance(port_val, bytes) else port_val) or str(PLUGIN_CONFIG["default_port"])
            else:
                server_host = None
                server_port = None
        except Exception as e:
            logger_ctx.debug(f"Could not check Redis for server state: {e}")
            server_running_redis = False
            server_host = None
            server_port = None
        
        if action == "start_server":
            # Check if gevent is available
            try:
                import gevent
                from gevent import pywsgi
            except ImportError:
                return {
                    "status": "error",
                    "message": "gevent is not installed (unexpected - it's a Dispatcharr dependency)",
                    "instructions": "If running a custom setup, install: pip install gevent"
                }
            
            try:
                port = int(settings.get("port", PLUGIN_CONFIG["default_port"]))
                host = settings.get("host", PLUGIN_CONFIG["default_host"])
                
                # Check Redis flag first (works across workers)
                if server_running_redis:
                    return {
                        "status": "error",
                        "message": f"Metrics server is already running on http://{server_host}:{server_port}/metrics"
                    }
                
                # Also check local instance
                if _metrics_server and _metrics_server.is_running():
                    return {
                        "status": "error",
                        "message": f"Metrics server is already running on http://{_metrics_server.host}:{_metrics_server.port}/metrics"
                    }
                
                server = MetricsServer(self.collector, port=port, host=host)
                if server.start(settings=settings):
                    return {
                        "status": "success",
                        "message": "Metrics server started successfully",
                        "endpoint": f"http://{host}:{port}/metrics",
                        "health_check": f"http://{host}:{port}/health",
                        "note": "Metrics are generated fresh on each Prometheus scrape request"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to start metrics server. Port may already be in use."
                    }
            except Exception as e:
                logger_ctx.error(f"Error starting metrics server: {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": f"Failed to start server: {str(e)}"
                }

        elif action == "stop_server":
            try:
                stopped_local = False
                
                # Try to stop local instance first
                if _metrics_server and _metrics_server.is_running():
                    if _metrics_server.stop():
                        stopped_local = True
                        return {
                            "status": "success",
                            "message": "Metrics server stopped successfully"
                        }
                
                # Server is in another worker - signal it to stop via Redis
                if redis_client:
                    try:
                        # Set stop request flag
                        redis_client.set("prometheus_exporter:stop_requested", "1")
                        
                        # Wait up to 5 seconds for server to stop
                        import time
                        for i in range(50):  # 50 * 0.1 = 5 seconds
                            running_flag = redis_client.get("prometheus_exporter:server_running")
                            if not running_flag or (running_flag != "1" and running_flag != b"1"):
                                # Server has stopped
                                return {
                                    "status": "success",
                                    "message": "Metrics server stopped successfully"
                                }
                            time.sleep(0.1)
                        
                        # Timeout - server didn't stop in time
                        return {
                            "status": "warning",
                            "message": "Stop signal sent, but server did not confirm shutdown within 5 seconds"
                        }
                    except Exception as redis_error:
                        logger_ctx.error(f"Failed to signal stop via Redis: {redis_error}")
                        return {
                            "status": "error",
                            "message": f"Failed to signal stop: {str(redis_error)}"
                        }
                else:
                    return {
                        "status": "error",
                        "message": "Cannot stop server: No local instance and Redis unavailable"
                    }
                    
            except Exception as e:
                logger_ctx.error(f"Error stopping metrics server: {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": f"Failed to stop server: {str(e)}"
                }

        elif action == "restart_server":
            try:
                # First, stop the server
                stopped_local = False
                
                # Try to stop local instance first
                if _metrics_server and _metrics_server.is_running():
                    if _metrics_server.stop():
                        stopped_local = True
                
                # Always clear Redis flags and signal stop
                if redis_client:
                    try:
                        redis_client.set("prometheus_exporter:stop_requested", "1")
                        
                        # Wait up to 5 seconds for server to stop
                        import time
                        for i in range(50):
                            running_flag = redis_client.get("prometheus_exporter:server_running")
                            if not running_flag or (running_flag != "1" and running_flag != b"1"):
                                break
                            time.sleep(0.1)
                    except Exception as redis_error:
                        logger_ctx.error(f"Failed to signal stop via Redis: {redis_error}")
                        return {
                            "status": "error",
                            "message": f"Failed to stop server: {str(redis_error)}"
                        }
                
                # Small delay to ensure cleanup
                import time
                time.sleep(0.5)
                
                # Clear the stop_requested flag before starting new server
                if redis_client:
                    try:
                        redis_client.delete("prometheus_exporter:stop_requested")
                        logger_ctx.debug("Cleared stop_requested flag before restart")
                    except Exception as e:
                        logger_ctx.warning(f"Failed to clear stop_requested flag: {e}")
                
                # Additional delay to ensure flag is cleared
                time.sleep(0.5)
                
                # Now start the server
                port = int(settings.get('port', PLUGIN_CONFIG["default_port"]))
                host = settings.get('host', PLUGIN_CONFIG["default_host"])
                
                # Check if already running (shouldn't be, but check anyway)
                if redis_client:
                    running_flag = redis_client.get("prometheus_exporter:server_running")
                    if running_flag == "1" or running_flag == b"1":
                        return {
                            "status": "error",
                            "message": "Server is still running after stop attempt"
                        }
                
                # Start new server
                server = MetricsServer(self.collector, port=port, host=host)
                if server.start(settings=settings):
                    return {
                        "status": "success",
                        "message": "Metrics server restarted successfully",
                        "endpoint": f"http://{host}:{port}/metrics",
                        "health_check": f"http://{host}:{port}/health"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Server stopped but failed to restart. Port may be in use."
                    }
                    
            except Exception as e:
                logger_ctx.error(f"Error restarting metrics server: {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": f"Failed to restart server: {str(e)}"
                }

        elif action == "server_status":
            try:
                # Determine endpoint URL
                if server_running_redis and server_host and server_port:
                    endpoint = f"http://{server_host}:{server_port}/metrics"
                elif _metrics_server and _metrics_server.host and _metrics_server.port:
                    endpoint = f"http://{_metrics_server.host}:{_metrics_server.port}/metrics"
                else:
                    # Use default from settings or fallback to config defaults
                    host = settings.get('host', PLUGIN_CONFIG["default_host"]) if settings else PLUGIN_CONFIG["default_host"]
                    port = settings.get('port', PLUGIN_CONFIG["default_port"]) if settings else PLUGIN_CONFIG["default_port"]
                    endpoint = f"http://{host}:{port}/metrics"
                
                # Check both local instance and Redis flag
                if (_metrics_server and _metrics_server.is_running()) or server_running_redis:
                    return {
                        "status": "success",
                        "message": f"Server is running on {endpoint}"
                    }
                else:
                    return {
                        "status": "success",
                        "message": f"Server is not running"
                    }
            except Exception as e:
                logger_ctx.error(f"Error checking server status: {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": f"Failed to check status: {str(e)}"
                }

        return {"status": "error", "message": f"Unknown action: {action}"}

