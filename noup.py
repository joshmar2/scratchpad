#!/usr/bin/python3

__author__ = "SCA TAC First Responders"
__copyright__ = "Copyright 2023, Cisco Systems Inc."
__version__ = "1.1"
__status__ = "Production"

import logging
import os
import subprocess
import tempfile
from argparse import ArgumentParser
from datetime import datetime, timezone
from os import mkdir, path, remove
from shutil import copy, copytree, ignore_patterns, rmtree
from subprocess import STDOUT, CalledProcessError, TimeoutExpired, check_output, run

import netifaces

parser = ArgumentParser()
subparsers = parser.add_subparsers(dest="command")

parser_upload = subparsers.add_parser("upload")
parser_upload.add_argument("-c", "--case", help="The case number to attach the files to", required=True)
parser_upload.add_argument("-t", "--token", help="The token to upload files to cxd.cisco.com", required=True)

args = parser.parse_args()

if args.command == "upload":
    case = str(args.case)
    token = str(args.token)


def root_check():
    return os.geteuid() == 0


def create_bundle_dir():
    temp_dir = tempfile.mkdtemp()
    return temp_dir

bundledir = create_bundle_dir()

def set_stage():
    for subdir in "ona_meta_data", "os_info", "network", "connectivity", "process_info", "disk_stats":
        mkdir(path.join(bundledir, subdir))


def print_log(msg, screen=False, log=False, color=None, level="info"):
    if screen:
        color_code = {"red": "\033[91m", "green": "\033[92m"}.get(color, "")
        print(f"{color_code}{msg} \033[00m" if color_code else msg)
    if log:
        logging_func = getattr(logging, level)
        logging_func(msg)


def upload_file(case, token, f_name):
    command = ["curl", "-k", "--progress-bar", f"https://{case}:{token}@cxd.cisco.com/home/", "--upload-file", f_name]
    try:
        subprocess.check_output(command)
        print_log(f"`{f_name}` successfully uploaded to {case}", screen=True, log=True, color="green", level="info")
    except subprocess.CalledProcessError as e:
        print_log(f"[FAILURE] Failed to upload `{f_name}` to {case}.", screen=True, color="red")
        print_log(f"Upload failed with the following error:\n----------\n{e}\n----------", log=True, level="warn")
        print_log("Notify Cisco TAC of Failure to upload for further assistance", log=True, level="warn")


def cmd_to_file(filename, command):
    try:
        result = check_output(command, timeout=10, stderr=STDOUT, shell=True)
    except (CalledProcessError, TimeoutExpired) as e:
        result = e.output
    with open(f"{bundledir}/filename", "w") as f:
        print(f"{result.decode('utf8')}", file=f, end="")


def get_ip():
    for interface in netifaces.interfaces():
        if interface.startswith("lo"):
            continue
        addresses = netifaces.ifaddresses(interface).get(netifaces.AF_INET)
        if addresses:
            ip_address = addresses[0]["addr"]
            with open(f"{bundledir}/ona_meta_data/mgmt_ip", "w") as f:
                f.write(ip_address)
            return ip_address
    return None


def ona_meta_data():
    cmd_to_file("/ona_meta_data/version", "cat /opt/obsrvbl-ona/version")
    cmd_to_file("/ona_meta_data/hostname", "hostname --long")
    cmd_to_file("/ona_meta_data/platform", "cat /sys/class/dmi/id/product_name")
    cmd_to_file("/ona_meta_data/serial", 'cat /sys/class/dmi/id/product_serial | tr -sd " "')


def os_info():
    cmd_to_file("/os_info/uname", "uname -a")
    cmd_to_file("/os_info/sysctl", "sysctl -a")
    cmd_to_file("/os_info/release", "lsb_release -a 2>/dev/null")
    cmd_to_file("/os_info/os_release", "cat /etc/os-release")
    cmd_to_file("/os_info/bash_history", "head -n0 /home/*/.bash_history")
    cmd_to_file("/os_info/dpkg_ona", "dpkg-query -W ona-service")
    cmd_to_file("/os_info/apt_list_ona", "apt list --installed ona-service")
    cmd_to_file("/os_info/rpm_ona", "rpm -q ona-service")
    cmd_to_file("/os_info/dpkg_netsa", "dpkg-query -W netsa-pkg")
    cmd_to_file("/os_info/apt_list_netsa", "apt list --installed netsa-pkg")
    cmd_to_file("/os_info/rpm_netsa", "rpm -q netsa-pkg")
    cmd_to_file("/os_info/last_reboot", "uptime -s")


