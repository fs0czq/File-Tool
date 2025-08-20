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
    """Dosya işlemleri için yardımcı sınıf"""
    
    @staticmethod
    def clear_screen():
        os.system("cls" if os.name == "nt" else "clear")
        print(Fore.RESET + Back.RESET + Style.RESET_ALL, end='')
    
    @staticmethod
    def show_banner():
        print(Fore.LIGHTCYAN_EX + r"""
███████╗██╗██╗     ███████╗              ████████╗ ██████╗  ██████╗ ██╗     
██╔════╝██║██║     ██╔════╝              ╚══██╔══╝██╔═══██╗██╔═══██╗██║     
█████╗  ██║██║     █████╗      █████╗       ██║   ██║   ██║██║   ██║██║     
██╔══╝  ██║██║     ██╔══╝      ╚════╝       ██║   ██║   ██║██║   ██║██║     
██║     ██║███████╗███████╗                 ██║   ╚██████╔╝╚██████╔╝███████╗
╚═╝     ╚═╝╚══════╝╚══════╝                 ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝
""" + Fore.LIGHTGREEN_EX + """
--------------------
< Coded by @sxnff />
--------------------""" + Fore.RESET)
        input(Fore.LIGHTYELLOW_EX + "\n[+] Devam etmek için Enter'a basın..." + Fore.RESET)
        FileUtils.clear_screen()

    @staticmethod
    def is_windows() -> bool:
        """İşletim sistemi Windows mu kontrol et"""
        return os.name == "nt"

    @staticmethod
    def is_admin() -> bool:
        """admin / root yetkileri kontrol et"""
        try:
            if FileUtils.is_windows():
                return ctypes.windll.shell32.IsUserAnAdmin()
            else:
                return os.geteuid() == 0
        except Exception:
            return False

    @staticmethod
    def ensure_admin():
        """Admin yetkileri olmadan çalışmayı engelle"""
        if not FileUtils.is_admin():
            if FileUtils.is_windows():
                # Windows'ta admin yetkisi iste
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                sys.exit()
            else:
                print(Fore.RED + Style.BRIGHT + "[!] Root olmadan bu kod çalışmaz!" + Fore.RESET)
                sys.exit(1)

    @staticmethod
    def get_permission(path: str) -> bool:
        """Dosya/klasör izinlerini düzenle"""
        try:
            if FileUtils.is_windows():
                cmds = [
                    f'takeown /F "{path}"',
                    f'icacls "{path}" /grant Administrators:F'
                ]
            else:
                # Daha güvenli izinler - 777 yerine 755 veya 700
                cmds = [f'chmod 755 "{path}"']

            for cmd in cmds:
                try:
                    print(Fore.LIGHTYELLOW_EX + Style.BRIGHT + f"[→] {cmd} çalıştırılıyor..." + Fore.RESET)
                    subprocess.run(
                        cmd, shell=True, check=True, 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    print(Fore.GREEN + Style.BRIGHT + "[✓] Başarılı!" + Fore.RESET)
                    return True
                except subprocess.CalledProcessError as e:
                    print(Fore.RED + Style.BRIGHT + f"[✗] Hata: {e}" + Fore.RESET)
                    return False
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"[✗] İzin hatası: {e}" + Fore.RESET)
            return False

    @staticmethod
    def terminate_process(process_name: str) -> bool:
        """Belirtilen prosesi sonlandır"""
        try:
            pname = process_name.lower()
            terminated = False
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    n = proc.info['name']
                    if n and n.lower() == pname:
                        print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + 
                              f"[→] {n} (PID: {proc.pid}) kapatılıyor..." + Fore.RESET)
                        proc.terminate()  # Önce graceful shutdown dene
                        sleep(1)
                        
                        if proc.is_running():
                            proc.kill()  # Zorla kapat
                            
                        print(Fore.GREEN + Style.BRIGHT + f"[✓] {n} başarıyla kapatıldı!" + Fore.RESET)
                        terminated = True
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    print(Fore.RED + Style.BRIGHT + f"[✗] {n} kapatılamadı: {e}" + Fore.RESET)
            
            return terminated
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"[✗] Proses kapatma hatası: {e}" + Fore.RESET)
            return False

