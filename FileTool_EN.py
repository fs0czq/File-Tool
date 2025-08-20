import os
import sys
import psutil
import ctypes
import shutil
import subprocess
import re
from time import sleep
from colorama import Fore, Back, Style, init
from typing import List, Tuple, Optional, Union

class FileUtils:
    """Helper class for file operations"""
    
    @staticmethod
    def clear_screen():
        os.system("cls" if os.name == "nt" else "clear")
        print(Fore.RESET + Back.RESET + Style.RESET_ALL, end='')
    
    @staticmethod
    def show_banner():
        print(Fore.LIGHTCYAN_EX + r"""
███████╗██╗██╗     ███████╗              ████████╗ ██████╗  ██████╗ ██╗     
██╔════╝██║██║     ██╔════╝              ╚══██╔══╝██╔═══██╗██╔═══██╗██║     
█████╗  ██║██║     █████╗      █████╗       ██║   ██║   ██║██║   ██╗██║     
██╔══╝  ██║██║     ██╔══╝      ╚════╝       ██║   ██║   ██║██║   ██║██║     
██║     ██║███████╗███████╗                 ██║   ╚██████╔╝╚██████╔╝███████╗
╚═╝     ╚═╝╚══════╝╚══════╝                 ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝
""" + Fore.LIGHTGREEN_EX + """
--------------------
< Coded by @sxnff />
--------------------""" + Fore.RESET)
        input(Fore.LIGHTYELLOW_EX + "\n[+] Press Enter to continue..." + Fore.RESET)
        FileUtils.clear_screen()

    @staticmethod
    def is_windows() -> bool:
        """Check if operating system is Windows"""
        return os.name == "nt"

    @staticmethod
    def is_admin() -> bool:
        """Check for admin/root privileges"""
        try:
            if FileUtils.is_windows():
                return ctypes.windll.shell32.IsUserAnAdmin()
            else:
                return os.geteuid() == 0
        except Exception:
            return False

    @staticmethod
    def ensure_admin():
        """Prevent execution without admin privileges"""
        if not FileUtils.is_admin():
            if FileUtils.is_windows():
                # Request admin privileges on Windows
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                sys.exit()
            else:
                print(Fore.RED + Style.BRIGHT + "[!] This code requires root privileges!" + Fore.RESET)
                sys.exit(1)

    @staticmethod
    def get_permission(path: str) -> bool:
        """Adjust file/folder permissions"""
        try:
            if FileUtils.is_windows():
                cmds = [
                    f'takeown /F "{path}"',
                    f'icacls "{path}" /grant Administrators:F'
                ]
            else:
                # More secure permissions - 755 instead of 777
                cmds = [f'chmod 755 "{path}"']

            for cmd in cmds:
                try:
                    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"[→] Executing: {cmd}..." + Fore.RESET)
                    subprocess.run(
                        cmd, shell=True, check=True, 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    print(Fore.GREEN + Style.BRIGHT + "[✓] Success!" + Fore.RESET)
                    return True
                except subprocess.CalledProcessError as e:
                    print(Fore.RED + Style.BRIGHT + f"[✗] Error: {e}" + Fore.RESET)
                    return False
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"[✗] Permission error: {e}" + Fore.RESET)
            return False

    @staticmethod
    def terminate_process(process_name: str) -> bool:
        """Terminate specified process"""
        try:
            pname = process_name.lower()
            terminated = False
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    n = proc.info['name']
                    if n and n.lower() == pname:
                        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + 
                              f"[→] Terminating {n} (PID: {proc.pid})..." + Fore.RESET)
                        proc.terminate()  # Try graceful shutdown first
                        sleep(1)
                        
                        if proc.is_running():
                            proc.kill()  # Force kill if still running
                            
                        print(Fore.GREEN + Style.BRIGHT + f"[✓] {n} successfully terminated!" + Fore.RESET)
                        terminated = True
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    print(Fore.RED + Style.BRIGHT + f"[✗] Failed to terminate {n}: {e}" + Fore.RESET)
            
            return terminated
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"[✗] Process termination error: {e}" + Fore.RESET)
            return False

