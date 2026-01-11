#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""Get detailed hardware information about your PC."""
from xulbux import FormatCodes, Console, Data
from typing import Optional, TYPE_CHECKING
import subprocess
import platform
import re

if TYPE_CHECKING:
    import psutil

# CHECK IF PSUTIL IS AVAILABLE (MAY FAIL ON PYTHON 3.14)
PSUTIL_AVAILABLE = False
PSUTIL_ERROR = None
try:
    import psutil
    PSUTIL_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    PSUTIL_ERROR = str(e)

ARGS = Console.get_args(
    detailed={"-d", "--detailed"},
    json_output={"-j", "--json"},
    help={"-h", "--help"},
)


def print_help():
    help_text = """
[b|in|bg:black]( Hardware Info - Get detailed hardware information about your PC )

[b](Usage:) [br:green](x-hw) [br:blue]([options])

[b](Options:)
  [br:blue](-d), [br:blue](--detailed)         Show detailed hardware information
  [br:blue](-j), [br:blue](--json)             Output in JSON format

[b](Examples:)
  [br:green](x-hw)                   [dim](# [i](Show basic hardware info))
  [br:green](x-hw) [br:blue](--detailed)        [dim](# [i](Show detailed info))
  [br:green](x-hw) [br:blue](--json)            [dim](# [i](Output as JSON))
"""
    FormatCodes.print(help_text)


