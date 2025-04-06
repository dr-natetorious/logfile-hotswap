#!/usr/bin/env python3
"""
Server management shell entry point.
"""
import os
import sys
import argparse
from shell.shell import ServerShell

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Server Management Shell')
    parser.add_argument('--config', '-c', type=str, help='Path to config file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    return parser.parse_args()


def load_config(config_path=None):
    """Load configuration from file or use defaults."""
    # Default config
    config = {
        'history_file': os.path.expanduser('~/.server_shell_history'),
        'verbose': False,
    }
    
    # If config path is provided, load it
    if config_path and os.path.exists(config_path):
        # In a real application, you'd load from the file here
        # For example, using json.load() or configparser
        pass
    
    return config


def main():
    """Main entry point for the application."""
    # Parse command line arguments
    args = parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line args
    if args.verbose:
        config['verbose'] = True
    
    try:
        # Create and run the shell
        shell = ServerShell(config)
        shell.run()
        return 0
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        if config.get('verbose'):
            import traceback
            traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())