class ProcessUtils:
    """Helper class for process operations"""
    
    @staticmethod
    def find_processes_using_file(file_path: str) -> List[psutil.Process]:
        """Find processes using the specified file"""
        try:
            file_handles = []
            normalized_path = os.path.abspath(file_path)
            
            for proc in psutil.process_iter(['pid', 'name', 'open_files']):
                try:
                    if proc.info['open_files']:
                        for open_file in proc.info['open_files']:
                            if os.path.abspath(open_file.path) == normalized_path:
                                file_handles.append(proc)
                                break
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    continue
            
            return file_handles
        except Exception as e:
            print(Fore.YELLOW + Style.BRIGHT + 
                 f"[!] File usage check error: {e}" + Fore.RESET)
            return []

    @staticmethod
    def terminate_processes_using_file(file_path: str) -> bool:
        """Terminate processes using the file"""
        processes = ProcessUtils.find_processes_using_file(file_path)
        if not processes:
            return False
        
        success = True
        for proc in processes:
            try:
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + 
                     f"[→] Terminating {proc.info['name']} (PID: {proc.pid})..." + Fore.RESET)
                
                # Try graceful termination first
                proc.terminate()
                sleep(1)
                
                # Force kill if still running
                if proc.is_running():
                    proc.kill()
                    sleep(0.5)
                
                print(Fore.GREEN + Style.BRIGHT + 
                     f"[✓] {proc.info['name']} successfully terminated!" + Fore.RESET)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(Fore.RED + Style.BRIGHT + 
                     f"[✗] Failed to terminate {proc.info.get('name', 'Unknown')}: {e}" + Fore.RESET)
                success = False
            except Exception as e:
                print(Fore.RED + Style.BRIGHT + 
                     f"[✗] Process termination error: {e}" + Fore.RESET)
                success = False
        
        return success

class DiskUtils:
    """Helper class for disk operations"""
    
    @staticmethod
    def get_available_disks() -> List[str]:
        """List available disks"""
        disks = []
        try:
            for partition in psutil.disk_partitions():
                if partition.device and os.path.exists(partition.mountpoint):
                    disks.append(partition.mountpoint)
            
            # Add root on Linux
            if not FileUtils.is_windows() and "/" not in disks:
                disks.append("/")
                
            return disks
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"[✗] Disk listing error: {e}" + Fore.RESET)
            return ["/"] if not FileUtils.is_windows() else ["C:\\"]

    @staticmethod
    def select_scan_method() -> str:
        """Select scanning method"""
        while True:
            method = input(Fore.CYAN + Style.BRIGHT + 
                          "[?] Scan method (e)xact / (s)imilar: " + Fore.RESET).lower()
            if method in ("e", "s"):
                return method
            print(Fore.RED + Style.BRIGHT + "[!] Invalid selection!" + Fore.RESET)

    @staticmethod
    def select_disks() -> Tuple[List[str], str]:
        """Select disks for scanning"""
        disks = DiskUtils.get_available_disks()
        method = DiskUtils.select_scan_method()
        
        while True:
            choice = input(Fore.CYAN + Style.BRIGHT + 
                          "[?] Specific disk/partition? (y/n): " + Fore.RESET).lower()
            
            if choice == "y":
                if os.name == "nt":
                    print(Fore.CYAN + Style.BRIGHT + f"Available disks:\n{Fore.LIGHTMAGENTA_EX}{Style.BRIGHT}******************" + Fore.RESET)
                else:
                    print(Fore.CYAN + Style.BRIGHT + f"Available partitions:\n{Fore.LIGHTMAGENTA_EX}{Style.BRIGHT}******************" + Fore.RESET)
                for d in disks:
                    print(d.strip())
                print(f"{Fore.LIGHTMAGENTA_EX}{Style.BRIGHT}******************" + Fore.RESET)
                entries = input(Fore.CYAN + Style.BRIGHT + 
                               "[>] Enter disks/partitions (comma separated): " + Fore.RESET).split(",")
                
                valid_disks = []
                for entry in entries:
                    clean_entry = entry.strip()
                    if os.path.exists(clean_entry):
                        valid_disks.append(clean_entry)
                    else:
                        print(Fore.YELLOW + Style.BRIGHT + 
                             f"[!] {clean_entry} not found, skipping..." + Fore.RESET)
                
                if valid_disks:
                    return valid_disks, method
                print(Fore.RED + Style.BRIGHT + "[!] No valid disks found!" + Fore.RESET)
                
            elif choice == "n":
                return disks, method
            else:
                print(Fore.RED + Style.BRIGHT + "[!] Invalid selection!" + Fore.RESET)

