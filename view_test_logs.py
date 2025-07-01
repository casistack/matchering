#!/usr/bin/env python3
"""
Enterprise Log Viewer for Matchering AI Enhancement Project

This script provides an easy way to view and analyze the comprehensive
logging data generated during testing sessions.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import argparse

def format_timestamp(timestamp_str):
    """Format ISO timestamp for readable display."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%H:%M:%S.%f')[:-3]  # Show milliseconds
    except:
        return timestamp_str

def format_json(obj, indent=2):
    """Format JSON object for readable display."""
    return json.dumps(obj, indent=indent, default=str)

def print_header(title, char="=", width=80):
    """Print a formatted header."""
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(f"{char * width}")

def print_section(title, char="-", width=60):
    """Print a formatted section header."""
    print(f"\n{char * width}")
    print(f"{title}")
    print(f"{char * width}")

def view_log_file(log_file, event_types=None, show_raw=False):
    """View a specific log file with filtering."""
    
    if not log_file.exists():
        print(f"❌ Log file not found: {log_file}")
        return
        
    print_header(f"📊 LOG FILE: {log_file.name}")
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            
        events_shown = 0
        
        for line_num, line in enumerate(lines, 1):
            try:
                log_entry = json.loads(line.strip())
                
                # Filter by event type if specified
                if event_types:
                    event_type = log_entry.get('event_type', 'unknown')
                    if event_type not in event_types:
                        continue
                
                events_shown += 1
                
                # Extract key information
                timestamp = log_entry.get('timestamp', 'unknown')
                event_type = log_entry.get('event_type', 'unknown')
                message = log_entry.get('event', log_entry.get('message', 'No message'))
                request_id = log_entry.get('request_id', 'N/A')
                job_id = log_entry.get('job_id', 'N/A')
                
                print(f"\n🔹 [{format_timestamp(timestamp)}] {event_type.upper()}")
                print(f"   📝 {message}")
                
                if request_id != 'N/A':
                    print(f"   🆔 Request: {request_id[:8]}...")
                if job_id != 'N/A':
                    print(f"   🎵 Job: {job_id[:8]}...")
                    
                # Show specific details based on event type
                if event_type == 'user_action':
                    action = log_entry.get('action', 'unknown')
                    details = log_entry.get('action_details', {})
                    print(f"   🎯 Action: {action}")
                    if 'settings' in details:
                        settings = details['settings']
                        print(f"   ⚙️ Settings: intensity={settings.get('intensity_level', 'N/A')}, "
                              f"eq={settings.get('eq_style', 'N/A')}, "
                              f"lufs={settings.get('target_loudness_lufs', 'N/A')}")
                
                elif event_type == 'ai_prediction':
                    model = log_entry.get('model_used', 'unknown')
                    confidence = log_entry.get('confidence', 0.0)
                    eq_analysis = log_entry.get('eq_analysis', {})
                    
                    print(f"   🤖 Model: {model} (confidence: {confidence:.2f})")
                    print(f"   🎛️ EQ Status: {'❌ FLAT' if eq_analysis.get('eq_curve_is_flat', True) else '✅ ACTIVE'}")
                    
                    if not eq_analysis.get('eq_curve_is_flat', True):
                        print(f"   📊 EQ Range: {eq_analysis.get('eq_curve_min', 0):.1f} to {eq_analysis.get('eq_curve_max', 0):.1f} dB")
                    
                    params = log_entry.get('parameter_analysis', {})
                    if params:
                        print(f"   🎚️ Compression: {params.get('compression_ratio', 'N/A')}")
                        print(f"   🔊 Limiting: {params.get('limiting_threshold', 'N/A')} dB")
                
                elif event_type == 'matchering_config':
                    config = log_entry.get('config_analysis', {})
                    user_settings = log_entry.get('user_settings_applied', {})
                    
                    print(f"   ⚙️ Max Peak: {config.get('loudness_max_peak', 'N/A')} dB")
                    print(f"   📈 Max Amp: {config.get('limiter_max_amplification_db', 'N/A')} dB")
                    print(f"   🎯 User Intensity: {user_settings.get('intensity_level', 'N/A')}")
                    print(f"   📊 Target LUFS: {user_settings.get('target_loudness_lufs', 'N/A')}")
                
                elif event_type == 'performance_metric':
                    metric = log_entry.get('metric_name', 'unknown')
                    value = log_entry.get('value', 0)
                    unit = log_entry.get('unit', '')
                    print(f"   ⚡ {metric}: {value:.2f} {unit}")
                
                elif event_type == 'error_occurred':
                    error = log_entry.get('error', 'Unknown error')
                    error_type = log_entry.get('error_type', 'unknown')
                    print(f"   🚨 Error Type: {error_type}")
                    print(f"   ❌ Error: {error}")
                
                # Show raw JSON if requested
                if show_raw:
                    print(f"   📋 Raw Data:")
                    print(f"      {format_json(log_entry, indent=6)}")
                    
            except json.JSONDecodeError:
                if show_raw:
                    print(f"   📝 Raw log: {line.strip()}")
                continue
                
        print(f"\n📊 Total events shown: {events_shown}")
        
    except Exception as e:
        print(f"❌ Error reading log file: {e}")

