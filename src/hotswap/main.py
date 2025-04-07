#!/usr/bin/env python3
"""
FdHotSwap - A tool to redirect file descriptors in running processes.

This tool allows redirecting file descriptors in a running process without
requiring a restart. It's particularly useful for log file rotation in
third-party applications where restart is complex or disruptive.

This tool requires the same user permissions as the target process.
"""

import argparse
import os
import pwd
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

class FdHotSwap:
    """
    A class to handle file descriptor hot-swapping in running processes.
    
    This class provides functionality to redirect file descriptors from
    one file to another in a running process, without requiring a restart.
    """
    
    def __init__(self, pid: int, old_path: str, new_path: str, verbose: bool = True) -> None:
        """
        Initialize the FdHotSwap instance.
        
        Args:
            pid: The process ID of the target process.
            old_path: The current file path to be redirected.
            new_path: The new file path to redirect to.
            verbose: Whether to print detailed progress messages.
        """
        self.pid = pid
        self.old_path = Path(old_path).absolute()
        self.new_path = Path(new_path).absolute()
        self.verbose = verbose
        self.fd_number: Optional[int] = None
    
    def log(self, message: str) -> None:
        """
        Print a log message if verbose mode is enabled.
        
        Args:
            message: The message to print.
        """
        if self.verbose:
            print(message)
    
    def check_process_exists(self) -> bool:
        """
        Check if the target process exists.
        
        Returns:
            True if the process exists, False otherwise.
        """
        try:
            os.kill(self.pid, 0)
            return True
        except OSError:
            self.log(f"Error: Process {self.pid} does not exist.")
            return False
    
    def check_process_ownership(self) -> bool:
        """
        Check if the current user owns the target process.
        
        Returns:
            True if the current user owns the process, False otherwise.
        """
        try:
            # Get the UID of the process by checking the owner of the /proc/{pid} directory
            proc_path = Path(f"/proc/{self.pid}")
            proc_stat = proc_path.stat()
            proc_uid = proc_stat.st_uid
            
            # Get the current user's UID
            current_uid = os.getuid()
            
            if proc_uid != current_uid:
                try:
                    proc_user = pwd.getpwuid(proc_uid).pw_name
                    current_user = pwd.getpwuid(current_uid).pw_name
                    self.log(f"Error: Process {self.pid} is owned by {proc_user}, but you are {current_user}.")
                    self.log("You can only redirect file descriptors for processes you own.")
                except KeyError:
                    # Handle the case where a UID doesn't map to a username
                    self.log(f"Error: Process {self.pid} is owned by UID {proc_uid}, but you are UID {current_uid}.")
                    self.log("You can only redirect file descriptors for processes you own.")
                return False
            return True
        except (FileNotFoundError, PermissionError):
            self.log(f"Error: Unable to determine ownership of process {self.pid}. Process may not exist or you lack permissions.")
            return False
        except Exception as e:
            self.log(f"Error checking process ownership: {str(e)}")
            return False
    
    def find_file_descriptor(self) -> bool:
        """
        Find the file descriptor that points to the old path.
        
        Returns:
            True if the file descriptor was found, False otherwise.
        """
        try:
            fd_dir = Path(f"/proc/{self.pid}/fd")
            for fd_path in fd_dir.iterdir():
                try:
                    target = fd_path.resolve()
                    if target == self.old_path:
                        self.fd_number = int(fd_path.name)
                        self.log(f"Found matching fd: {self.fd_number} -> {self.old_path}")
                        return True
                except (ValueError, OSError):
                    continue
            
            self.log(f"Error: No file descriptor pointing to {self.old_path} was found in process {self.pid}.")
            self.log(f"Open file descriptors for PID {self.pid}:")
            self.log(subprocess.run(["ls", "-la", f"/proc/{self.pid}/fd/"], 
                                   stdout=subprocess.PIPE).stdout.decode())
            return False
        except (FileNotFoundError, PermissionError) as e:
            self.log(f"Error accessing process file descriptors: {e}")
            return False
    
    def create_new_file(self) -> bool:
        """
        Create the new file and copy permissions from the old file.
        
        Returns:
            True if the file was created successfully, False otherwise.
        """
        try:
            # Create the directory if it doesn't exist
            self.new_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create the new file
            self.new_path.touch()
            self.log(f"Created new file: {self.new_path}")
            
            # Try to copy permissions from old file
            if self.old_path.exists():
                old_stat = self.old_path.stat()
                os.chmod(self.new_path, stat.S_IMODE(old_stat.st_mode))
                self.log(f"Copied permissions from {self.old_path} to {self.new_path}")
            else:
                os.chmod(self.new_path, 0o644)
                self.log(f"Old file not found, set default permissions (644) on {self.new_path}")
            
            return True
        except (OSError, PermissionError) as e:
            self.log(f"Error creating new file: {e}")
            return False
    
    def create_gdb_script(self) -> Tuple[bool, Path]:
        """
        Create a temporary GDB script to perform the file descriptor redirection.
        
        Returns:
            A tuple of (success, script_path).
        """
        try:
            fd, script_path = tempfile.mkstemp(suffix='.gdb')
            os.close(fd)
            
            # Escape backslashes in paths for GDB
            new_path_escaped = str(self.new_path).replace('\\', '\\\\')
        
            script_content = f"""
set pagination off
set confirm off
set height 0
set width 0

# Attach to the process
attach {self.pid}

# Call libc's freopen to safely redirect the file descriptor
# This avoids issues with file descriptor inheritance between GDB and the target process
set $fp = (FILE*)fdopen({self.fd_number}, "a")
call (void*)freopen("{new_path_escaped}", "a", $fp)

# Check the result (will be NULL on failure)
if $1 == 0
    echo REDIRECT_FAILED\\n
    detach
    quit 1
else
    echo REDIRECT_SUCCESS\\n
    # Flush the file to ensure writes are committed
    call fflush((FILE*)$fp)
end

# Detach and quit
detach
quit 0
"""
            Path(script_path).write_text(script_content)
            return True, Path(script_path)
        except OSError as e:
            self.log(f"Error creating GDB script: {e}")
            return False, Path()
    
    def run_gdb(self, script_path: Path) -> bool:
        """
        Run GDB with the created script.
        
        Args:
            script_path: The path to the GDB script.
            
        Returns:
            True if GDB executed successfully, False otherwise.
        """
        try:
            self.log(f"Executing GDB to redirect fd {self.fd_number} to {self.new_path}...")
            result = subprocess.run(["gdb", "-batch", "-x", str(script_path)], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
            
            if result.returncode != 0:
                self.log(f"GDB exited with error code {result.returncode}")
                self.log(f"Output: {result.stdout.decode()}")
                self.log(f"Error: {result.stderr.decode()}")
                return False
            
            return True
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            self.log(f"Error running GDB: {e}")
            return False
    
    def verify_redirection(self) -> bool:
        """
        Verify that the file descriptor now points to the new file.
        
        Returns:
            True if verification succeeded, False otherwise.
        """
        try:
            fd_link = Path(f"/proc/{self.pid}/fd/{self.fd_number}")
            new_target = fd_link.resolve()
            
            if new_target == self.new_path:
                self.log(f"Success! File descriptor {self.fd_number} now points to {self.new_path}")
                self.log(f"You can now safely delete or compress the old log file: {self.old_path}")
                return True
            else:
                self.log(f"Warning: Verification failed. Current target is: {new_target}")
                return False
        except (FileNotFoundError, PermissionError) as e:
            self.log(f"Error verifying redirection: {e}")
            return False
    
    def run(self) -> bool:
        """
        Execute the file descriptor hot-swap process.
        
        Returns:
            True if the operation succeeded, False otherwise.
        """
        # Header
        self.log("Starting log file descriptor hot-swap...")
        self.log(f"PID: {self.pid}")
        self.log(f"Current log: {self.old_path}")
        self.log(f"New log: {self.new_path}")
        self.log("")
        
        # Check prerequisites
        if not self.check_process_exists():
            return False
        
        if not self.check_process_ownership():
            return False
        
        if not self.find_file_descriptor():
            return False
        
        if not self.create_new_file():
            return False
        
        # Create and run GDB script
        success, script_path = self.create_gdb_script()
        if not success:
            return False
        
        try:
            if not self.run_gdb(script_path):
                return False
            
            return self.verify_redirection()
        finally:
            # Clean up the temporary script
            try:
                os.unlink(script_path)
            except OSError:
                pass
            
            self.log("\nOperation completed.")
        
        return True


def main() -> int:
    """
    Main entry point for the fd-hotswap tool.
    
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    parser = argparse.ArgumentParser(
        description="Hot-swap a file descriptor in a running process.",
        epilog="Example: %(prog)s --pid 12345 --from /var/log/app/current.log --to /var/log/app/new.log"
    )
    
    parser.add_argument("-p", "--pid", type=int, required=True, help="Process ID of the target process")
    parser.add_argument("-f", "--from", dest="old_path", type=str, required=True, help="Current log file path")
    parser.add_argument("-t", "--to", dest="new_path", type=str, required=True, help="New log file path")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress detailed output")
    
    args = parser.parse_args()
    
    hotswap = FdHotSwap(args.pid, args.old_path, args.new_path, verbose=not args.quiet)
    success = hotswap.run()
    
    return 0 if success else 1

if __name__ == "__main__":
    #hotswap = FdHotSwap(21367, "/mnt/c/git/logfile-hotswap/bin/test.log", "/mnt/c/git/logfile-hotswap/bin/test2.log", verbose=True)
    #success = hotswap.run()
    sys.exit(main())