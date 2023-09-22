def main():
    functions = [set_stage, ona_meta_data, get_ip, os_info, network, connectivity, ona_settings_and_logs, process_info, disk_stats, pcap_30_second] 
    print("\r\n*** Creating Support Bundle") 
    for i, func in enumerate(functions, start=1): 
        print(f"Processing {i}/{len(functions)}: {func.name:<22}", end="\r") 
        func() 
    if args.command == "upload": 
        bundle_name = f"scabundle-ona-{open('/sys/class/dmi/id/product_serial').read().strip().replace(' ','')}.{datetime.now(timezone.utc).strftime('%Y%m%d.%H%M')}_fr.tar.xz"
    else:
        bundle_name = f"scabundle-ona-{open('/sys/class/dmi/id/product_serial').read().strip().replace(' ','')}.{datetime.now(timezone.utc).strftime('%Y%m%d.%H%M')}.tar.xz"
    cmd = f"tar -Jcf {bundle_name} -C {bundledir} . ../capture.pcap --remove-files 2>/dev/null" 
    print("\nCompressing files. This may take some time.") 
    run(cmd, shell=True) 
    if args.command == "upload": 
        print("\nUploading file to TAC Case. This may take some time.") 
        upload_file(case, token, bundle_name)
    else:
        pass

def main():
    functions = [set_stage, ona_meta_data, get_ip, os_info, network, connectivity, ona_settings_and_logs, process_info, disk_stats, pcap_30_second] 
    print("\r\n*** Creating Support Bundle") 
    for i, func in enumerate(functions, start=1): 
        print(f"Processing {i}/{len(functions)}: {func.name:<22}", end="\r") 
        func() 
    bundle_name = f"scabundle-ona-{open('/sys/class/dmi/id/product_serial').read().strip().replace(' ','')}.{datetime.now(timezone.utc).strftime('%Y%m%d.%H%M')}.tar.xz"
    if args.command == "upload": 
        unique_bundle_name = bundle_name.replace('.tar.xz', f'_{uuid.uuid4()}.tar.xz') 
    else: 
        unique_bundle_name = bundle_name cmd = f"tar -Jcf {unique_bundle_name} -C {bundledir} . ../capture.pcap --remove-files 2>/dev/null" 
    print("\nCompressing files. This may take some time.") 
    run(cmd, shell=True) 
    if args.command == "upload": 
        print("\nUploading file to TAC Case. This may take some time.")
        upload_file(case, token, unique_bundle_name) 
    else: 
        pass

def main():
    functions = [set_stage, ona_meta_data, get_ip, os_info, network, connectivity, ona_settings_and_logs, process_info, disk_stats, pcap_30_second] 
    print("\r\n*** Creating Support Bundle") 
    for i, func in enumerate(functions, start=1): 
        print(f"Processing {i}/{len(functions)}: {func.name:<22}", end="\r") 
        func() 
    bundle_name = f"scabundle-ona-{open('/sys/class/dmi/id/product_serial').read().strip().replace(' ','')}.{datetime.now(timezone.utc).strftime('%Y%m%d.%H%M')}.tar.xz" 
    cmd = f"tar -Jcf {bundle_name} -C {bundledir} . ../capture.pcap --remove-files 2>/dev/null" 
    print("\nCompressing files. This may take some time.") 
    run(cmd, shell=True) 
    if args.command == "upload": 
        unique_bundle_name = bundle_name.replace('.tar.xz', '_fr.tar.xz') 
        print("\nUploading file to TAC Case. This may take some time.") 
        upload_file(case, token, unique_bundle_name)
    else:
        pass
