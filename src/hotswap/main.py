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
from typing import Dict, List, Optional, Tuple, Union, Set


def find_processes_with_file(file_path: Path) -> List[int]:
    """
    Find all processes that have the specified file open.
    
    Args:
        file_path: The absolute path to the file to search for.
        
    Returns:
        A list of process IDs that have the file open.
    """
    file_path = file_path.absolute()
    pids = []
    
    # Iterate through all processes in /proc
    for proc_dir in Path("/proc").glob("[0-9]*"):
        try:
            pid = int(proc_dir.name)
            fd_dir = proc_dir / "fd"
            
            # Skip if fd directory doesn't exist or isn't accessible
            if not fd_dir.exists() or not os.access(fd_dir, os.R_OK):
                continue
                
            # Check each fd to see if it points to our target file
            for fd_path in fd_dir.glob("*"):
                try:
                    if fd_path.resolve() == file_path:
                        pids.append(pid)
                        break  # Found a match in this process, move to next
                except (OSError, ValueError):
                    continue
        except (ValueError, PermissionError, FileNotFoundError):
            continue
            
    return pids


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
            
            # Create the new file if it doesn't exist
            if not self.new_path.exists():
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
            else:
                self.log(f"Using existing file: {self.new_path}")
                # Update permissions on existing file if needed
                if self.old_path.exists():
                    old_stat = self.old_path.stat()
                    os.chmod(self.new_path, stat.S_IMODE(old_stat.st_mode))
                    self.log(f"Updated permissions on existing file to match {self.old_path}")
            
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
call (FILE*)fdopen({self.fd_number}, "a")
# Store the FILE* in a convenience variable
print $
# Now use that value directly in the freopen call
set $result=(FILE*)freopen("{new_path_escaped}", "a", $)

# Check if the result is NULL (0)
if $result == 0
    echo REDIRECT_FAILED\\n
    detach
    quit 1
else
    echo REDIRECT_SUCCESS\\n
    # No need to flush; the target app will flush its buffers eventually
    # fflush((FILE*)$1)
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
        self.log(f"Starting log file descriptor hot-swap for process {self.pid}...")
        self.log(f"Current log: {self.old_path}")
        self.log(f"New log: {self.new_path}")
        self.log("")
        
        # Check prerequisites
        if not self.check_process_exists():
            self.log("\nOperation completed.")
            return False
        
        if not self.check_process_ownership():
            self.log("\nOperation completed.")
            return False
        
        if not self.find_file_descriptor():
            self.log("\nOperation completed.")
            return False
        
        if not self.create_new_file():
            self.log("\nOperation completed.")
            return False
        
        # Create and run GDB script
        success, script_path = self.create_gdb_script()
        if not success:
            self.log("\nOperation completed.")
            return False
        
        result = False
        try:
            if not self.run_gdb(script_path):
                self.log("\nOperation completed.")
                return False
            
            result = self.verify_redirection()
            if result:
                self.log(f"You can now safely delete or compress the old log file: {self.old_path}")
            self.log("\nOperation completed.")
            return result
        finally:
            # Clean up the temporary script
            try:
                os.unlink(script_path)
            except OSError:
                pass


