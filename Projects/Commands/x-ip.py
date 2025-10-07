#!/usr/bin/env python3
"""Get local and public IP addresses with optional geolocation information."""
from xulbux import FormatCodes, Console, Data
from typing import Optional
import subprocess
import socket
import json
import re


ARGS = Console.get_args({
    "geo": ["-g", "--geo", "--location"],
    "provider": {"flags": ["-p", "--provider"], "default": "ipify"},
    "json_output": ["-j", "--json"],
    "help": ["-h", "--help"],
})


def print_help():
    help_text = """
[b|in]( IP Info - Get local and public IP addresses with geolocation )

[b](Usage:) [br:green](x-ip) [br:blue]([options])

[b](Options:)
  [br:blue](-g), [br:blue](--geo)              Show geolocation info for public IP
  [br:blue](-p), [br:blue](--provider NAME)    Use specific IP provider [dim]((ipify, ipapi, icanhazip))
  [br:blue](-j), [br:blue](--json)             Output in JSON format

[b](Examples:)
  [br:green](x-ip)                   [dim](# [i](Show basic IP info))
  [br:green](x-ip) [br:blue](--geo)             [dim](# [i](Show IP with location))
  [br:green](x-ip) [br:blue](--json)            [dim](# [i](Output as JSON))
"""
    FormatCodes.print(help_text)


