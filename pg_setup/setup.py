#!/usr/bin/env python3

import shutil
import os
import tarfile
import time
import stat

# Function to check if a directory is empty
def is_directory_empty(directory):
    return not os.listdir(directory)

# Function to extract tar archive contents
def extract_tar(tarfile_path, destination):
    print(f"Extracting {tarfile_path} to {destination}...", flush=True)
    try:
        with tarfile.open(tarfile_path, 'r') as tar:
            tar.extractall(path=destination)
        print(f"Extraction to {destination} successful", flush=True)
    except Exception as e:
        print(f"Error extracting {tarfile_path} to {destination}: {str(e)}", flush=True)

# Function to change ownership and permissions of files
def change_permissions_and_ownership(directory, uid=999, gid=999):
    for root, dirs, files in os.walk(directory):
        for dir_name in dirs:
            os.chown(os.path.join(root, dir_name), uid, gid)
            os.chmod(os.path.join(root, dir_name), 0o755)
        for file_name in files:
            os.chown(os.path.join(root, file_name), uid, gid)
            os.chmod(os.path.join(root, file_name), 0o644)
    print(f"Permissions and ownership changed for {directory}", flush=True)

# Function to append or update a parameter in postgresql.conf
def update_postgresql_conf(filepath, parameter, value):
    try:
        updated = False
        with open(filepath, 'r') as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                if line.strip().startswith(parameter):
                    if '#' in line:
                        # Parameter is commented out, uncomment it
                        lines[i] = f"{parameter} = {value}\n"
                        updated = True
                    else:
                        # Parameter exists and is set, update it
                        lines[i] = f"{parameter} = {value}\n"
                        updated = True
                    break
            else:
                # Parameter not found, append it at the end of the file
                lines.append(f"{parameter} = {value}\n")
                updated = True
        
        if updated:
            with open(filepath, 'w') as file:
                file.writelines(lines)
                print(f"Updated {parameter} in {filepath}", flush=True)
        else:
            print(f"No changes needed for {parameter} in {filepath}", flush=True)
    except Exception as e:
        print(f"Error updating {parameter} in {filepath}: {str(e)}", flush=True)

# Function to add a line to pg_hba.conf
def add_line_to_pg_hba_conf(filepath, line):
    try:
        with open(filepath, 'a') as file:
            file.write(f"{line}\n")
        print(f"Added line to {filepath}: {line}", flush=True)
    except Exception as e:
        print(f"Error adding line to {filepath}: {str(e)}", flush=True)

# Paths to directories and files
pg_backup_tar = '/pg_backup.tar'
pg_master = '/pg_master'
pg_slave = '/pg_slave'
pg_asyncslave = '/pg_asyncslave'
pg_standalone = '/pg_standalone'

# Path to flag file
flag_file = '/setup_done.flag'

# Retrieve PG_NET from environment variables
PG_NET = os.environ.get('PG_NET')

# Check if setup is already done
if os.path.exists(flag_file):
    print("Setup already done. Sleeping indefinitely...", flush=True)
    while True:
        time.sleep(3600)  # Sleep for an hour and then repeat indefinitely

# Extract contents of /pg_backup.tar to /pg_master, /pg_slave, /pg_asyncslave
extract_tar(pg_backup_tar, pg_master)
extract_tar(pg_backup_tar, pg_slave)
extract_tar(pg_backup_tar, pg_asyncslave)
extract_tar(pg_backup_tar, pg_standalone)

# Change permissions and ownership of extracted files
change_permissions_and_ownership(pg_master)
change_permissions_and_ownership(pg_slave)
change_permissions_and_ownership(pg_asyncslave)
change_permissions_and_ownership(pg_standalone)

# Configure PostgreSQL settings on /pg_master
configurations = {
    "ssl": "off",
    "wal_level": "logical",
    "max_wal_senders": "4",
    "synchronous_commit": "on",
    "synchronous_standby_names": "'FIRST 1 (pg_slave, pg_asyncslave)'"
}

for param, value in configurations.items():
    update_postgresql_conf(os.path.join(pg_master, 'postgresql.conf'), param, value)

# Update pg_hba.conf on /pg_master
add_line_to_pg_hba_conf(os.path.join(pg_master, 'pg_hba.conf'), f"host replication replicator {PG_NET} md5")

# Create standby.signal file and configure settings on /pg_slave
open(os.path.join(pg_slave, 'standby.signal'), 'a').close()
update_postgresql_conf(os.path.join(pg_standalone, 'postgresql.conf'), "wal_level", "replica")
update_postgresql_conf(os.path.join(pg_slave, 'postgresql.conf'), "primary_conninfo", "'host=pg_master port=5432 user=replicator password=pass application_name=pg_slave'")
add_line_to_pg_hba_conf(os.path.join(pg_slave, 'pg_hba.conf'), f"host replication replicator {PG_NET} md5")

# Create standby.signal file and configure settings on /pg_asyncslave
open(os.path.join(pg_asyncslave, 'standby.signal'), 'a').close()
update_postgresql_conf(os.path.join(pg_standalone, 'postgresql.conf'), "wal_level", "replica")
update_postgresql_conf(os.path.join(pg_asyncslave, 'postgresql.conf'), "primary_conninfo", "'host=pg_master port=5432 user=replicator password=pass application_name=pg_asyncslave'")
add_line_to_pg_hba_conf(os.path.join(pg_asyncslave, 'pg_hba.conf'), f"host replication replicator {PG_NET} md5")

# Create standby.signal file and configure settings on /pg_standalone
update_postgresql_conf(os.path.join(pg_standalone, 'postgresql.conf'), "wal_level", "logical")
update_postgresql_conf(os.path.join(pg_standalone, 'postgresql.conf'), "primary_conninfo", "'host=pg_master port=5432 user=replicator password=pass application_name=pg_standalone'")
add_line_to_pg_hba_conf(os.path.join(pg_standalone, 'pg_hba.conf'), f"host replication replicator {PG_NET} md5")

# Create flag file to indicate setup is done
with open(flag_file, 'w') as file:
    file.write('setup_done')

print("Setup completed successfully. Sleeping indefinitely...", flush=True)
while True:
    time.sleep(3600)  # Sleep for an hour and then repeat indefinitely