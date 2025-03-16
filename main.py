#!/usr/bin/env python3
"""
Main entry point for the Oracle I Ching application.

This script provides a command-line interface to run either the API server
or the Streamlit web application.
"""

import argparse
import os
import socket
import subprocess
import sys
import time

import requests
import uvicorn


def is_port_in_use(port, host="0.0.0.0"):
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def run_api(host="0.0.0.0", port=8000, reload=True):
    """Run the FastAPI server."""
    if is_port_in_use(port, host):
        print(f"ERROR: Port {port} is already in use.")
        sys.exit(1)

    print(f"Starting API server at http://{host}:{port}")
    uvicorn.run("src.app.api.app:app", host=host, port=port, reload=reload)


def run_streamlit(port=8501):
    """Run the Streamlit web application."""
    if is_port_in_use(port, "127.0.0.1"):
        print(f"ERROR: Port {port} is already in use.")
        sys.exit(1)

    print("Starting Streamlit application...")
    subprocess.run(
        f"streamlit run src/app/web/streamlit_app.py --server.port={port}",
        shell=True,
        check=True,
    )


def wait_for_api(url, max_retries=10, retry_interval=1):
    """Wait for the API server to be ready."""
    print(f"Waiting for API server at {url}...")
    for i in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("API server is ready!")
                return True
        except requests.exceptions.ConnectionError:
            pass

        print(
            f"API not ready yet, retrying in {retry_interval}s... ({i+1}/{max_retries})"
        )
        time.sleep(retry_interval)

    print("Failed to connect to API server after multiple attempts")
    return False


def main():
    """Parse command line arguments and run the appropriate application."""
    parser = argparse.ArgumentParser(description="Oracle I Ching Application")
    parser.add_argument(
        "--app",
        choices=["api", "web", "both"],
        default="api",
        help="Which application to run (api, web, or both)",
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to run the API server on"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to run the API server on"
    )
    parser.add_argument(
        "--streamlit-port",
        type=int,
        default=8501,
        help="Port to run the Streamlit app on",
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload for the API server",
    )

    args = parser.parse_args()

    if args.app == "api":
        run_api(args.host, args.port, not args.no_reload)
    elif args.app == "web":
        run_streamlit(args.streamlit_port)
    elif args.app == "both":
        # Check for port conflicts first
        if is_port_in_use(args.port, args.host):
            print(f"ERROR: Port {args.port} is already in use.")
            sys.exit(1)

        if is_port_in_use(args.streamlit_port, "127.0.0.1"):
            print(f"ERROR: Port {args.streamlit_port} is already in use.")
            sys.exit(1)

        api_cmd = [
            "python",
            "-m",
            "uvicorn",
            "src.app.api.app:app",
            "--host",
            args.host,
            "--port",
            str(args.port),
        ]

        if not args.no_reload:
            api_cmd.append("--reload")

        try:
            api_process = subprocess.Popen(api_cmd)

            api_url = f"http://localhost:{args.port}/languages"
            if wait_for_api(api_url):
                try:
                    run_streamlit(args.streamlit_port)
                except KeyboardInterrupt:
                    print("Streamlit application stopped by user")
                finally:
                    print("Shutting down API server...")
                    api_process.terminate()
                    api_process.wait()
            else:
                print("Shutting down due to API server not starting properly.")
                api_process.terminate()
                api_process.wait()
                sys.exit(1)
        except Exception as e:
            print(f"Error starting API server: {e}")
            sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