class RegistryUtils:
    """Helper class for Windows registry operations"""
    
    @staticmethod
    def search_registry(target: str):
        """Search in registry"""
        if not FileUtils.is_windows():
            print(Fore.RED + Style.BRIGHT + "[!] This feature only works on Windows!" + Fore.RESET)
            return
        
        FileUtils.clear_screen()
        options = {"1": "HKCU", "2": "HKLM", "3": "HKCR", "4": "HKU", "5": "HKCC"}
        
        while True:
            print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "\n[1] HKEY_CURRENT_USER")
            print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[2] HKEY_LOCAL_MACHINE")
            print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[3] HKEY_CLASSES_ROOT")
            print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[4] HKEY_USERS")
            print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[5] HKEY_CURRENT_CONFIG")
            print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[0] Back" + Fore.RESET)
            
            choice = input(Fore.CYAN + Style.BRIGHT + "[>] Your choice: " + Fore.RESET)
            if choice == "0":
                return
            
            root = options.get(choice)
            if root:
                break
            
            print(Fore.RED + Style.BRIGHT + "[!] Invalid selection!" + Fore.RESET)

        print(Fore.YELLOW + Style.BRIGHT + "\n[~] Scanning, please wait..." + Fore.RESET)
        found = False
        
        try:
            # More secure command execution
            result = subprocess.run(
                f'reg query {root} /f "{target}" /s', 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if target.lower() in line.lower():
                        found = True
                        print(Fore.GREEN + Style.BRIGHT + f"[✓] {line}" + Fore.RESET)
            else:
                print(Fore.YELLOW + Style.BRIGHT + 
                     f"[!] Registry query error code: {result.returncode}" + Fore.RESET)
                
        except subprocess.TimeoutExpired:
            print(Fore.RED + Style.BRIGHT + "[!] Registry scan timed out!" + Fore.RESET)
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"[✗] Registry scan error: {e}" + Fore.RESET)

        if not found:
            print(f"{Fore.LIGHTWHITE_EX}[{Fore.RED + Style.BRIGHT}✗{Fore.LIGHTWHITE_EX}]{Fore.RED + Style.BRIGHT} No records found" + Fore.RESET)
        
        input(Fore.YELLOW + Style.BRIGHT + "\n[+] Press Enter to continue..." + Fore.RESET)

