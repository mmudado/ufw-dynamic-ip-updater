#!/usr/bin/python3

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Check Hostnames address/IP for changes and updates ufw accordingly."""

import os, signal
import time
import subprocess, select
import re
import sys, signal
import argparse
import string
from os.path import isfile, join
from datetime import datetime
import json
import ipaddress

FNULL = open(os.devnull, 'w')
GETENT =  "/usr/bin/getent"
UFW = "/usr/sbin/ufw"

def _is_valid_json(file_path: str) -> None:
    """Invoke all validations."""
    if _exists(file_path) and _is_file(file_path) and  _is_readable(file_path) and _is_readable_json(file_path):
        return True
    else:
        return False

def _is_ip_valid(ipv4: str) -> None:
    """ Validate IP address """
    try:
        ip_addr = ipaddress.ip_address(ipv4)
    except ValueError as e:
        raise e
    return True

def _is_port_valid(port: str) -> None:
    """ Validate port range """
    if ( (int(port) <= 65535) and (int(port) >= 1)):
        return True
    else:
        return False

def _is_hostname_valid(hostname: str) -> None:
    """ Validate domain name address """
    if hostname[-1] == ".":
        hostname = hostname[:-1] # strip exactly one dot from the right, if present
    if len(hostname) > 255:
        return False
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    for x in hostname.split("."):
        if not allowed.match(x):
            return False
    return True

def _is_readable_json(file_path: str) -> None:
    """Check whether json is readable."""
    with open(file_path) as json_file:
        try:
            json.load(json_file)
        except json.decoder.JSONDecodeError as e:
            print ("JSON file format invalid {}".format(json_file))
            raise e
    return True

def _exists(file_path: str) -> None:
    """Check whether a file exists."""
    if not os.path.exists(file_path):
        return False
    else:
        return True

def _is_file(file_path: str) -> None:
    """Check whether file is actually a file type."""
    if not os.path.isfile(file_path):
        return False
    else:
        return True

def _is_readable(file_path: str) -> None:
    """Check file is readable."""
    try:
        f = open(file_path, "r")
        f.close()
        return True
    except IOError:
        return False

def remove_log(log):
    try:
        os.remove(log)
    except IOError as e:
        raise e

def getent_ip(addr: str):
    ip = '' 
    try:
        ip = (subprocess.getoutput(GETENT + " hosts " + addr + " | cut -d' ' -f1"))
    except (IOError, OSError) as e:
        raise e
    return ip

def enable_ufw():
    args = [UFW, "--force", "enable"]
    try:
        subprocess.run(args, stdout=FNULL, stderr=FNULL)
    except (IOError, OSError) as e:
        raise e
    return True

def reset_ufw():
    args = [UFW, "--force", "reset"]
    try:
        subprocess.run(args, stdout=FNULL, stderr=FNULL)
    except (IOError, OSError) as e:
        raise e
    return True

def insert_ufw_rules(ipv4: str, port: str):
    args = [UFW, "allow", "from", ipv4, "to", "any", "port", port]
    try:
        subprocess.run(args, stdout=FNULL, stderr=FNULL)
    except (IOError, OSError) as e:
        raise e
    return True

def delete_ufw_rules(ipv4: str, port: str):
    args = [UFW, "delete", "allow", "from", ipv4, "to", "any", "port", port]
    try:
        subprocess.run(args, stdout=FNULL, stderr=FNULL)
    except (IOError, OSError) as e:
        raise e
    return True

def get_dict_from_json(jsonfile: str):
    try:
        with open(jsonfile) as f:
            nodes = json.load(f)
    except OSError as e:
        raise e
    return nodes

def _are_valid_nodes(nodes: list):
    for entry in nodes:
        if ( (isinstance(entry, dict)) and (len(entry) == 3) and (entry["ipv4"]) and (_is_ip_valid(entry["ipv4"])) and (entry["name"]) and (_is_hostname_valid(entry["name"])) and (entry["port"]) and _is_port_valid(entry["port"]) ):
            pass
        else:
            return False
    return True
    
def insert_nodes_rules_ufw(nodes: list):
    for entry in nodes:
        try:
            insert_ufw_rules(entry["ipv4"], entry["port"])
        except (IOError, OSError) as e:
            raise e
    return True

def resolve_ips_update_ufw(nodes: list):
    new_nodes = list()
    changed_ips = list()

    for entry in nodes:
        new_node = dict()
        ip = getent_ip(entry["name"])
        if not ip :
            print("Could not resolve {} name address".format(entry["name"]))
            sys.exit()
        else:
            # update ufw rules
            if ip != entry["ipv4"]:
                changed_ips.append(entry["ipv4"])
                d = delete_ufw_rules(entry["ipv4"], entry["port"])
                u = insert_ufw_rules(ip, entry["port"])
            new_node.update({'name' : entry["name"]})
            new_node.update({'ipv4' : ip})
            new_node.update({'port' : entry["port"]})
            new_nodes.append(new_node)
    return (new_nodes, changed_ips)

def dump_new_json(new_nodes: list, nodes_file:str):
    try:
        with open(nodes_file, "w") as data_file:
            json.dump(new_nodes, data_file, indent=4)
    except IOError as e:
        raise e
    except ValueError as v:
        raise v
    return True


####################
# RUNNING THE SCRIPT
####################
parser = argparse.ArgumentParser(description="Updates ufw rules as dynamic IP address changes.")
group = parser.add_mutually_exclusive_group()
group.add_argument("-v", "--verbose", required=False, action="store_true")
parser.add_argument("-f", "--json_file", required=True, type=str, help="full directory path that contains the .json configuration file")
args = parser.parse_args()

### VALIDATING .JSON FILE
valid = False
if _is_valid_json(args.json_file):
        pass
else:
    print("JSON format not valid:  {}... ".format(args.json_file))
    sys.exit()

### READ NODE'S DATA
nodes = list()
nodes = get_dict_from_json(args.json_file)
if _are_valid_nodes(nodes):
    pass
else:
    print("Data format is not valid. Check file {} and README. ".format(args.json_file))
    sys.exit()

### START UFW 
if enable_ufw():
   pass
else:
    print("could not start ufw")
    sys.exit()

#### INSERT RULES
if insert_nodes_rules_ufw(nodes):
    pass
else:
    print("could not insert ufw rules")
    sys.exit()

#### RESOLVE IPS'S AND UPDATE UFW
new_nodes = list()
changed_ips = list()
(new_nodes, changed_ips) = resolve_ips_update_ufw(nodes)
if not changed_ips:
    pass
else:
    for entry in changed_ips:
        if (args.verbose):
            print("{} !!!!!! IP {} have changed !!!!".format(datetime.now(),entry))

### DUMP THE NEW JSON NODES TO FILE
if new_nodes != nodes:
    dump_new_json(new_nodes, args.json_file)