class ProcessUtils:
    """Proses işlemleri için yardımcı sınıf"""
    
    @staticmethod
    def find_processes_using_file(file_path: str) -> List[psutil.Process]:
        """Belirtilen dosyayı kullanan prosesleri bul"""
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
                 f"[!] Dosya kullanım kontrol hatası: {e}" + Fore.RESET)
            return []

    @staticmethod
    def terminate_processes_using_file(file_path: str) -> bool:
        """Dosyayı kullanan prosesleri sonlandır"""
        processes = ProcessUtils.find_processes_using_file(file_path)
        if not processes:
            return False
        
        success = True
        for proc in processes:
            try:
                print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + 
                     f"[→] {proc.info['name']} (PID: {proc.pid}) kapatılıyor..." + Fore.RESET)
                
                # Önce graceful termination dene
                proc.terminate()
                sleep(1)
                
                # Hala çalışıyorsa force kill yap
                if proc.is_running():
                    proc.kill()
                    sleep(0.5)
                
                print(Fore.GREEN + Style.BRIGHT + 
                     f"[✓] {proc.info['name']} başarıyla kapatıldı!" + Fore.RESET)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(Fore.RED + Style.BRIGHT + 
                     f"[✗] {proc.info.get('name', 'Unknown')} kapatılamadı: {e}" + Fore.RESET)
                success = False
            except Exception as e:
                print(Fore.RED + Style.BRIGHT + 
                     f"[✗] Proses kapatma hatası: {e}" + Fore.RESET)
                success = False
        
        return success

class DiskUtils:
    """Disk işlemleri için yardımcı sınıf"""
    
    @staticmethod
    def get_available_disks() -> List[str]:
        """Kullanılabilir diskleri listele"""
        disks = []
        try:
            for partition in psutil.disk_partitions():
                if partition.device and os.path.exists(partition.mountpoint):
                    disks.append(partition.mountpoint)
            
            # Linux'ta root ekle
            if not FileUtils.is_windows() and "/" not in disks:
                disks.append("/")
                
            return disks
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"[✗] Disk listeleme hatası: {e}" + Fore.RESET)
            return ["/"] if not FileUtils.is_windows() else ["C:\\"]

    @staticmethod
    def select_scan_method() -> str:
        """Tarama yöntemi seç"""
        while True:
            method = input(Fore.CYAN + Style.BRIGHT + 
                          "[?] Tarama yöntemi (k)esinlik / (b)enzerlik: " + Fore.RESET).lower()
            if method in ("k", "b"):
                return method
            print(Fore.RED + Style.BRIGHT + "[!] Geçersiz seçim!" + Fore.RESET)

    @staticmethod
    def select_disks() -> Tuple[List[str], str]:
        """Tarama için diskleri seç"""
        disks = DiskUtils.get_available_disks()
        method = DiskUtils.select_scan_method()
        
        while True:
            choice = input(Fore.CYAN + Style.BRIGHT + 
                          "[?] Belirli disk/bölüm var mı? (e/h): " + Fore.RESET).lower()
            
            if choice == "e":
                if os.name == "nt":
                    print(Fore.CYAN + Style.BRIGHT + f"Mevcut diskler:\n{Fore.LIGHTMAGENTA_EX}{Style.BRIGHT}******************" + Fore.RESET)
                else:
                    print(Fore.CYAN + Style.BRIGHT + f"Mevcut bölümler:\n{Fore.LIGHTMAGENTA_EX}{Style.BRIGHT}******************" + Fore.RESET)
                for d in disks:
                    print(d.strip())
                print(f"{Fore.LIGHTMAGENTA_EX}{Style.BRIGHT}******************" + Fore.RESET)
                entries = input(Fore.CYAN + Style.BRIGHT + 
                               "[>] Disk/Bölümleri girin (virgülle ayırın): " + Fore.RESET).split(",")
                
                valid_disks = []
                for entry in entries:
                    clean_entry = entry.strip()
                    if os.path.exists(clean_entry):
                        valid_disks.append(clean_entry)
                    else:
                        print(Fore.YELLOW + Style.BRIGHT + 
                             f"[!] {clean_entry} bulunamadı, atlanıyor..." + Fore.RESET)
                
                if valid_disks:
                    return valid_disks, method
                print(Fore.RED + Style.BRIGHT + "[!] Geçerli disk bulunamadı!" + Fore.RESET)
                
            elif choice == "h":
                return disks, method
            else:
                print(Fore.RED + Style.BRIGHT + "[!] Geçersiz seçim!" + Fore.RESET)