class HardwareInfo:

    def __init__(self):
        self.system: dict = {}
        self.cpu: dict = {}
        self.memory: dict = {}
        self.disk: dict = {}
        self.gpu: dict = {}
        self.network: dict = {}
        self.battery: dict = {}

    def _get_system_info(self) -> dict:
        """Get basic system information."""
        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "platform": platform.platform(),
        }
        return info

    def _get_cpu_info(self, detailed: bool = False) -> dict:
        """Get CPU information."""
        info = {
            "processor": platform.processor(),
            "physical_cores": None,
            "logical_cores": None,
            "frequency": None,
            "max_frequency": None,
            "cpu_usage": None,
        }

        if PSUTIL_AVAILABLE:
            info["physical_cores"] = psutil.cpu_count(logical=False)
            info["logical_cores"] = psutil.cpu_count(logical=True)

            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                info["frequency"] = f"{cpu_freq.current:.2f} MHz"
                info["max_frequency"] = f"{cpu_freq.max:.2f} MHz"

            info["cpu_usage"] = f"{psutil.cpu_percent(interval=1)}%"

            if detailed:
                info["per_core_usage"] = [f"{x}%" for x in psutil.cpu_percent(interval=1, percpu=True)]

        return info

    def _get_memory_info(self, detailed: bool = False) -> dict:
        """Get memory information."""
        info: dict[str, Optional[str]] = {
            "total": None,
            "available": None,
            "used": None,
            "usage_percent": None,
        }

        if PSUTIL_AVAILABLE:
            mem = psutil.virtual_memory()
            info["total"] = self._format_bytes(mem.total)
            info["available"] = self._format_bytes(mem.available)
            info["used"] = self._format_bytes(mem.used)
            info["usage_percent"] = f"{mem.percent}%"

            if detailed:
                swap = psutil.swap_memory()
                info["swap_total"] = self._format_bytes(swap.total)
                info["swap_used"] = self._format_bytes(swap.used)
                info["swap_percent"] = f"{swap.percent}%"

        return info

    def _get_disk_info(self, detailed: bool = False) -> dict:
        """Get disk information."""
        info = {
            "partitions": [],
            "total_size": None,
            "total_used": None,
            "total_free": None,
        }

        if PSUTIL_AVAILABLE:
            partitions = psutil.disk_partitions()

            total_size = 0
            total_used = 0
            total_free = 0

            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partition_info = {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "filesystem": partition.fstype,
                        "total": self._format_bytes(usage.total),
                        "used": self._format_bytes(usage.used),
                        "free": self._format_bytes(usage.free),
                        "usage_percent": f"{usage.percent}%",
                    }

                    total_size += usage.total
                    total_used += usage.used
                    total_free += usage.free

                    info["partitions"].append(partition_info)
                except (PermissionError, OSError):
                    continue

            info["total_size"] = self._format_bytes(total_size)
            info["total_used"] = self._format_bytes(total_used)
            info["total_free"] = self._format_bytes(total_free)

            if not detailed:
                # IN NON-DETAILED MODE, ONLY SHOW SUMMARY
                info["partitions"] = []

        return info

    def _get_gpu_info(self) -> dict:
        """Get GPU information."""
        info = {
            "gpus": [],
        }

        system = platform.system()

        if system == "Windows":
            try:
                result = subprocess.run(["wmic", "path", "win32_VideoController", "get", "name"],
                                        capture_output=True,
                                        text=True,
                                        timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")[1:]
                    for line in lines:
                        gpu_name = line.strip()
                        if gpu_name:
                            info["gpus"].append({"name": gpu_name})
            except Exception:
                pass

        elif system == "Linux":
            try:
                # TRY 'lspci' FOR GPU INFO
                result = subprocess.run(["lspci"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split("\n"):
                        if "VGA" in line or "3D" in line or "Display" in line:
                            match = re.search(r": (.+)$", line)
                            if match:
                                info["gpus"].append({"name": match.group(1).strip()})
            except Exception:
                pass

        elif system == "Darwin":  # macOS
            try:
                result = subprocess.run(["system_profiler", "SPDisplaysDataType"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.split("\n")
                    for line in lines:
                        if "Chipset Model:" in line:
                            gpu_name = line.split(":", 1)[1].strip()
                            info["gpus"].append({"name": gpu_name})
            except Exception:
                pass

        return info

    def _get_network_info(self) -> dict:
        """Get network adapter information."""
        info = {
            "adapters": [],
        }

        if PSUTIL_AVAILABLE:
            stats = psutil.net_if_stats()
            addrs = psutil.net_if_addrs()

            for interface_name in stats:
                if interface_name in addrs:
                    adapter_info = {
                        "name": interface_name,
                        "is_up": stats[interface_name].isup,
                        "speed": f"{stats[interface_name].speed} Mbps" if stats[interface_name].speed > 0 else "Unknown",
                    }

                    # GET MAC ADDRESS
                    for addr in addrs[interface_name]:
                        if addr.family.name == 'AF_LINK' or addr.family.name == 'AF_PACKET':
                            adapter_info["mac"] = addr.address
                            break

                    info["adapters"].append(adapter_info)

        return info

    def _get_battery_info(self) -> dict:
        """Get battery information (for laptops)."""
        info = {
            "has_battery": False,
            "percent": None,
            "power_plugged": None,
            "time_left": None,
        }

        if PSUTIL_AVAILABLE:
            try:
                battery = psutil.sensors_battery()
                if battery:
                    info["has_battery"] = True
                    info["percent"] = f"{battery.percent}%"
                    info["power_plugged"] = battery.power_plugged
                    if battery.secsleft != psutil.POWER_TIME_UNLIMITED and battery.secsleft > 0:
                        hours = battery.secsleft // 3600
                        minutes = (battery.secsleft % 3600) // 60
                        info["time_left"] = f"{hours}h {minutes}m"
            except AttributeError:
                pass

        return info

    def _format_bytes(self, bytes_value: float) -> str:
        """Format bytes to human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"

    def gather_info(self, detailed: bool = False) -> None:
        """Gather all hardware information."""
        if not PSUTIL_AVAILABLE:
            FormatCodes.print(
                "\n[br:yellow][b](⚠ Library psutil failed to initialize - some hardware info will be missing!)"
                "\n  [dim](This is likely due to incompatibility with your Python version.)[_c]\n"
            )
        Console.info("Gathering hardware information...", start="\n")
        self.system = self._get_system_info()
        self.cpu = self._get_cpu_info(detailed)
        self.memory = self._get_memory_info(detailed)
        self.disk = self._get_disk_info(detailed)
        self.gpu = self._get_gpu_info()
        self.network = self._get_network_info()
        self.battery = self._get_battery_info()

    def to_dict(self) -> dict:
        """Convert hardware info to dictionary."""
        result = {}
        if self.system:
            result["system"] = self.system
        if self.cpu:
            result["cpu"] = self.cpu
        if self.memory:
            result["memory"] = self.memory
        if self.disk:
            result["disk"] = self.disk
        if self.gpu:
            result["gpu"] = self.gpu
        if self.network:
            result["network"] = self.network
        if self.battery and self.battery.get("has_battery"):
            result["battery"] = self.battery
        return result

    def display(self) -> None:
        """Display hardware information in formatted output."""
        print()

        # SYSTEM INFO
        if self.system:
            FormatCodes.print("\n[b|br:green](System Information)")
            system_text = []
            if self.system.get("os"):
                system_text.append(f"          [b](OS) : [br:white]({self.system['os']} {self.system.get('os_release', '')})")
            if self.system.get("os_version"):
                system_text.append(f"     [b](Version) : [br:white]({self.system['os_version']})")
            if self.system.get("architecture"):
                system_text.append(f"[b](Architecture) : [br:white]({self.system['architecture']})")
            if self.system.get("hostname"):
                system_text.append(f"    [b](Hostname) : [br:white]({self.system['hostname']})")
            Console.log_box_bordered(*system_text, border_style="br:green")

        # CPU INFO
        if self.cpu:
            FormatCodes.print("\n[b|br:cyan](CPU Information)")
            cpu_text = []
            if self.cpu.get("processor"):
                cpu_text.append(f"{'     ' if PSUTIL_AVAILABLE else ''}[b](Processor) : [br:white]({self.cpu['processor']})")
            if self.cpu.get("physical_cores"):
                cpu_text.append(f"[b](Physical Cores) : [br:white]({self.cpu['physical_cores']})")
            if self.cpu.get("logical_cores"):
                cpu_text.append(f" [b](Logical Cores) : [br:white]({self.cpu['logical_cores']})")
            if self.cpu.get("frequency"):
                cpu_text.append(f"     [b](Frequency) : [br:white]({self.cpu['frequency']})")
            if self.cpu.get("max_frequency"):
                cpu_text.append(f" [b](Max Frequency) : [br:white]({self.cpu['max_frequency']})")
            if self.cpu.get("cpu_usage"):
                cpu_text.append(f"     [b](CPU Usage) : [br:white]({self.cpu['cpu_usage']})")
            if self.cpu.get("per_core_usage"):
                cpu_text.append("{hr}")
                cores = self.cpu['per_core_usage']
                formatted_cores = []
                for i in range(0, len(cores), 10):
                    formatted_cores.append('[br:white]' + ', '.join(cores[i:i + 10]))
                cpu_text.append(f"[b|br:cyan](Per-Core Usage)\n" + '\n'.join(formatted_cores) + "[_c]")
            Console.log_box_bordered(*cpu_text, border_style="br:cyan")

        # GPU INFO
        if self.gpu and self.gpu.get("gpus"):
            FormatCodes.print("\n[b|br:blue](GPU Information)")
            gpu_text = []
            for i, gpu in enumerate(self.gpu["gpus"]):
                if i > 0:
                    gpu_text.append("{hr}")
                gpu_text.append(f"[b](GPU {i + 1}) : [br:white]({gpu['name']})")
            Console.log_box_bordered(*gpu_text, border_style="br:blue")

        # MEMORY INFO
        if self.memory:
            FormatCodes.print("\n[b|magenta](Memory Information)")
            mem_text = []
            if self.memory.get("total"):
                mem_text.append(f"     [b](Total) : [br:white]({self.memory['total']})")
            if self.memory.get("available"):
                mem_text.append(f" [b](Available) : [br:white]({self.memory['available']})")
            if self.memory.get("used"):
                mem_text.append(f"      [b](Used) : [br:white]({self.memory['used']})")
            if self.memory.get("usage_percent"):
                mem_text.append(f"     [b](Usage) : [br:white]({self.memory['usage_percent']})")
            if self.memory.get("swap_total"):
                mem_text.append(f"[b](Swap Total) : [br:white]({self.memory['swap_total']})")
            if self.memory.get("swap_used"):
                mem_text.append(f" [b](Swap Used) : [br:white]({self.memory['swap_used']})")
            if self.memory.get("swap_percent"):
                mem_text.append(f"[b](Swap Usage) : [br:white]({self.memory['swap_percent']})")
            Console.log_box_bordered(*mem_text, border_style="magenta")

        # DISK INFO
        if self.disk:
            FormatCodes.print("\n[b|br:magenta](Disk Information)")
            disk_text = []
            if self.disk.get("total_size"):
                disk_text.append(f"[b](Total Size) : [br:white]({self.disk['total_size']})")
            if self.disk.get("total_used"):
                disk_text.append(f"[b](Total Used) : [br:white]({self.disk['total_used']})")
            if self.disk.get("total_free"):
                disk_text.append(f"[b](Total Free) : [br:white]({self.disk['total_free']})")

            if self.disk.get("partitions"):
                for i, partition in enumerate(self.disk["partitions"]):
                    disk_text.append("{hr}")
                    disk_text.append(f"[b|br:magenta]({partition['device']})")
                    disk_text.append(f"     [b](Mount) : [br:white]({partition['mountpoint']})")
                    disk_text.append(f"[b](Filesystem) : [br:white]({partition['filesystem']})")
                    disk_text.append(f"     [b](Total) : [br:white]({partition['total']})")
                    disk_text.append(f"      [b](Used) : [br:white]({partition['used']})")
                    disk_text.append(f"      [b](Free) : [br:white]({partition['free']})")
                    disk_text.append(f"     [b](Usage) : [br:white]({partition['usage_percent']})")

            Console.log_box_bordered(*disk_text, border_style="br:magenta")

        # NETWORK INFO
        if self.network and self.network.get("adapters"):
            FormatCodes.print("\n[b|br:red](Network Adapters)")
            net_text = []
            for i, adapter in enumerate(self.network["adapters"]):
                if i > 0:
                    net_text.append("{hr}")
                status = "[i|green](Connected)" if adapter["is_up"] else "[i|dim|white](Disconnected)"
                net_text.append(f"[b|br:red]({adapter['name']}) {status}[_c]")
                if adapter.get("mac"):
                    net_text.append(f"  [b](MAC) : [br:white]({adapter['mac']})")
                if adapter.get("speed"):
                    net_text.append(f"[b](Speed) : [br:white]({adapter['speed']})")
            Console.log_box_bordered(*net_text, border_style="br:red")

        # BATTERY INFO
        if self.battery and self.battery.get("has_battery"):
            FormatCodes.print("\n[b|br:white](Battery Information)")
            battery_text = []
            time_left = self.battery.get("time_left")
            if self.battery.get("percent"):
                battery_text.append(f"{'        ' if time_left else ''}[b](Charge) : [br:white]({self.battery['percent']})")
            if self.battery.get("power_plugged") is not None:
                status = "[green](Plugged In)" if self.battery["power_plugged"] else "[i|yellow](On Battery)"
                battery_text.append(f"{'        ' if time_left else ''}[b](Status) : {status}[_c]")
            if time_left:
                battery_text.append(f"[b](Time Remaining) : [br:white]({time_left})")
            Console.log_box_bordered(*battery_text, border_style="br:white")

        print()


def main() -> None:
    if ARGS.help.exists:
        print_help()
        return

    hw_info = HardwareInfo()

    try:
        hw_info.gather_info(detailed=ARGS.detailed.exists)
    except Exception as e:
        Console.fail(f"Error gathering hardware information: {e}", end="\n\n")
        return

    if ARGS.json_output.exists:
        print()
        Data.print(hw_info.to_dict(), indent=2, as_json=True)
        print()
    else:
        hw_info.display()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