def network():
    cmd_to_file("/network/ip_addr_show", "ip addr show")
    cmd_to_file("/network/netstat_tunap", "netstat -tunap")
    cmd_to_file("/network/route", "route -n")
    cmd_to_file("/network/ifconfig", "ifconfig -a")


def connectivity():
    cmd_to_file("/connectivity/resolv", 'grep -Ev "^#" /etc/resolv.conf')
    cmd_to_file("/connectivity/netplan", "cat /etc/netplan/*.yaml")
    cmd_to_file("/connectivity/timedatectl", "timedatectl")
    cmd_to_file("/connectivity/chrony", "cat /etc/chrony.conf")
    cmd_to_file("/connectivity/ntp", "cat /etc/ntp.conf")
    cmd_to_file("/connectivity/sensor_ext", "curl -so- -D- https://sensor.ext.obsrvbl.com")
    cmd_to_file("/connectivity/sensor_us", "curl -so- -D- https://sensor.obsrvbl.obsrvbl.com")
    cmd_to_file("/connectivity/sensor_eu", "curl -so- -D- https://sensor.eu-prod.obsrvbl.com")
    cmd_to_file("/connectivity/sensor_anz", "curl -so- -D- https://sensor.anz-prod.obsrvbl.com")
    cmd_to_file("/connectivity/iptables", "iptables -nvL")
    cmd_to_file("/connectivity/firewalld", "firewall-cmd --list-all-zones")


def ona_settings_and_logs():
    copytree(
        "/opt/obsrvbl-ona/",
        f"{bundledir}/ona_settings/",
        ignore=ignore_patterns("*python-packages*", "*__pycache__*", "*.2*", "*pna-*.log*", "*pdns_*.pcap.gz"),
        copy_function=copy,
    )
    copytree("/var/log", f"{bundledir}/var/log/", ignore=ignore_patterns("*.dat", "journal"), copy_function=copy)
    cmd = f"/opt/silk/bin/rwcut --timestamp-format iso --fields sIp,dIp,sPort,dPort,protocol,Bytes,Packets,sTime,eTime /opt/obsrvbl-ona/logs/ipfix/.202* >> {bundledir}/ona_settings/logs/ipfix/clear_silk 2>/dev/null"
    run(cmd,shell=True)


def process_info():
    cmd_to_file("/process_info/top", "top -bn1")
    cmd_to_file("/process_info/free", "free -m")
    cmd_to_file("/process_info/meminfo", "cat /proc/meminfo")
    cmd_to_file("/process_info/cpuinfo", "cat /proc/cpuinfo")
    cmd_to_file("/process_info/ps_faux", "ps faux")
    cmd_to_file("/process_info/ps_obsrvbl", "ps -fU obsrvbl_ona")


def disk_stats():
    cmd_to_file("/disk_stats/df_ah", "df -ah")
    cmd_to_file("/disk_stats/du_xah", "du -xah /")
    cmd_to_file("/disk_stats/mounts", "cat /proc/mounts")
    cmd_to_file("/disk_stats/vgdisplay", "vgdisplay")
    cmd_to_file("/disk_stats/lvdisplay", "lvdisplay")
    cmd_to_file("/disk_stats/lsblk", "lsblk")
    cmd_to_file("/disk_stats/allfiles-list", "ls -laR /opt/")
    cmd_to_file("/disk_stats/lsof", "timeout 60 lsof")


def pcap_30_second():
    cmd = f"timeout 30 tcpdump -i any not host localhost and not host 127.0.0.1 and udp -c10000 -w {bundledir}/capture.pcap >/dev/null 2>&1"
    run(cmd, shell=True)


def main():
    functions = [
        set_stage,
        ona_meta_data,
        get_ip,
        os_info,
        network,
        connectivity,
        ona_settings_and_logs,
        process_info,
        disk_stats,
        pcap_30_second,
    ]
    print("\r\n*** Creating Support Bundle")
    for i, func in enumerate(functions, start=1):
        print(f"Processing {i}/{len(functions)}: {func.__name__:<22}", end="\r")
        func()
    bundle_name = f"scabundle-ona-{open('/sys/class/dmi/id/product_serial').read().strip().replace(' ','')}.{datetime.now(timezone.utc).strftime('%Y%m%d.%H%M')}.tar.xz"
    cmd = f"tar -Jcf {bundle_name} -C {bundledir} . ../capture.pcap --remove-files 2>/dev/null"
    print("\nCompressing files. This may take some time.")
    run(cmd, shell=True)
    if args.command == "upload":
        print("\nUploading file to TAC Case. This may take some time.")
        upload_file(case, token, bundle_name)
    else:
        pass


if root_check():
    main()
else:
    print("You are not root, re-run this script as root. Exiting.")