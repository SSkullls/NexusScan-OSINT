import socket
import threading
import sys
import requests
import json
from queue import Queue
from colorama import Fore, Style, init

# Initialize terminal colors
init(autoreset=True)

class NexusScanFramework:
    def __init__(self):
        # Professional Metadata Embedded for the GitHub CD Release
        self.AUTHOR = "SSkullls"
        self.VERSION = "1.0.0-CD_EDITION"
        
        self.print_lock = threading.Lock()
        self.port_queue = Queue()
        self.subdomain_queue = Queue()
        
        self.common_ports = [21, 22, 23, 25, 53, 80, 110, 139, 443, 445, 1433, 3306, 3389, 8080, 8443]
        self.common_subdomains = ["www", "mail", "remote", "blog", "webmail", "server", "ns1", "ns2", "smtp", "secure", "vpn", "api", "dev", "staging", "admin"]
        self.SHODAN_API_KEY = "" 

    def banner(self):
        print(f"{Fore.MAGENTA}{Style.BRIGHT}" + "="*65)
        print(f"{Fore.CYAN}{Style.BRIGHT}  NEXUSSCAN-OSINT : THE CD-ROM SPECIAL FRAMEWORK  ")
        print(f"{Fore.GREEN}  DEVELOPED BY CORE AUTHOR: {Fore.YELLOW}{self.AUTHOR} {Fore.DIM}(v{self.VERSION})")
        print(f"{Fore.MAGENTA}{Style.BRIGHT}" + "="*65 + "\n")

    def log_success(self, message):
        with self.print_lock:
            print(f"[{Fore.GREEN}✓{Style.RESET_ALL}] {message}")

    def log_info(self, message):
        with self.print_lock:
            print(f"[{Fore.BLUE}*{Style.RESET_ALL}] {message}")

    def log_alert(self, message):
        with self.print_lock:
            print(f"[{Fore.YELLOW}!{Style.RESET_ALL}] {Fore.YELLOW}{message}")

    def fetch_shodan_intel(self, target_ip):
        if not self.SHODAN_API_KEY:
            self.log_alert("Shodan API key omitted. Skipping cloud-recon layer.")
            return
            
        self.log_info(f"Querying Shodan Threat Intel for IP: {target_ip}...")
        url = f"https://shodan.io{target_ip}?key={self.SHODAN_API_KEY}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_success(f"Organization: {data.get('org', 'N/A')}")
                self.log_success(f"Operating System: {data.get('os', 'N/A')}")
                if 'vulns' in data:
                    self.log_alert(f"Known Vulnerabilities Found: {', '.join(data['vulns'])}")
            else:
                self.log_alert("Shodan returned no public data for this IP.")
        except Exception as e:
            self.log_alert(f"Threat Intelligence pipeline down: {str(e)}")

    def subdomain_worker(self, target_domain):
        while not self.subdomain_queue.empty():
            sub = self.subdomain_queue.get()
            url = f"http://{sub}.{target_domain}"
            try:
                res = requests.get(url, timeout=2, allow_redirects=True)
                server_header = res.headers.get('Server', 'Unknown Web Server')
                self.log_success(f"Host Discovered: {Fore.CYAN}{url}{Style.RESET_ALL} | Status: {res.status_code} ({server_header})")
            except requests.RequestException:
                pass
            finally:
                self.subdomain_queue.task_done()

    def port_worker(self, target_ip):
        while not self.port_queue.empty():
            port = self.port_queue.get()
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1.0)
                result = s.connect_ex((target_ip, port))
                if result == 0:
                    try:
                        s.sendall(b"HEAD / HTTP/1.1\r\n\r\n")
                        banner = s.recv(1024).decode('utf-8', errors='ignore').strip().split('\n')[0]
                    except:
                        banner = "Active Connection TCP"
                    self.log_success(f"Port Open: {Fore.YELLOW}{port}{Style.RESET_ALL} -> {Fore.DIM}{banner[:60]}")
                s.close()
            except Exception:
                pass
            finally:
                self.port_queue.task_done()

    def execute(self):
        self.banner()
        target = input(f"{Fore.WHITE}Target Domain or IP Address: {Style.RESET_ALL}").strip()
        if not target:
            print(f"{Fore.RED}Invalid Target Host.")
            return

        try:
            target_ip = socket.gethostbyname(target)
            self.log_info(f"Target Resolved to Base IP Target: {Fore.GREEN}{target_ip}")
        except socket.gaierror:
            self.log_alert("Could not map host directly to IP address. Scanning purely via domain context.")
            target_ip = None

        if target_ip:
            print("")
            self.fetch_shodan_intel(target_ip)

        print(f"\n{Fore.BLUE}[*] Stage 2: Deploying Subdomain Mapping Engine...")
        for sub in self.common_subdomains:
            self.subdomain_queue.put(sub)
        
        for _ in range(8):
            t = threading.Thread(target=self.subdomain_worker, args=(target,))
            t.daemon = True
            t.start()
        self.subdomain_queue.join()

        if target_ip:
            print(f"\n{Fore.BLUE}[*] Stage 3: Launching Deep Port Scanner Engine...")
            for port in self.common_ports:
                self.port_queue.put(port)
            
            for _ in range(10):
                t = threading.Thread(target=self.port_worker, args=(target_ip,))
                t.daemon = True
                t.start()
            self.port_queue.join()

        print(f"\n{Fore.GREEN}{Style.BRIGHT}================ Framework Run Finished ================")

if __name__ == "__main__":
    try:
        engine = NexusScanFramework()
        engine.execute()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Operations cleanly suspended by Administrator.")
        sys.exit()
