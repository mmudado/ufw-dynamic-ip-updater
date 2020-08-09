# ufw-dynamic-ip-updater.py

This script is intended to update your ufw firewall by resolving a list of one or more dynamic IP addresses in a
.json file.

## Purpose of the script

Say you have a machine in which the input communications should be filtered by specific IPv4 addresses and ports.
And say these IPs are dynamic and change often.

Example: A Cardano producer node, part of a stake pool operation, that can only communicate with its relays by specific ports.
To provide better security, this producer node also filters the incoming communications by the relays's IPs. 

Check out the Cardano's Foundation [best security approaches](https://docs.cardano.org/projects/cardano-node/en/latest/stake-pool-operations/node_keys.html#basic-block-producing-node-firewall-configuration) for a block producing node: 

 - Make sure you can only login with SSH Keys, not password.
 - Make sure to setup SSH connections in a port different than the default 22
 - Make sure to configure the firewall to only allow connections from your relay nodes by setting up their ip addresses.

Some of the relays may have dynamic IPs, so the firewall (e.g. ufw/iptables) from this producer node have to be updated
 every time its relays's IPs change. 

Ufw uses iptables to set firewall rules, and unfortunatelly they cannot resolve hostname addresses, so this needs to be done in another way.

Dummy example of a ufw configuration from such a producer node, port 3001 open only to the specified relays's IPs, and default SSH port open to your machine's IP:

	$ sudo ufw status numbered

	Status: active

	     To                         Action      From
	     --                         ------      ----
	[ 1] 3001                       ALLOW IN    111.222.333.444            
	[ 2] 3001                       ALLOW IN    555.666.777.888            
	[ 3] 3001                       ALLOW IN    12.13.14.15             
	[ 4] 3001                       ALLOW IN    21.22.23.24 
	[ 5] 22/tcp                     ALLOW IN    123.123.123.123                  
	[ 6] 22/tcp (v6)                ALLOW IN    123.123.123.123.   

In the example above, it would be desirable to change the default SSH port (22) to any random other.

## Before you begin
 
 !!! Make sure **you have a SSH port already open** by ufw rules !!! You may lose communication to your
machine if you don't. !!! If not, run the following command to open SSH in ufw to your machine:


    sudo ufw allow from <YOUR-IP> to any port <SSH-PORT>
    
 - ufw-dynamic-ip-updater.py enables ufw by default.

 - ufw-dynamic-ip-updater.py **does not disable ufw or removes rules** not related in the .json file.
 
 - The script should be run by root or any superuser.

 - Use it by your own risks - please try it out and make suggestions/corrections, I would really appreciate it.

## Installation

 - Create a file named "relay.json" with the format below (a list of dictionaries). 

```json
	[
	    {
		"name": "relay1.net.io",
		"ipv4": "0.0.0.0",
		"port": "3001"
	    },
	    {
		"name": "relay2.hopto.org",
		"ipv4": "0.0.0.0",
		"port": "3001"
	    },
	    {
		"name": "relay3.com.br",
		"ipv4": "0.0.0.0",
		"port": "3001"
	    },
	    {
		"name": "relay4.dns.me",
		"ipv4": "0.0.0.0",
		"port": "3001"
	    }
	]
```
 Change the addresses and insert/remove entries accordingly to your configuration:

 Put "relays.json" together with "ufw-dynamic-ip-updater.py" in a root's accessible directory (e.g. /root/)

 Make the script runnable by:

    chmod 755 ufw-dynamic-ip-updater.py

 Put the following line in root's cron (you can run "sudo crontab -e"), it will execute every 2 min. (change the way you prefer):

    */2 * * * * /root/ufw-dynamic-ip-updater.py -f /root/relay.json -v >> /root/relay.log 2>&1

 Make sure you have "ufw", "getent" and "python3" installed. Python3 should reside in: "/usr/bin/python3".

 Verify that the variables point to the correct location of these programs in your OS. Change the paths if needed in the "ufw-dynamic-ip-updater.py" script, lines 31 and 32:
 
    GETENT =  "/usr/bin/getent"
    UFW = "/usr/sbin/ufw"

## How it works

Cron runs "ufw-dynamic-ip-updater.py" script every 2 minutes, and it:
 - Reads the dynamic ip hostnames listed in relays.json and resolves the addresses using the "getent" software.
 - Verifies if any of the IPs have changed, and if so updates ufw rules.
 - Dumps a new "relays.json" with new IPs.

## Some features implemented

 - Format checkings for the hostname addresses and IPv4 addresses.
 - Format checkings for the .json file.
 - Verbose mode allows to check the output "relay.log" file.

## NOTE:

 If you liked it, consider delegating your ADA to [BioStakingPool - BIO](https://biostakingpool.hopto.org) - this is Darwin's Stake Pool ;-)

 Or if you prefer, donate lovelaces to:  
    
    addr1q8dcts6dqy4x28kazkt6snqkskpf7wl0awa9m3xqzv3nnyxg66dcjy55dyrnplgszvzfj6gv3unjk0n3w4qhvvka2ufqmj9nt0

## LICENSE

ufw-dynamic-ip-updater.py is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Additional permission under GNU GPL version 3 section 7

If you modify this Program, or any covered work, by linking or combining
it with Chado (or a modified version of that library), containing parts
covered by the terms of Artistic License 2.0, the licensors of this Program
grant you additional permission to convey the resulting work. {Corresponding
Source for a non-source form of such a combination shall include the source
code for the parts of Chado used as well as that of the covered work.}

See LICENSE.txt for complete gpl-3.0 license.

