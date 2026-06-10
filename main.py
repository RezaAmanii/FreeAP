import time
from network_utils import NetworkUtils
from network_manager_setup import NetworkManagerSetup


def main():
    network_utils = NetworkUtils()
    nm_setup = NetworkManagerSetup()

    networks = network_utils.conn_network_interfaces()
    modes = network_utils.adapter_interfaces_modes("phy1")
    wlan = network_utils.phy_to_wlan("phy1")[-1]

    nm_setup.network_manager_setup(wlan)
    nm_setup.configure_static_ip(wlan, "192.168.4.1/24")
    nm_setup.configure_hostapd(wlan, "Freeland2.0", "11223344", "g", "1")
    nm_setup.configure_dhcp(wlan, "192.168.4.2", "192.168.4.254", "255.255.255.0")
    nm_setup.enable_wlan_forward(wlan)

    nm_setup.configure_nat("wlan0")

    nm_setup.go_online(wlan)

    try:
        print("Freeland2.0 is active and servering clients.")
        print("PRESS CTRL+C TO SHUT DOWN THE ROUTER CLEANLY.")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n")
        nm_setup.go_offline()


if __name__ == "__main__":
    main()