class RegistryUtils:
    """Windows registry işlemleri için yardımcı sınıf"""
    
    @staticmethod
    def search_registry(target: str):
        """Registry'de arama yap"""
        if not FileUtils.is_windows():
            print(Fore.RED + Style.BRIGHT + "[!] Bu özellik sadece Windows'ta çalışır!" + Fore.RESET)
            return
        
        FileUtils.clear_screen()
        options = {"1": "HKCU", "2": "HKLM", "3": "HKCR", "4": "HKU", "5": "HKCC"}
        
        while True:
            print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "\n[1] HKEY_CURRENT_USER")
            print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[2] HKEY_LOCAL_MACHINE")
            print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[3] HKEY_CLASSES_ROOT")
            print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[4] HKEY_USERS")
            print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[5] HKEY_CURRENT_CONFIG")
            print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[0] Geri" + Fore.RESET)
            
            choice = input(Fore.CYAN + Style.BRIGHT + "[>] Seçiminiz: " + Fore.RESET)
            if choice == "0":
                return
            
            root = options.get(choice)
            if root:
                break
            
            print(Fore.RED + Style.BRIGHT + "[!] Geçersiz seçim!" + Fore.RESET)

        print(Fore.YELLOW + Style.BRIGHT + "\n[~] Taranıyor, lütfen bekleyin..." + Fore.RESET)
        found = False
        
        try:
            # Daha güvenli komut yürütme
            result = subprocess.run(
                f'reg query {root} /f "{target}" /s', 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 dakika timeout
            )
            
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if target.lower() in line.lower():
                        found = True
                        print(Fore.GREEN + Style.BRIGHT + f"[✓] {line}" + Fore.RESET)
            else:
                print(Fore.YELLOW + Style.BRIGHT + 
                     f"[!] Registry sorgusu hata kodu: {result.returncode}" + Fore.RESET)
                
        except subprocess.TimeoutExpired:
            print(Fore.RED + Style.BRIGHT + "[!] Registry taraması zaman aşımına uğradı!" + Fore.RESET)
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + f"[✗] Registry tarama hatası: {e}" + Fore.RESET)

        if not found:
            print(f"{Fore.LIGHTWHITE_EX}[{Fore.RED + Style.BRIGHT}✗{Fore.LIGHTWHITE_EX}]{Fore.RED + Style.BRIGHT} Kayıt Bulunamadı" + Fore.RESET)
        
        input(Fore.YELLOW + Style.BRIGHT + "\n[+] Devam etmek için Enter'a basın..." + Fore.RESET)