class IPInfo:

    def __init__(self):
        self.local_ipv4: Optional[str] = None
        self.local_ipv6: Optional[str] = None
        self.public_ipv4: Optional[str] = None
        self.public_ipv6: Optional[str] = None
        self.all_interfaces: dict[str, dict[str, str]] = {}
        self.geo_info: Optional[dict] = None

    def _get_local_ip(self) -> Optional[str]:
        """Get primary local IPv4 address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.1)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return None

    def _get_local_ipv6(self) -> Optional[str]:
        """Get local IPv6 address."""
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            s.settimeout(0.1)
            s.connect(("2001:4860:4860::8888", 80))  # GOOGLE DNS IPv6
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return None

    def _get_all_interfaces(self) -> dict[str, dict[str, str]]:
        """Get all network interfaces and their IPs."""
        interfaces = {}
        try:
            import netifaces  # type: ignore[import]

            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                interface_info = {}
                # IPv4
                if netifaces.AF_INET in addrs:
                    ipv4_info = addrs[netifaces.AF_INET][0]
                    interface_info["ipv4"] = ipv4_info.get("addr", "N/A")
                    if "netmask" in ipv4_info:
                        interface_info["subnet_mask"] = ipv4_info["netmask"]
                # IPv6
                if netifaces.AF_INET6 in addrs:
                    ipv6_info = addrs[netifaces.AF_INET6][0]
                    ipv6_addr = ipv6_info.get("addr", "N/A")
                    ipv6_addr = ipv6_addr.split("%")[0]
                    interface_info["ipv6"] = ipv6_addr

                # GET GATEWAY INFORMATION
                try:
                    gateways = netifaces.gateways()
                    if 'default' in gateways and netifaces.AF_INET in gateways['default']:
                        default_gateway_info = gateways['default'][netifaces.AF_INET]
                        if len(default_gateway_info) >= 2 and default_gateway_info[1] == interface:
                            interface_info["gateway"] = default_gateway_info[0]
                except Exception:
                    pass

                if interface_info:
                    interfaces[interface] = interface_info

            return interfaces
        except ImportError:
            return self._get_interfaces_fallback()

    def _get_interfaces_fallback(self) -> dict[str, dict[str, str]]:
        """Fallback method to get interfaces using system commands."""
        interfaces = {}

        try:
            result = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                current_interface = None
                for line in result.stdout.split("\n"):
                    line = line.strip()

                    # CHECK IF THIS LINE DEFINES A NEW INTERFACE
                    if ("adapter" in line or "configuration" in line) and line.endswith(":"):
                        interface_name = line.rstrip(":")
                        interface_name = re.sub(
                            r"^(Ethernet adapter|Wireless LAN adapter|Unknown adapter)\s*", "", interface_name
                        )
                        if interface_name and interface_name != "Windows IP Configuration":
                            current_interface = interface_name
                            interfaces[current_interface] = {}

                    # EXTRACT IPv4 ADDRESS
                    elif "IPv4 Address" in line and current_interface:
                        match = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
                        if match:
                            interfaces[current_interface]["ipv4"] = match.group(1)

                    # EXTRACT SUBNET MASK
                    elif "Subnet Mask" in line and current_interface:
                        match = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
                        if match:
                            interfaces[current_interface]["subnet_mask"] = match.group(1)

                    # EXTRACT DEFAULT GATEWAY
                    elif "Default Gateway" in line and current_interface:
                        match = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
                        if match:
                            interfaces[current_interface]["gateway"] = match.group(1)

                    # EXTRACT DNS SUFFIX
                    elif "Connection-specific DNS Suffix" in line and current_interface:
                        match = re.search(r":\s+(.+)", line)
                        if match:
                            dns_suffix = match.group(1).strip()
                            if dns_suffix:
                                interfaces[current_interface]["dns_suffix"] = dns_suffix

                    # EXTRACT IPv6 ADDRESS
                    elif ("IPv6 Address" in line or "Link-local IPv6 Address" in line) and current_interface:
                        match = re.search(r":\s+([0-9a-fA-F:]+)", line)
                        if match:
                            ipv6_addr = match.group(1).split("%")[0]
                            if ":" in ipv6_addr and len(ipv6_addr) > 5:
                                interfaces[current_interface]["ipv6"] = ipv6_addr

                    # EXTRACT MEDIA STATE (FOR DISCONNECTED INTERFACES)
                    elif "Media State" in line and current_interface:
                        if "disconnected" in line.lower():
                            interfaces[current_interface]["status"] = "Disconnected"

                # REMOVE INTERFACES WITH NO IP ADDRESSES (BUT KEEP DISCONNECTED ONES FOR STATUS INFO)
                interfaces = {
                    name: addrs
                    for name, addrs in interfaces.items()
                    if addrs and (any(key in addrs for key in ["ipv4", "ipv6"]) or "status" in addrs)
                }

        except Exception:
            pass

        return interfaces

    def _get_public_ip(self, provider: str = "ipify", ipv6: bool = False) -> Optional[str]:
        """Get public IP address from various providers."""
        providers = {
            "ipify": f"https://api{'64' if ipv6 else ''}.ipify.org?format=text",
            "icanhazip": f"https://{'ipv6.' if ipv6 else ''}icanhazip.com",
            "ipapi": "https://ipapi.co/ip/",
        }

        url = providers.get(provider.lower(), providers["ipify"])

        try:
            import urllib.request
            with urllib.request.urlopen(url, timeout=5) as response:
                ip = response.read().decode("utf-8").strip()
                return ip if ip else None
        except Exception:
            return None

    def _get_geolocation(self, ip: str) -> Optional[dict]:
        """Get geolocation information for an IP address."""
        try:
            import urllib.request
            url = f"https://ipapi.co/{ip}/json/"

            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                if "error" in data:
                    return None
                return {
                    "ip": data.get("ip"),
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country_name"),
                    "country_code": data.get("country_code"),
                    "postal": data.get("postal"),
                    "lat": data.get("lat"),
                    "lng": data.get("lng"),
                    "timezone": data.get("timezone"),
                    "org": data.get("org"),
                    "asn": data.get("asn"),
                }
        except Exception:
            return None

    def gather_info(self, provider: str = "ipify", get_geo: bool = False) -> None:
        """Gather all IP information."""
        Console.info("Gathering IP information...", start="\n")
        self.local_ipv4 = self._get_local_ip()
        self.local_ipv6 = self._get_local_ipv6()
        self.public_ipv4 = self._get_public_ip(provider, ipv6=False)
        self.public_ipv6 = self._get_public_ip(provider, ipv6=True)
        self.all_interfaces = self._get_all_interfaces()
        if get_geo and self.public_ipv4:
            Console.info("Fetching geolocation data...")
            self.geo_info = self._get_geolocation(self.public_ipv4)

    def to_dict(self) -> dict:
        """Convert IP info to dictionary."""
        result = {"local": {}, "public": {}}
        if self.local_ipv4:
            result["local"]["ipv4"] = self.local_ipv4
        if self.local_ipv6:
            result["local"]["ipv6"] = self.local_ipv6
        if self.public_ipv4:
            result["public"]["ipv4"] = self.public_ipv4
        if self.public_ipv6:
            result["public"]["ipv6"] = self.public_ipv6
        if self.all_interfaces:
            result["interfaces"] = self.all_interfaces
        if self.geo_info:
            result["geolocation"] = self.geo_info
        return result

    def display(self) -> None:
        """Display IP information in formatted output."""
        print()

        FormatCodes.print("\n[b|br:cyan](Local IP Addresses)")
        local_ips_text = []
        if self.local_ipv4:
            local_ips_text.append(f"[b](IPv4:) [white]({self.local_ipv4})")
        else:
            local_ips_text.append(f"[b](IPv4:) [dim|white](Not Found)")
        if self.local_ipv6:
            local_ips_text.append(f"[b](IPv6:) [white]({self.local_ipv6})")
        else:
            local_ips_text.append(f"[b](IPv6:) [dim|white](Not Found)")
        Console.log_box_bordered(*local_ips_text, border_style=f"br:cyan")

        FormatCodes.print("\n[b|br:magenta](Public IP Addresses)")
        public_ips_text = []
        if self.public_ipv4:
            public_ips_text.append(f"[b](IPv4:) [white]({self.public_ipv4})")
        else:
            public_ips_text.append(f"[b](IPv4:) [dim|white](Not Found)")
        if self.public_ipv6:
            public_ips_text.append(f"[b](IPv6:) [white]({self.public_ipv6})")
        else:
            public_ips_text.append(f"[b](IPv6:) [dim|white](Not Found)")
        Console.log_box_bordered(*public_ips_text, border_style=f"br:magenta")

        if self.all_interfaces:
            FormatCodes.print("\n[b|br:yellow](All Network Interfaces)")
            interfaces_text, i = [], 0
            for interface, addrs in self.all_interfaces.items():
                interfaces_text.append(f"{'{hr}' if i > 0 else ''}[b|br:yellow]({interface})")
                # SHOW CONNECTION STATUS IF DISCONNECTED
                if "status" in addrs:
                    interfaces_text.append(f"[b](Status:) [dim|white]({addrs['status']})")
                # IPv4 INFO
                if "ipv4" in addrs:
                    interfaces_text.append(f"[b](IPv4:) [white]({addrs['ipv4']})")
                    if "subnet_mask" in addrs:
                        interfaces_text.append(f"[b](Subnet:) [white]({addrs['subnet_mask']})")
                    if "gateway" in addrs:
                        interfaces_text.append(f"[b](Gateway:) [white]({addrs['gateway']})")
                # IPv6 INFO
                if "ipv6" in addrs:
                    interfaces_text.append(f"[b](IPv6:) [white]({addrs['ipv6']})")
                # DNS SUFFIX
                if "dns_suffix" in addrs:
                    interfaces_text.append(f"[b](DNS Suffix:) [white]({addrs['dns_suffix']})")
                i += 1
            Console.log_box_bordered(*interfaces_text, border_style="br:yellow")

        if self.geo_info:
            geo = self.geo_info
            geo_text = []
            if geo.get("city") or geo.get("region"):
                location = f"{geo.get('city', '')}, {geo.get('region', '')}".strip(", ")
                geo_text.append(f"[b](Location:) [white]({location})")
            if geo.get("country"):
                geo_text.append(f"[b](Country:) [white]{geo['country']} ({geo.get('country_code', '')})[_c]")
            if geo.get("postal"):
                geo_text.append(f"[b](Postal:) [white]{geo['postal']}[_c]")
            if geo.get("timezone"):
                geo_text.append(f"[b](Timezone:) [white]{geo['timezone']}[_c]")
            if geo.get("lat") and geo.get("lng"):
                geo_text.append(f"[b](Coordinates:) [white]{geo['lat']}, {geo['lng']}[_c]")
            if geo.get("org"):
                geo_text.append(f"[b](ISP:) [white]{geo['org']}[_c]")
            if geo.get("asn"):
                geo_text.append(f"[b](ASN:) [white]{geo['asn']}[_c]")
            FormatCodes.print("\n[b|br:blue](Geolocation Information)")
            Console.log_box_bordered(*geo_text, border_style=f"br:blue")

        print()


def main() -> None:
    if ARGS.help.exists:
        print_help()
        return

    ip_info = IPInfo()

    try:
        ip_info.gather_info(provider=ARGS.provider.value, get_geo=ARGS.geo.exists)
    except Exception as e:
        Console.fail(f"Error gathering IP information: {e}", end="\n\n")
        return

    if ARGS.json_output.exists:
        print()
        Data.print(ip_info.to_dict(), indent=2, as_json=True)
        print()
    else:
        ip_info.display()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
