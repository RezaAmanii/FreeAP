import argparse
import sys
import time
from network_utils import NetworkUtils
from network_manager_setup import NetworkManagerSetup


class HotspotControlCenter:

    def __init__(self):
        self.network_utils = NetworkUtils()
        self.nm_setup = NetworkManagerSetup()

        try:
            self.wlan_hotspot = self.network_utils.phy_to_wlan("phy1")[-1]
        except Exception:
            print("Warning: Could not automatically map phy1. Defaulting to wlan1.")
            self.wlan_hotspot = "wlan1"

        self.wlan_internet = "wlan0"




    def print_banner(self):
        print("\n" + "=" * 55)
        print("FREE NETWOWORK CONTROL CENTER")
        print("=" * 55)
        print(f"Hotspt Broadcast [Output]: {self.wlan_hotspot}")
        print(f"Internet Provider [Input]: {self.wlan_internet}")
        print("="  * 55)


    def run_setup(self):
        print("\n Executing System Provisioning Sequence...")
        self.nm_setup.network_manager_setup(self.wlan_hotspot)
        self.nm_setup.configure_static_ip(self.wlan_hotspot, "192.168.4.1/24")
        self.nm_setup.configure_hostapd(self.wlan_hotspot, "Freeland2.0", "11223344", "g", "1")
        self.nm_setup.configure_dhcp(self.wlan_hotspot, "192.168.4.2", "192.168.4.254", "255.255.255.0")
        self.nm_setup.enable_wlan_forward(self.wlan_hotspot)
        self.nm_setup.configure_nat(self.wlan_internet)
        print("\n SYSTEM PROVISIONING COMPLETE! Ready to go online!")

    def run_online(self):
        self.nm_setup.go_online(self.wlan_hotspot)
        
        try:
            print("\n 'Freeland2.0' is active and serving clients.")
            print("PRESS CTRL+C TO SHUT DOWN THE ROUTER CLEANLY.")

            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            self.run_offline()


    def run_offline(self):
        print("\n")
        self.nm_setup.go_offline()


    def run_uninstall(self):
        print("\n Initiating Complete System Wipe...")
        self.nm_setup.uninstall_system(self.wlan_hotspot, self.wlan_internet)


    def interactive_menu(self):
        while True:
            self.print_banner()
            print(" [1] Run System Setup (Generate All Configs)")
            print(" [2] Go ONLINE (Start Hotspot & Routing)")
            print(" [3] Go OFFLINE (Stop Service)")
            print(" [4] UNINSTALL (Wipe Configs & Restore Factory Defaults)")
            print(" [5] Exit Control Center")
            print("=" * 55)

            choice = input("Select an option (1-5): ").strip()

            if choice == "1":
                self.run_setup()
            elif choice == "2":
                self.run_online()
            elif choice == "3":
                self.run_offline()
            elif choice == "4":
                confirm = (input("Are you sure you want to completely uninstall? (y/N): ").strip().lower())
                if confirm == "y":
                    self.run_uninstall()
                else:
                    print("Uninstallation aborted.")
            elif choice == "5":
                print("Exiting Control Center. Goodbye!")
                sys.exit(0)
            else:
                print("Invalid choice. Please select a number between 1 and 5.")

            input("\nPress Enter to return to main menu...")



def main():
    parser = argparse.ArgumentParser(description="Freeland Hotspot Control Center Router CLI Wrapper")
    parser.add_argument("--setup", action="store_true", help="Run initial provisioning sequence")
    parser.add_argument("--start", action="store_true", help="Bring the hotspot router online")
    parser.add_argument("--stop", action="store_true", help="Take the hotspot router offline")
    parser.add_argument("--uninstall", action="store_true", help="Wipe configs and reset OS defaults")

    args = parser.parse_args()
    control_center = HotspotControlCenter()

    if args.setup:
        control_center.run_setup()
    elif args.start:
        control_center.run_online()
    elif args.stop:
        control_center.run_offline()
    elif args.uninstall:
        control_center.run_uninstall()
    else:
        control_center.interactive_menu()



if __name__ == "__main__":
    main()