class FileFinder:
    """File search class"""
    
    @staticmethod
    def highlight_match(text: str, pattern: str, color: str = Fore.LIGHTCYAN_EX) -> str:
        """Highlight matching text"""
        try:
            lower_text = text.lower()
            lower_pattern = pattern.lower()
            
            if lower_pattern in lower_text:
                start = lower_text.find(lower_pattern)
                end = start + len(lower_pattern)
                return text[:start] + color + text[start:end] + Fore.LIGHTGREEN_EX + text[end:]
            return text
        except Exception:
            return text

    @staticmethod
    def find_files(directories: Optional[List[str]] = None, 
                  files: Optional[List[str]] = None, 
                  extensions: Optional[List[str]] = None):
        """Search for files/folders"""
        disks, method = DiskUtils.select_disks()
        label = "disk" if FileUtils.is_windows() else "partition"
        found = False

        for disk in disks:
            print(f"\n{Fore.LIGHTWHITE_EX}[{Fore.MAGENTA + Style.BRIGHT}✓{Fore.LIGHTWHITE_EX}]"
                 f"{Fore.MAGENTA + Style.BRIGHT} Scanning {disk} {label}..." + Fore.RESET)
            
            try:
                for root, dirs, file_list in os.walk(disk):
                    try:
                        if directories:
                            for directory in directories:
                                lower_dir = directory.lower()
                                lower_root = root.lower()
                                base_name = os.path.basename(root).lower()
                                
                                match = False
                                if method == "s" and lower_dir in lower_root:
                                    match = True
                                elif method == "e" and lower_dir == base_name:
                                    match = True
                                
                                if match:
                                    highlighted = FileFinder.highlight_match(root, directory)
                                    print(f"{Fore.LIGHTWHITE_EX}[{Fore.LIGHTGREEN_EX + Style.BRIGHT}✓{Fore.LIGHTWHITE_EX}]"
                                         f"{Fore.LIGHTGREEN_EX + Style.BRIGHT} {highlighted}" + Fore.RESET)
                                    found = True
                        
                        if files:
                            for file_name in file_list:
                                for search_file in files:
                                    lower_search = search_file.lower()
                                    lower_file = file_name.lower()
                                    fname, fext = os.path.splitext(file_name)
                                    
                                    match = False
                                    if method == "s" and lower_search in lower_file:
                                        match = True
                                    elif method == "e" and (lower_search == fname.lower() or 
                                                          lower_search == lower_file):
                                        match = True
                                    
                                    if match:
                                        full_path = os.path.join(root, file_name)
                                        highlighted = FileFinder.highlight_match(full_path, search_file)
                                        print(f"{Fore.LIGHTWHITE_EX}[{Fore.LIGHTGREEN_EX + Style.BRIGHT}✓{Fore.LIGHTWHITE_EX}]"
                                             f"{Fore.LIGHTGREEN_EX + Style.BRIGHT} {highlighted}" + Fore.RESET)
                                        found = True
                        
                        if extensions:
                            for file_name in file_list:
                                for ext in extensions:
                                    if file_name.lower().endswith(ext.lower()):
                                        full_path = os.path.join(root, file_name)
                                        highlighted = FileFinder.highlight_match(
                                            full_path, ext, Fore.LIGHTCYAN_EX
                                        )
                                        print(f"{Fore.LIGHTWHITE_EX}[{Fore.LIGHTGREEN_EX + Style.BRIGHT}✓{Fore.LIGHTWHITE_EX}]"
                                             f"{Fore.LIGHTGREEN_EX + Style.BRIGHT} {highlighted}" + Fore.RESET)
                                        found = True
                    
                    except PermissionError:
                        continue  # Skip directories with permission errors
                    except Exception as e:
                        print(Fore.YELLOW + Style.BRIGHT + 
                             f"[!] Error scanning {root}: {e}" + Fore.RESET)
                        
            except Exception as e:
                print(Fore.RED + Style.BRIGHT + 
                     f"[✗] Error scanning {disk}: {e}" + Fore.RESET)

        if not found:
            print(Fore.RED + Style.BRIGHT + "[✗] Not found!" + Fore.RESET)
        
        input(Fore.YELLOW + Style.BRIGHT + "\n[+] Press Enter to continue..." + Fore.RESET)

