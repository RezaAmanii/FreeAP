import subprocess
import re
from typing import List


class NetworkUtils:
    def conn_network_interfaces(self):
        info_dict = {}

        output = subprocess.check_output(["ip", "link", "show"], text=True)

        for line in output.splitlines():
            match = re.match(r"^\d+:\s+([^:]+):.*mtu\s+(\d+).*state\s+(\S+)", line)

            if match:
                interface = match.group(1)
                mtu = match.group(2)
                state = match.group(3)

                # MAC Address on the next line
                idx = output.splitlines().index(line) + 1
                mac_line = output.splitlines()[idx]

                mac_match = re.search(r"link/\w+\s+([0-9a-f:]{17})", mac_line)
                mac = mac_match.group(1) if mac_match else "N/A"

                info_dict[interface] = {"mtu": mtu, "state": state, "MAC": mac}

        return info_dict

    def adapter_interfaces_modes(self, phy_name: str) -> List[str]:
        output = subprocess.check_output(["iw", "list"], text=True)

        lines = output.splitlines()

        in_phy = False
        in_modes = False
        modes = []

        target = f"Wiphy {phy_name}"

        for line in lines:
            line = line.rstrip()

            if line.startswith("Wiphy "):
                in_phy = line.strip() == target
                in_modes = False
                continue

            if not in_phy:
                continue

            if "Supported interface modes:" in line:
                in_modes = True
                continue

            if in_modes:
                stripped = line.strip()

                if stripped.startswith("*"):
                    modes.append(stripped.lstrip("* ").strip())
                else:
                    break

        return modes

    def phy_to_wlan(self, phy_name: str):
        output = subprocess.check_output(["iw", "dev"], text=True)

        current_phy = None
        interfaces = []

        for line in output.splitlines():
            line = line.strip()

            # detect PHY
            phy_match = re.match(r"phy#(\d+)", line)
            if phy_match:
                current_phy = f"phy{phy_match.group(1)}"
                continue

            # Collect interface under that PHY
            if current_phy == phy_name:
                iface_match = re.match(r"Interface\s+(\w+)", line)
                if iface_match:
                    interfaces.append(iface_match.group(1))

        return interfaces
