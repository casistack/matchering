#!/usr/bin/env python3
"""
Celery worker startup script for Enhanced Matchering API.

This script helps start Celery workers and beat scheduler with proper configuration.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def start_worker(queues=None, concurrency=None, loglevel="info"):
    """Start Celery worker process."""
    cmd = ["celery", "-A", "app.core.celery_app", "worker"]
    
    if queues:
        cmd.extend(["--queues", ",".join(queues)])
    
    if concurrency:
        cmd.extend(["--concurrency", str(concurrency)])
    
    cmd.extend(["--loglevel", loglevel])
    
    print(f"Starting Celery worker: {' '.join(cmd)}")
    return subprocess.run(cmd)


def start_beat(loglevel="info"):
    """Start Celery beat scheduler."""
    cmd = ["celery", "-A", "app.core.celery_app", "beat", "--loglevel", loglevel]
    
    print(f"Starting Celery beat: {' '.join(cmd)}")
    return subprocess.run(cmd)


def start_flower(port=5555):
    """Start Flower monitoring tool."""
    cmd = ["celery", "-A", "app.core.celery_app", "flower", "--port", str(port)]
    
    print(f"Starting Flower monitoring: {' '.join(cmd)}")
    return subprocess.run(cmd)


def check_redis():
    """Check if Redis is available."""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        return True
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="Start Enhanced Matchering Celery workers")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Worker command
    worker_parser = subparsers.add_parser("worker", help="Start Celery worker")
    worker_parser.add_argument(
        "--queues", 
        nargs="+", 
        choices=["matchering_default", "audio_processing", "audio_analysis", "file_operations"],
        help="Queues to process (default: all)"
    )
    worker_parser.add_argument(
        "--concurrency", 
        type=int, 
        default=None,
        help="Number of concurrent worker processes"
    )
    worker_parser.add_argument(
        "--loglevel", 
        choices=["debug", "info", "warning", "error"], 
        default="info",
        help="Log level"
    )
    
    # Beat command
    beat_parser = subparsers.add_parser("beat", help="Start Celery beat scheduler")
    beat_parser.add_argument(
        "--loglevel", 
        choices=["debug", "info", "warning", "error"], 
        default="info",
        help="Log level"
    )
    
    # Flower command
    flower_parser = subparsers.add_parser("flower", help="Start Flower monitoring")
    flower_parser.add_argument(
        "--port", 
        type=int, 
        default=5555,
        help="Port for Flower web interface"
    )
    
    # Multi command (start worker + beat)
    multi_parser = subparsers.add_parser("multi", help="Start worker and beat together")
    multi_parser.add_argument(
        "--concurrency", 
        type=int, 
        default=2,
        help="Number of concurrent worker processes"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Check Redis availability
    if not check_redis():
        print("⚠️  Warning: Redis is not available at localhost:6379")
        print("   Please start Redis before running Celery workers:")
        print("   redis-server")
        print()
        
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return 1
    else:
        print("✅ Redis is available")
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    if args.command == "worker":
        return start_worker(
            queues=args.queues,
            concurrency=args.concurrency,
            loglevel=args.loglevel
        ).returncode
    
    elif args.command == "beat":
        return start_beat(loglevel=args.loglevel).returncode
    
    elif args.command == "flower":
        return start_flower(port=args.port).returncode
    
    elif args.command == "multi":
        print("Starting multi-process setup (worker + beat)...")
        print("Use Ctrl+C to stop all processes")
        
        # Start worker in background
        worker_cmd = [
            "celery", "-A", "app.core.celery_app", "worker",
            "--concurrency", str(args.concurrency),
            "--loglevel", "info"
        ]
        
        # Start beat in background  
        beat_cmd = [
            "celery", "-A", "app.core.celery_app", "beat",
            "--loglevel", "info"
        ]
        
        try:
            worker_proc = subprocess.Popen(worker_cmd)
            beat_proc = subprocess.Popen(beat_cmd)
            
            print(f"Worker started with PID: {worker_proc.pid}")
            print(f"Beat started with PID: {beat_proc.pid}")
            print("Both processes running. Press Ctrl+C to stop...")
            
            # Wait for both processes
            worker_proc.wait()
            beat_proc.wait()
            
        except KeyboardInterrupt:
            print("\nStopping processes...")
            worker_proc.terminate()
            beat_proc.terminate()
            
            worker_proc.wait()
            beat_proc.wait()
            
            print("All processes stopped")
            return 0
    
    return 0


if __name__ == "__main__":
    exit(main())