class FileDeleter:
    """File deletion class - Enhanced version"""
    
    @staticmethod
    def safe_delete_file(file_path: str) -> bool:
        """Safely delete file (with process control)"""
        max_retries = 2
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # First try - normal deletion
                os.remove(file_path)
                print(Fore.GREEN + Style.BRIGHT + f"[✓] Deleted: {file_path}" + Fore.RESET)
                return True
                
            except PermissionError:
                if attempt == 0:
                    # Permission error on first try - check processes
                    print(Fore.YELLOW + Style.BRIGHT + 
                         f"[!] File might be in use, checking processes..." + Fore.RESET)
                    
                    # Terminate processes using the file
                    if ProcessUtils.terminate_processes_using_file(file_path):
                        sleep(retry_delay)  # Wait for processes to close
                        continue
                    else:
                        # Might be permission issue, try adjusting permissions
                        if FileUtils.get_permission(file_path):
                            sleep(retry_delay)
                            continue
                
                print(Fore.RED + Style.BRIGHT + 
                     f"[✗] Failed to delete: {file_path} (Permission error)" + Fore.RESET)
                return False
                
            except FileNotFoundError:
                print(Fore.YELLOW + Style.BRIGHT + 
                     f"[!] File already deleted: {file_path}" + Fore.RESET)
                return True
                
            except Exception as e:
                print(Fore.RED + Style.BRIGHT + 
                     f"[✗] Failed to delete: {file_path} ({e})" + Fore.RESET)
                return False
        
        return False

    @staticmethod
    def safe_delete_directory(dir_path: str) -> bool:
        """Safely delete directory"""
        try:
            # First check all files inside
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Try file deletion (includes process control)
                    FileDeleter.safe_delete_file(file_path)
            
            # Then delete the directory
            shutil.rmtree(dir_path)
            print(Fore.GREEN + Style.BRIGHT + f"[✓] Directory deleted: {dir_path}" + Fore.RESET)
            return True
            
        except PermissionError:
            # Permission error - check processes
            print(Fore.YELLOW + Style.BRIGHT + 
                 f"[!] Directory might be in use, checking processes..." + Fore.RESET)
            
            # Find and terminate processes using files in the directory
            processes_found = False
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if ProcessUtils.terminate_processes_using_file(file_path):
                        processes_found = True
            
            if processes_found:
                sleep(2)  # Wait for processes to close
                
            # Try again
            try:
                shutil.rmtree(dir_path)
                print(Fore.GREEN + Style.BRIGHT + f"[✓] Directory deleted: {dir_path}" + Fore.RESET)
                return True
            except Exception as e:
                print(Fore.RED + Style.BRIGHT + 
                     f"[✗] Failed to delete directory: {dir_path} ({e})" + Fore.RESET)
                return False
                
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + 
                 f"[✗] Failed to delete directory: {dir_path} ({e})" + Fore.RESET)
            return False

    @staticmethod
    def delete_items(directories: Optional[List[str]] = None, files: Optional[List[str]] = None):
        """Delete files/folders - Enhanced version"""
        disks, method = DiskUtils.select_disks()
        failed = []
        success_count = 0
        
        print(Fore.CYAN + Style.BRIGHT + 
             "[!] WARNING: This operation will permanently delete files!" + Fore.RESET)
        confirm = input(Fore.CYAN + Style.BRIGHT + 
                       "[?] Do you want to continue? (y/n): " + Fore.RESET).lower()
        
        if confirm != 'y':
            print(Fore.YELLOW + Style.BRIGHT + "[!] Operation cancelled." + Fore.RESET)
            sleep(1)
            return
        
        for disk in disks:
            print(Fore.MAGENTA + Style.BRIGHT + f"\n[~] Scanning {disk}..." + Fore.RESET)
            
            try:
                for root, dirs, file_list in os.walk(disk, topdown=False):
                    try:
                        if directories:
                            for directory in directories:
                                lower_dir = directory.lower()
                                lower_root = root.lower()
                                base_name = os.path.basename(root).lower()
                                
                                match = False
                                if method == "s" and lower_dir in lower_root:
                                    match = True
                                elif method == "e" and lower_dir == base_name:
                                    match = True
                                
                                if match:
                                    if FileDeleter.safe_delete_directory(root):
                                        success_count += 1
                                    else:
                                        failed.append(root)
                        
                        if files:
                            for file_name in file_list:
                                for search_file in files:
                                    lower_search = search_file.lower()
                                    lower_file = file_name.lower()
                                    
                                    match = False
                                    if method == "s" and lower_search in lower_file:
                                        match = True
                                    elif method == "e" and lower_search == lower_file:
                                        match = True
                                    
                                    if match:
                                        full_path = os.path.join(root, file_name)
                                        if FileDeleter.safe_delete_file(full_path):
                                            success_count += 1
                                        else:
                                            failed.append(full_path)
                    
                    except Exception as e:
                        print(Fore.YELLOW + Style.BRIGHT + 
                             f"[!] Error processing {root}: {e}" + Fore.RESET)
                        
            except Exception as e:
                print(Fore.RED + Style.BRIGHT + 
                     f"[✗] Error scanning {disk}: {e}" + Fore.RESET)

        # Show results
        print(Fore.GREEN + Style.BRIGHT + f"\n[✓] Successfully deleted: {success_count}" + Fore.RESET)
        
        if failed:
            print(Fore.RED + Style.BRIGHT + f"\n[!] Failed to process ({len(failed)}):" + Fore.RESET)
            for item in failed[:10]:
                print(Fore.RED + Style.BRIGHT + f"[✗] {item}" + Fore.RESET)
            if len(failed) > 10:
                print(Fore.YELLOW + Style.BRIGHT + 
                     f"[!] ... and {len(failed) - 10} more" + Fore.RESET)
        
        input(Fore.YELLOW + Style.BRIGHT + "\n[+] Press Enter to continue..." + Fore.RESET)