def process_all_instances(old_path: str, new_path: str, verbose: bool = True) -> Tuple[bool, int]:
    """
    Process all instances of processes that have the old file open.
    
    Args:
        old_path: Path to the old file.
        new_path: Path to the new file.
        verbose: Whether to print verbose output.
        
    Returns:
        A tuple of (success, count) where:
            - success is True if all processes were processed successfully
            - count is the number of processes found and processed
    """
    old_path_abs = Path(old_path).absolute()
    
    if verbose:
        print(f"Searching for processes with open file: {old_path_abs}")
    
    pids = find_processes_with_file(old_path_abs)
    
    if not pids:
        if verbose:
            print(f"No processes found with file {old_path_abs} open.")
            print("\nOperation completed.")
        return True, 0  # No error, but no processes found
    
    if verbose:
        print(f"Found {len(pids)} process(es) with file open: {', '.join(map(str, pids))}")
    
    # Create the new file first (just once)
    new_path_abs = Path(new_path).absolute()
    new_path_abs.parent.mkdir(parents=True, exist_ok=True)
    
    # Handle file creation or update permissions if it exists
    try:
        if not new_path_abs.exists():
            new_path_abs.touch()
            if verbose:
                print(f"Created new file: {new_path_abs}")
            
            if old_path_abs.exists():
                old_stat = old_path_abs.stat()
                os.chmod(new_path_abs, stat.S_IMODE(old_stat.st_mode))
                if verbose:
                    print(f"Copied permissions from {old_path_abs} to {new_path_abs}")
            else:
                os.chmod(new_path_abs, 0o644)
                if verbose:
                    print(f"Old file not found, set default permissions (644) on {new_path_abs}")
        else:
            if verbose:
                print(f"Using existing file: {new_path_abs}")
            
            # Update permissions on existing file
            if old_path_abs.exists():
                old_stat = old_path_abs.stat()
                os.chmod(new_path_abs, stat.S_IMODE(old_stat.st_mode))
                if verbose:
                    print(f"Updated permissions on existing file to match {old_path_abs}")
    except (OSError, PermissionError) as e:
        if verbose:
            print(f"Error setting up target file: {e}")
            print("\nOperation completed.")
        return False, 0
    
    # Track overall success
    overall_success = True
    successful_pids = []
    failed_pids = []
    
    # Process each PID
    for pid in pids:
        if verbose:
            print(f"\n{'=' * 50}")
        
        hotswap = FdHotSwap(pid, old_path, new_path, verbose=verbose)
        success = hotswap.run()
        
        if success:
            successful_pids.append(pid)
        else:
            failed_pids.append(pid)
            overall_success = False
    
    # Summary
    if verbose:
        print(f"\n{'=' * 50}")
        print("\nOperation Summary:")
        print(f"Successfully redirected {len(successful_pids)} process(es): {', '.join(map(str, successful_pids)) if successful_pids else 'None'}")
        print(f"Failed to redirect {len(failed_pids)} process(es): {', '.join(map(str, failed_pids)) if failed_pids else 'None'}")
        
        if successful_pids:
            print(f"\nYou can now safely delete or compress the old log file: {old_path_abs}")
        
        print("\nOperation completed.")
    
    return overall_success, len(pids)


def main() -> int:
    """
    Main entry point for the fd-hotswap tool.
    
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    parser = argparse.ArgumentParser(
        description="Hot-swap a file descriptor in a running process.",
        epilog="""
Examples:
  %(prog)s --from /var/log/app/current.log --to /var/log/app/new.log
  %(prog)s --pid 12345 --from /var/log/app/current.log --to /var/log/app/new.log
"""
    )
    
    parser.add_argument("-p", "--pid", type=int, help="Process ID of the target process (optional)")
    parser.add_argument("-f", "--from", dest="old_path", type=str, required=True, help="Current log file path")
    parser.add_argument("-t", "--to", dest="new_path", type=str, required=True, help="New log file path")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress detailed output")
    
    args = parser.parse_args()
    verbose = not args.quiet
    
    if args.pid is not None:
        # Process a specific PID
        hotswap = FdHotSwap(args.pid, args.old_path, args.new_path, verbose=verbose)
        success = hotswap.run()
        return 0 if success else 1
    else:
        # Find and process all matching PIDs
        success, count = process_all_instances(args.old_path, args.new_path, verbose=verbose)
        if count == 0:
            # Special case: no error, but no processes found
            if verbose:
                # Already printed detailed message in process_all_instances
                pass
            else:
                print(f"No processes found with file {args.old_path} open.")
            return 2  # Special exit code for "no processes found"
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())