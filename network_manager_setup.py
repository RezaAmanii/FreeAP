import subprocess
import textwrap
import os


NETWORK_MANAGER_CONFIG_PATH = "/etc/NetworkManager/NetworkManager.conf"


class NetworkManagerSetup:
    def network_manager_setup(self, interface_name: str):
        config = textwrap.dedent(f"""\
        [main]
        plugins=ifupdown,keyfile

        [ifupdown]
        managed=false

        [keyfile]
        unmanaged-devices=interface-name:{interface_name}
        """)

        # Write configuration in the path of NetworkManager
        with open("/tmp/NetworkManager.conf", "w") as f:
            f.write(config)

        # Move file using sudo permission
        subprocess.run(
            ["sudo", "mv", "/tmp/NetworkManager.conf", NETWORK_MANAGER_CONFIG_PATH],
            check=True,
        )
        print(f"Successfully updated {NETWORK_MANAGER_CONFIG_PATH}")

        # Restart NetworkManager
        print("Restarting NetworkManager...")
        subprocess.run(["sudo", "systemctl", "restart", "NetworkManager"], check=True)

        # Reading the file
        with open(NETWORK_MANAGER_CONFIG_PATH, "r") as f:
            print(f.read().strip())

        # Verfiy
        subprocess.run(["nmcli", "device", "status"])

    def configure_static_ip(self, interface_name: str, ip_block: str):
        configure_filename = f"10-{interface_name}.network"
        target_path = f"/etc/systemd/network/{configure_filename}"
        tmp_path = f"/tmp/{configure_filename}"

        config = textwrap.dedent(f"""\
        [Match]
        Name={interface_name}

        [Network]
        Address={ip_block}
        """)

        try:
            print(f"Generating systemd-networkd configuration for {interface_name}...")

            with open(tmp_path, "w") as f:
                f.write(config)

            # Move the file into the systemd-networkd directory using sudo
            subprocess.run(["sudo", "mv", tmp_path, target_path], check=True)
            print(f"SYSTEMD-NETWORKD Configuration deployed to {target_path}")

            # Activating systemd-networkd
            print("Activating systemd-networkd...")
            subprocess.run(
                ["sudo", "systemctl", "enable", "systemd-networkd"], check=True
            )
            subprocess.run(
                ["sudo", "systemctl", "start", "systemd-networkd"], check=True
            )

            # Restart systemd-networkd to apply changes
            print("Restarting systemd-networkd daemon...")
            subprocess.run(
                ["sudo", "systemctl", "restart", "systemd-networkd"], check=True
            )

        except subprocess.CalledProcessError as e:
            print(f"System automation failed 'systemd-networkd' {e}")

    def configure_hostapd(
        self, interface_name: str, ssid: str, passcode: str, hw_mode: str, channel: str
    ):
        configure_filename = f"{interface_name}-hostapd.conf"
        target_path = f"/etc/hostapd/{configure_filename}"
        tmp_path = f"/tmp/{configure_filename}"

        if len(passcode) < 8:
            print("The length of the passcode should be >8 characters...")
            return

        config = textwrap.dedent(f"""\
        interface={interface_name}
        driver=nl80211
        ssid={ssid}
        hw_mode={hw_mode}
        channel={channel}
        ieee80211n=1

        wpa=2
        wpa_passphrase={passcode}
        wpa_key_mgmt=WPA-PSK
        wpa_pairwise=CCMP
        rsn_pairwise=CCMP

        wpa_disable_eapol_key_retries=0
        """)

        try:
            print(f"Generating hosapd configuration for {interface_name}...")

            with open(tmp_path, "w") as f:
                f.write(config)

            subprocess.run(["sudo", "mv", tmp_path, target_path], check=True)
            print(f"HOSTAPD Configuration deployed to {target_path}")

        except subprocess.CalledProcessError as e:
            print(f"System automation failed 'HOSTAPD' {e}")

    def configure_dhcp(
        self,
        interface_name: str,
        start_ip_address: str,
        end_ip_address: str,
        dns_mask: str,
    ):
        configure_filename = f"{interface_name}-dhcp.conf"
        target_path = f"/etc/dnsmasq.d/{configure_filename}"
        tmp_path = f"/tmp/{configure_filename}"

        config = textwrap.dedent(f"""\
        interface={interface_name}
        dhcp-range={start_ip_address},{end_ip_address},{dns_mask},24h
        """)

        try:
            print(f"Generating dhcp configuration for {interface_name}...")

            with open(tmp_path, "w") as f:
                f.write(config)

            subprocess.run(["sudo", "mv", tmp_path, target_path], check=True)
            print(f"DHCP configuration deployed to {interface_name}...")

            print("Restarting dnsmasq daemon...")
            subprocess.run(["sudo", "systemctl", "restart", "dnsmasq"], check=True)
            print("dnsmasq is successfully running with new leases!")

        except subprocess.CalledProcessError as e:
            print(f"System automation failed 'DHCP' {e}")

    def enable_wlan_forward(self, interface_name: str):
        configure_filename = f"99-{interface_name}.conf"
        target_path = f"/etc/sysctl.d/{configure_filename}"
        tmp_path = f"/tmp/{configure_filename}"

        config = "net.ipv4.ip_forward=1"

        try:
            print(
                f"Writing persistent configuration for '{interface_name}' packet forwarding..."
            )

            with open(tmp_path, "w") as f:
                f.write(config)

            subprocess.run(["sudo", "mv", tmp_path, target_path], check=True)

            print("Reloading system network variables (sysctl)...")
            subprocess.run(["sudo", "sysctl", "--system"], check=True)
            print("Kernel interface forwarding is now LIVE!")

        except subprocess.CalledProcessError as e:
            print(f"System automation failed 'Network Interface Forwarding' {e}")

    def configure_nat(self, upstream_interface: str):
        target_path = "/etc/nftables.conf"
        tmp_path = "/tmp/nftables.conf"

        nat_config = textwrap.dedent(f"""
        
        table ip nat {{
            chain postrouting {{
                type nat hook postrouting priority srcnat; policy accept;
                oifname "{upstream_interface}" masquerade
            }}
        }}
        """)

        try:
            print(
                f"Configuring NAT routing rules via nftables for upstream {upstream_interface}..."
            )

            subprocess.run(["sudo", "systemctl", "enable", "nftables"], check=True)
            subprocess.run(["sudo", "systemctl", "start", "nftables"], check=True)

            with open(target_path, "r") as f:
                capture_content = f.read()

            # Prevent duplicate appends if the code is executed multiple times
            if (
                "table ip nat" in capture_content
                and f'oifname "{upstream_interface}"' in capture_content
            ):
                print(
                    "NAT rules are already present in nftables.conf. Skipping file write."
                )
            else:
                new_content = capture_content + nat_config
                with open(tmp_path, "w") as f:
                    f.write(new_content)

                subprocess.run(["sudo", "mv", tmp_path, target_path], check=True)

                print("Restarting nftables firewall...")
                subprocess.run(["sudo", "systemctl", "restart", "nftables"], check=True)
                print("Firewall NAT routing bridge is now LIVE!")

        except subprocess.CalledProcessError as e:
            print(f"System automation failed 'nftables NAT': {e}")

    def uninstall_system(self, interface_name: str, upstream_interface: str):
        print("Beginning Full Network Stack Uninstallation...")
        print("-" * 60)

        # Target path to clean up
        network_manager_config = "/etc/NetworkManager/NetworkManager.conf"
        systemd_config = f"/etc/systemd/network/10-{interface_name}.network"
        hostapd_config = f"/etc/hostapd/{interface_name}-hostapd.conf"
        dnsmasq_config = f"/etc/dnsmasq.d/{interface_name}-dhcp.conf"
        sysctl_config = f"/etc/sysctl.d/99-{interface_name}.conf"
        nftables_config = "/etc/nftables.conf"

        try:
            # Kill any hostspot process immediately
            print("Force stopping hostapd and network process...")
            subprocess.run(
                ["sudo", "killall", "hostapd"], capture_output=True, check=False
            )

            # Disable and stop background daemons we activated
            print("Disabling dnsmasq and systemd-networkd file we generated...")
            subprocess.run(
                ["sudo", "systemctl", "disable", "--now", "dnsmasq"], check=False
            )
            subprocess.run(
                ["sudo", "systemctl", "disable", "--now", "systemd-networkd"],
                check=False,
            )

            # Cleanly delete all the modular configuration files we generated
            print("Deleting configuration files...")
            files_to_delete = [
                systemd_config,
                hostapd_config,
                dnsmasq_config,
                sysctl_config,
            ]
            for file_path in files_to_delete:
                if os.path.exists(file_path) or True:
                    subprocess.run(["sudo", "rm", "-f", file_path], check=True)
            print("Custom configuration files are removed.")

            # Restore NetworkManager.conf back to its default state
            print("Restoring original NetworkManager configuration...")
            default_nm = textwrap.dedent("""\
            # Configuration file for NetworkManager.
            # See 'Man 5 NetworkManager.conf' for details.
            """)

            with open("/tmp/NetworkManager.conf", "w") as f:
                f.write(default_nm)

            subprocess.run(
                ["sudo", "mv", "/tmp/NetworkManager.conf", network_manager_config],
                check=True,
            )

            print("Restoring factory nftables template...")
            default_nftables = textwrap.dedent("""\
            flush ruleset

            table inet filter {
                chain input {
                    type filter hook input priority filter; policy accept;
                }
                chain forward {
                    type filter hook forward priority filter; policy accept;
                }
                chain output {
                    type filter hook output priority filter; policy accept;
                }
            }
            """)

            with open("/tmp/nftables.conf", "w") as f:
                f.write(default_nftables)

            subprocess.run(
                ["sudo", "mv", "/tmp/nftables.conf", nftables_config], check=True
            )
            subprocess.run(["sudo", "systemctl", "restart", "nftables"], check=True)

            # Trun off IP packet forwarding inside the live Linux Kernel
            print("Disabling kernel IP forwarding...")
            subprocess.run(
                ["sudo", "sysctl", "-w", "net.ipv4.ip_forward=0"], check=True
            )
            subprocess.run(["sudo", "sysctl", "--system"], check=True)

            # Restarting NetworkManager to reclaim the network adapter
            print("Reseting core NetworkManager engine...")
            subprocess.run(
                ["sudo", "systemctl", "restart", "NetworkManager"], check=True
            )

            # Wake the wireless radios back up explicitly
            subprocess.run(["sudo", "nmcli", "radio", "wifi", "on"], check=True)
            subprocess.run(
                ["sudo", "nmcli", "device", "connect", upstream_interface], check=False
            )

            print("-" * 60)
            print("UNINSTALL COMPLETE! Your OS is back to factory network defaults.")

        except subprocess.CalledProcessError as e:
            print(f"Uninstallation failed process halted due to system error {e}")

    def go_online(self, interface_name: str):
        print("Turning ON custom router...")

        hostapd_config_file_path = f"/etc/hostapd/{interface_name}-hostapd.conf"

        try:
            process = subprocess.Popen(
                ["sudo", "hostapd", hostapd_config_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            print(f"Hostapd is now broadcasting on {interface_name} in the backgroud!")
            return process
        except Exception as e:
            print(f"Failed to spin up hostapd wrapper: {e}")

    def go_offline(self):
        print("Turning OFF custom router...")

        try:
            print(" Closing wireless broadcast (hostapd)...")
            subprocess.run(
                ["sudo", "killall", "hostapd"], capture_output=True, check=False
            )

            print(" Stopping DHCP daemon (dnsmasq)...")
            subprocess.run(["sudo", "systemctl", "stop", "dnsmasq"], check=True)

            print("Custom router is completely offline and resources are freed.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to bring network offline cleanly: {e}")