def view_latest_test():
    """View the most recent test session logs."""
    logs_dir = Path("backend/logs")
    
    if not logs_dir.exists():
        print("❌ Logs directory not found. Run a test first to generate logs.")
        return
        
    print_header("🔍 LATEST TEST SESSION ANALYSIS")
    
    # Check all log files by modification time
    log_files = {
        "requests": logs_dir / "requests.log",
        "processing": logs_dir / "processing.log", 
        "quality": logs_dir / "quality.log",
        "performance": logs_dir / "performance.log",
        "errors": logs_dir / "errors.log"
    }
    
    # Find the most recent logs
    most_recent = None
    for name, path in log_files.items():
        if path.exists():
            if most_recent is None or path.stat().st_mtime > most_recent.stat().st_mtime:
                most_recent = path
    
    if most_recent is None:
        print("❌ No log files found.")
        return
        
    print(f"📅 Most recent activity: {datetime.fromtimestamp(most_recent.stat().st_mtime)}")
    
    # Show summary from each log type
    for log_name, log_path in log_files.items():
        if log_path.exists():
            print_section(f"📋 {log_name.upper()} LOG")
            view_log_file(log_path)

def analyze_test_quality():
    """Analyze test results for quality issues."""
    
    print_header("🔍 QUALITY ANALYSIS")
    
    logs_dir = Path("backend/logs")
    processing_log = logs_dir / "processing.log"
    
    if not processing_log.exists():
        print("❌ Processing log not found. Run a test first.")
        return
        
    issues_found = []
    eq_curves_analyzed = 0
    flat_eq_curves = 0
    
    try:
        with open(processing_log, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    
                    if entry.get('event_type') == 'ai_prediction':
                        eq_curves_analyzed += 1
                        eq_analysis = entry.get('eq_analysis', {})
                        
                        if eq_analysis.get('eq_curve_is_flat', True):
                            flat_eq_curves += 1
                            issues_found.append({
                                'type': 'EQ_CURVE_FLAT',
                                'severity': 'HIGH',
                                'description': 'AI EQ curve is flat (all zeros) despite user settings',
                                'timestamp': entry.get('timestamp'),
                                'job_id': entry.get('job_id', 'unknown')
                            })
                        
                        # Check for other quality indicators
                        params = entry.get('parameter_analysis', {})
                        if params.get('compression_ratio') == 2.5:  # Default value
                            issues_found.append({
                                'type': 'DEFAULT_COMPRESSION',
                                'severity': 'MEDIUM', 
                                'description': 'Using default compression ratio (may not match user intensity)',
                                'timestamp': entry.get('timestamp'),
                                'job_id': entry.get('job_id', 'unknown')
                            })
                
                except json.JSONDecodeError:
                    continue
                    
    except Exception as e:
        print(f"❌ Error analyzing logs: {e}")
        return
    
    # Report findings
    print(f"📊 EQ Curves Analyzed: {eq_curves_analyzed}")
    print(f"❌ Flat EQ Curves: {flat_eq_curves}")
    
    if issues_found:
        print_section("🚨 ISSUES FOUND")
        for issue in issues_found:
            severity_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(issue['severity'], "⚪")
            print(f"{severity_emoji} {issue['type']} ({issue['severity']})")
            print(f"   📝 {issue['description']}")
            print(f"   🕐 {format_timestamp(issue['timestamp'])}")
            print(f"   🆔 Job: {issue['job_id'][:8]}...")
            print()
    else:
        print("✅ No quality issues detected!")

def main():
    parser = argparse.ArgumentParser(description="View Matchering AI test logs")
    parser.add_argument("--latest", action="store_true", help="Show latest test session")
    parser.add_argument("--quality", action="store_true", help="Analyze quality issues")
    parser.add_argument("--file", type=str, help="View specific log file")
    parser.add_argument("--events", nargs="+", help="Filter by event types")
    parser.add_argument("--raw", action="store_true", help="Show raw JSON data")
    
    args = parser.parse_args()
    
    if args.quality:
        analyze_test_quality()
    elif args.latest:
        view_latest_test()
    elif args.file:
        log_file = Path(args.file)
        view_log_file(log_file, args.events, args.raw)
    else:
        # Default: show latest
        view_latest_test()

if __name__ == "__main__":
    main()