class FileFinder:
    """Dosya bulma sınıfı"""
    
    @staticmethod
    def highlight_match(text: str, pattern: str, color: str = Fore.LIGHTCYAN_EX) -> str:
        """Eşleşen metni vurgula"""
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
        """Dosya/klasör arama"""
        disks, method = DiskUtils.select_disks()
        label = "diski" if FileUtils.is_windows() else "bölümü"
        found = False

        for disk in disks:
            print(f"\n{Fore.LIGHTWHITE_EX}[{Fore.MAGENTA + Style.BRIGHT}✓{Fore.LIGHTWHITE_EX}]"
                 f"{Fore.MAGENTA + Style.BRIGHT} {disk} {label} taranıyor..." + Fore.RESET)
            
            try:
                for root, dirs, file_list in os.walk(disk):
                    try:
                        if directories:
                            for directory in directories:
                                lower_dir = directory.lower()
                                lower_root = root.lower()
                                base_name = os.path.basename(root).lower()
                                
                                match = False
                                if method == "b" and lower_dir in lower_root:
                                    match = True
                                elif method == "k" and lower_dir == base_name:
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
                                    if method == "b" and lower_search in lower_file:
                                        match = True
                                    elif method == "k" and (lower_search == fname.lower() or 
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
                        continue  # İzin hatası olan dizinleri atla
                    except Exception as e:
                        print(Fore.YELLOW + Style.BRIGHT + 
                             f"[!] {root} taranırken hata: {e}" + Fore.RESET)
                        
            except Exception as e:
                print(Fore.RED + Style.BRIGHT + 
                     f"[✗] {disk} taranırken hata: {e}" + Fore.RESET)

        if not found:
            print(Fore.RED + Style.BRIGHT + "[✗] Bulunamadı!" + Fore.RESET)
        
        input(Fore.YELLOW + Style.BRIGHT + "\n[+] Devam etmek için Enter'a basın..." + Fore.RESET)

class FileDeleter:
    """Dosya silme sınıfı - Geliştirilmiş versiyon"""
    
    @staticmethod
    def safe_delete_file(file_path: str) -> bool:
        """Dosyayı güvenli bir şekilde sil (proses kontrolü ile)"""
        max_retries = 2
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # İlk deneme - normal silme
                os.remove(file_path)
                print(Fore.GREEN + Style.BRIGHT + f"[✓] Silindi: {file_path}" + Fore.RESET)
                return True
                
            except PermissionError:
                if attempt == 0:
                    # İlk denemede permission hatası - prosesleri kontrol et
                    print(Fore.YELLOW + Style.BRIGHT + 
                         f"[!] Dosya kullanımda olabilir, prosesler kontrol ediliyor..." + Fore.RESET)
                    
                    # Dosyayı kullanan prosesleri sonlandır
                    if ProcessUtils.terminate_processes_using_file(file_path):
                        sleep(retry_delay)  # Proseslerin kapanması için bekle
                        continue
                    else:
                        # İzin sorunu olabilir, izinleri dene
                        if FileUtils.get_permission(file_path):
                            sleep(retry_delay)
                            continue
                
                print(Fore.RED + Style.BRIGHT + 
                     f"[✗] Silinemedi: {file_path} (Yetki hatası)" + Fore.RESET)
                return False
                
            except FileNotFoundError:
                print(Fore.YELLOW + Style.BRIGHT + 
                     f"[!] Dosya zaten silinmiş: {file_path}" + Fore.RESET)
                return True
                
            except Exception as e:
                print(Fore.RED + Style.BRIGHT + 
                     f"[✗] Silinemedi: {file_path} ({e})" + Fore.RESET)
                return False
        
        return False

    @staticmethod
    def safe_delete_directory(dir_path: str) -> bool:
        """Klasörü güvenli bir şekilde sil"""
        try:
            # Önce içindeki tüm dosyaları kontrol et
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Dosya silme denemesi (proses kontrolü yapar)
                    FileDeleter.safe_delete_file(file_path)
            
            # Sonra klasörü sil
            shutil.rmtree(dir_path)
            print(Fore.GREEN + Style.BRIGHT + f"[✓] Klasör silindi: {dir_path}" + Fore.RESET)
            return True
            
        except PermissionError:
            # İzin hatası - proses kontrolü yap
            print(Fore.YELLOW + Style.BRIGHT + 
                 f"[!] Klasör kullanımda olabilir, prosesler kontrol ediliyor..." + Fore.RESET)
            
            # Klasördeki dosyaları kullanan prosesleri bul ve sonlandır
            processes_found = False
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if ProcessUtils.terminate_processes_using_file(file_path):
                        processes_found = True
            
            if processes_found:
                sleep(2)  # Proseslerin kapanması için bekle
                
            # Tekrar dene
            try:
                shutil.rmtree(dir_path)
                print(Fore.GREEN + Style.BRIGHT + f"[✓] Klasör silindi: {dir_path}" + Fore.RESET)
                return True
            except Exception as e:
                print(Fore.RED + Style.BRIGHT + 
                     f"[✗] Klasör silinemedi: {dir_path} ({e})" + Fore.RESET)
                return False
                
        except Exception as e:
            print(Fore.RED + Style.BRIGHT + 
                 f"[✗] Klasör silinemedi: {dir_path} ({e})" + Fore.RESET)
            return False

    @staticmethod
    def delete_items(directories: Optional[List[str]] = None, files: Optional[List[str]] = None):
        """Dosya/klasör silme - Geliştirilmiş versiyon"""
        disks, method = DiskUtils.select_disks()
        failed = []
        success_count = 0
        
        print(Fore.CYAN + Style.BRIGHT + 
             "[!] UYARI: Bu işlem dosyaları kalıcı olarak silecektir!" + Fore.RESET)
        confirm = input(Fore.CYAN + Style.BRIGHT + 
                       "[?] Devam etmek istiyor musunuz? (e/h): " + Fore.RESET).lower()
        
        if confirm != 'e':
            print(Fore.YELLOW + Style.BRIGHT + "[!] İşlem iptal edildi." + Fore.RESET)
            sleep(1)
            return
        
        for disk in disks:
            print(Fore.MAGENTA + Style.BRIGHT + f"\n[~] {disk} taranıyor..." + Fore.RESET)
            
            try:
                for root, dirs, file_list in os.walk(disk, topdown=False):
                    try:
                        if directories:
                            for directory in directories:
                                lower_dir = directory.lower()
                                lower_root = root.lower()
                                base_name = os.path.basename(root).lower()
                                
                                match = False
                                if method == "b" and lower_dir in lower_root:
                                    match = True
                                elif method == "k" and lower_dir == base_name:
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
                                    if method == "b" and lower_search in lower_file:
                                        match = True
                                    elif method == "k" and lower_search == lower_file:
                                        match = True
                                    
                                    if match:
                                        full_path = os.path.join(root, file_name)
                                        if FileDeleter.safe_delete_file(full_path):
                                            success_count += 1
                                        else:
                                            failed.append(full_path)
                    
                    except Exception as e:
                        print(Fore.YELLOW + Style.BRIGHT + 
                             f"[!] {root} işlenirken hata: {e}" + Fore.RESET)
                        
            except Exception as e:
                print(Fore.RED + Style.BRIGHT + 
                     f"[✗] {disk} taranırken hata: {e}" + Fore.RESET)

        # Sonuçları göster
        print(Fore.GREEN + Style.BRIGHT + f"\n[✓] Başarıyla silinen: {success_count}" + Fore.RESET)
        
        if failed:
            print(Fore.RED + Style.BRIGHT + f"\n[!] İşlem yapılamayanlar ({len(failed)}):" + Fore.RESET)
            for item in failed[:10]:
                print(Fore.RED + Style.BRIGHT + f"[✗] {item}" + Fore.RESET)
            if len(failed) > 10:
                print(Fore.YELLOW + Style.BRIGHT + 
                     f"[!] ... ve {len(failed) - 10} daha fazla" + Fore.RESET)
        
        input(Fore.YELLOW + Style.BRIGHT + "\n[+] Devam etmek için Enter'a basın..." + Fore.RESET)

def main():
    """Ana uygulama"""
    init(autoreset=True)
    
    # Admin yetkilerini kontrol et
    FileUtils.ensure_admin()
    FileUtils.show_banner()
    
    while True:
        FileUtils.clear_screen()
        print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "\n[1] Finder - Dosya / Klasör Bul")
        print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[2] Deleter - Dosya / Klasör Sil")
        
        if FileUtils.is_windows():
            print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[3] Registry Scanner - Kayıt Defteri Tara")
        if FileUtils.is_windows():
            print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[4] Process Killer - Proses Sonlandır")
        else:
            print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[3] Process Killer - Proses Sonlandır")
            
        print(Fore.LIGHTBLUE_EX + Style.BRIGHT + "[0] Çıkış" + Fore.RESET)
        
        choice = input(Fore.CYAN + Style.BRIGHT + "[>] Seçiminiz: " + Fore.RESET).strip()
        
        if choice == "1":
            FileUtils.clear_screen()
            search_type = input(Fore.CYAN + Style.BRIGHT + 
                               "[?] [d] Klasör / [f] Dosya / [e] Uzantı: " + Fore.RESET).lower()
            
            if search_type == "d":
                terms = input(Fore.CYAN + Style.BRIGHT + 
                             "[>] Kelimeleri girin (virgülle ayırın): " + Fore.RESET).split(",")
                FileFinder.find_files(directories=[x.strip() for x in terms])
            
            elif search_type == "f":
                terms = input(Fore.CYAN + Style.BRIGHT + 
                             "[>] Kelimeleri girin (virgülle ayırın): " + Fore.RESET).split(",")
                FileFinder.find_files(files=[x.strip() for x in terms])
            
            elif search_type == "e":
                terms = input(Fore.CYAN + Style.BRIGHT + 
                             "[>] Uzantıları girin (virgülle ayırın, nokta ile): " + Fore.RESET).split(",")
                FileFinder.find_files(extensions=[x.strip() for x in terms])
        
        elif choice == "2":
            FileUtils.clear_screen()
            delete_type = input(Fore.CYAN + Style.BRIGHT + 
                               "[?] [d] Klasör / [f] Dosya: " + Fore.RESET).lower()
            
            if delete_type == "d":
                terms = input(Fore.CYAN + Style.BRIGHT + 
                             "[>] Kelimeleri girin (virgülle ayırın): " + Fore.RESET).split(",")
                FileDeleter.delete_items(directories=[x.strip() for x in terms])
            
            elif delete_type == "f":
                terms = input(Fore.CYAN + Style.BRIGHT + 
                             "[>] Kelimeleri girin (virgülle ayırın): " + Fore.RESET).split(",")
                FileDeleter.delete_items(files=[x.strip() for x in terms])
        
        elif choice == "3" and FileUtils.is_windows():
            FileUtils.clear_screen()
            key = input(Fore.CYAN + Style.BRIGHT + 
                       "[>] Registry anahtar kelimesi: " + Fore.RESET).strip()
            if key:
                RegistryUtils.search_registry(key)
        
        elif choice == "4" and FileUtils.is_windows():
            FileUtils.clear_screen()
            process_name = input(Fore.CYAN + Style.BRIGHT + 
                                "[>] Sonlandırılacak proses adı: " + Fore.RESET).strip()
            if process_name:
                FileUtils.terminate_process(process_name)
                input(Fore.YELLOW + Style.BRIGHT + 
                     "\n[+] Devam etmek için Enter'a basın..." + Fore.RESET)
        
        elif choice == "3":
            FileUtils.clear_screen()
            process_name = input(Fore.CYAN + Style.BRIGHT + 
                                "[>] Sonlandırılacak proses adı: " + Fore.RESET).strip()
            if process_name:
                FileUtils.terminate_process(process_name)
                input(Fore.YELLOW + Style.BRIGHT + 
                     "\n[+] Devam etmek için Enter'a basın..." + Fore.RESET)
                
                
        elif choice == "0":
            print(Fore.LIGHTMAGENTA_EX + Style.BRIGHT + "\n[+] Çıkış yapılıyor..." + Fore.RESET)
            sleep(1)
            break
        
        else:
            print(Fore.RED + Style.BRIGHT + "[!] Geçersiz seçim!" + Fore.RESET)
            sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.YELLOW + Style.BRIGHT + "\n[!] Kullanıcı tarafından durduruldu!" + Fore.RESET)
        sys.exit(0)
    except Exception as e:
        print(Fore.RED + Style.BRIGHT + f"[✗] Beklenmeyen hata: {e}" + Fore.RESET)
        sys.exit(1)