def main():
    """Main application"""
    init(autoreset=True)
    
    # Check admin privileges
    FileUtils.ensure_admin()
    FileUtils.show_banner()
    
    while True:
        FileUtils.clear_screen()
        print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "\n[1] Finder - Find Files/Folders")
        print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[2] Deleter - Delete Files/Folders")
        
        if FileUtils.is_windows():
            print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[3] Registry Scanner - Scan Registry")
            print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[4] Process Killer - Terminate Process")
        else:
            print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[3] Process Killer - Terminate Process")
            
        print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[0] Exit" + Fore.RESET)
        
        choice = input(Fore.CYAN + Style.BRIGHT + "[>] Your choice: " + Fore.RESET).strip()
        
        if choice == "1":
            FileUtils.clear_screen()
            search_type = input(Fore.CYAN + Style.BRIGHT + 
                               "[?] [d] Folder / [f] File / [e] Extension: " + Fore.RESET).lower()
            
            if search_type == "d":
                terms = input(Fore.CYAN + Style.BRIGHT + 
                             "[>] Enter words (comma separated): " + Fore.RESET).split(",")
                FileFinder.find_files(directories=[x.strip() for x in terms])
            
            elif search_type == "f":
                terms = input(Fore.CYAN + Style.BRIGHT + 
                             "[>] Enter words (comma separated): " + Fore.RESET).split(",")
                FileFinder.find_files(files=[x.strip() for x in terms])
            
            elif search_type == "e":
                terms = input(Fore.CYAN + Style.BRIGHT + 
                             "[>] Enter extensions (comma separated, with dot): " + Fore.RESET).split(",")
                FileFinder.find_files(extensions=[x.strip() for x in terms])
        
        elif choice == "2":
            FileUtils.clear_screen()
            delete_type = input(Fore.CYAN + Style.BRIGHT + 
                               "[?] [d] Folder / [f] File: " + Fore.RESET).lower()
            
            if delete_type == "d":
                terms = input(Fore.CYAN + Style.BRIGHT + 
                             "[>] Enter words (comma separated): " + Fore.RESET).split(",")
                FileDeleter.delete_items(directories=[x.strip() for x in terms])
            
            elif delete_type == "f":
                terms = input(Fore.CYAN + Style.BRIGHT + 
                             "[>] Enter words (comma separated): " + Fore.RESET).split(",")
                FileDeleter.delete_items(files=[x.strip() for x in terms])
        
        elif choice == "3" and FileUtils.is_windows():
            FileUtils.clear_screen()
            key = input(Fore.CYAN + Style.BRIGHT + 
                       "[>] Registry key word: " + Fore.RESET).strip()
            if key:
                RegistryUtils.search_registry(key)
        
        elif choice == "4" and FileUtils.is_windows():
            FileUtils.clear_screen()
            process_name = input(Fore.CYAN + Style.BRIGHT + 
                                "[>] Process name to terminate: " + Fore.RESET).strip()
            if process_name:
                FileUtils.terminate_process(process_name)
                input(Fore.YELLOW + Style.BRIGHT + 
                     "\n[+] Press Enter to continue..." + Fore.RESET)
        
        elif choice == "3":
            FileUtils.clear_screen()
            process_name = input(Fore.CYAN + Style.BRIGHT + 
                                "[>] Process name to terminate: " + Fore.RESET).strip()
            if process_name:
                FileUtils.terminate_process(process_name)
                input(Fore.YELLOW + Style.BRIGHT + 
                     "\n[+] Press Enter to continue..." + Fore.RESET)
                
                
        elif choice == "0":
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n[+] Exiting..." + Fore.RESET)
            sleep(1)
            break
        
        else:
            print(Fore.RED + Style.BRIGHT + "[!] Invalid selection!" + Fore.RESET)
            sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.YELLOW + Style.BRIGHT + "\n[!] Stopped by user!" + Fore.RESET)
        sys.exit(0)
    except Exception as e:
        print(Fore.RED + Style.BRIGHT + f"[✗] Unexpected error: {e}" + Fore.RESET)
        sys.exit(1)
