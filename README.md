# Cloudflare → Zabbix Status Code Monitor

This repository provides a small integration script that lets Zabbix discover and monitor HTTP status-code metrics from Cloudflare zones. It provisions hosts, exposes a low-level discovery (LLD) rule, and returns the latest 30-minute totals along with the overall 5xx error percentage so you can alert on delivery problems quickly.

## Highlights
- **Automatic host provisioning** – Creates a `Cloudflare_Status_Codes` host group and registers one Zabbix host per configured Cloudflare zone, all wired to use the external script.
- **Low-level discovery integration** – Populates an LLD rule so Zabbix automatically builds one item per discovered status code plus an extra item for the 5xx error percentage.
- **Cached lookups** – Stores the most recent analytics response on disk, allowing subsequent checks to return instantly without re-querying Cloudflare.

## Requirements
- Python 3.6+ on the Zabbix server where the external script will run.
- Zabbix 4.0+ (earlier versions may work but have not been tested).
- A Cloudflare account with API token access to the target zones.
- A Zabbix user with **Super Admin** permissions to create host groups, hosts, LLD rules, and item prototypes.

## Installation
1. Install the Python dependencies:
   ```bash
   sudo pip3 install -r requirements.txt
   ```
2. Copy `cloudflare.py`, `cloudflare.ini`, and `requirements.txt` into Zabbix’s `externalscripts` directory (commonly `/usr/lib/zabbix/externalscripts`, but this can vary by distribution).
3. Ensure the files are owned by the user that runs the `zabbix_server` process so the external script can be executed and cache files can be written under `/var/tmp`.

## Configuration (`cloudflare.ini`)
Populate the INI file with your credentials and the list of zones you want to monitor. The expected structure is:

```ini
[CREDENTIALS]
cloudflare_user = user@example.com
cloudflare_token = your_cloudflare_api_token
zabbix_user = zabbix_admin_user
zabbix_password = zabbix_admin_password
zabbix_url = https://zabbix.example.com

[HOSTS]
# One zone per line. These values are used both for provisioning and metric queries.
hosts_list =
    example.com
    api.example.com
```

Notes:
- `hosts_list` is newline-delimited; indenting with spaces is optional but keeps the list readable.
- The Cloudflare credentials may be either a global API key or a scoped token that grants access to the specified zones.
- The Zabbix URL should point to the API endpoint (normally the main web URL).

## Provisioning Zabbix Objects
Run the script once with `--create` to establish the host group, hosts, discovery rule, and item prototype:

```bash
/usr/bin/python3 /usr/lib/zabbix/externalscripts/cloudflare.py --create
```

For each zone in `hosts_list`, the script will:
1. Create (or reuse) the `Cloudflare_Status_Codes` host group.
2. Register a host named `<zone>_status_codes` with a dummy loopback interface.
3. Attach an external check LLD rule that invokes `cloudflare.py -l <zone>`.
4. Create an item prototype that becomes one item per discovered status code and an additional item called `Porcentaje_errores_500` for the 5xx error percentage.

You can re-run the command safely; existing hosts or host groups will be detected and reused.

## How Data Collection Works
- **Discovery (`-l`)** – Zabbix calls `cloudflare.py -l <zone>` to fetch the latest 30-minute analytics snapshot from Cloudflare. The script prints LLD JSON so Zabbix can (re)discover items and writes the raw status-code counts plus the 5xx percentage to `/var/tmp/status_<zone>.pickle`.
- **Item checks (`-s`)** – When Zabbix evaluates an item, it executes `cloudflare.py -s <zone> <status_code>`. The script loads the cached pickle file and returns the requested count (or `0` if the code was not present). The special key `Porcentaje_errores_500` yields the calculated percentage value.

Because Cloudflare is queried only during discovery runs, make sure your discovery rule interval matches how frequently you want to refresh the cached metrics.

## Verifying Operation
After provisioning, wait for the first discovery cycle to run (by default every 25 minutes after the host is created). You should see:
- A discovery rule named after each zone.
- One item per HTTP status code observed in the last 30 minutes.
- An item called `Porcentaje_errores_500` displaying the integer percentage of 5xx responses.

If you prefer to test manually, run:
```bash
/usr/bin/python3 /usr/lib/zabbix/externalscripts/cloudflare.py -l example.com
/usr/bin/python3 /usr/lib/zabbix/externalscripts/cloudflare.py -s example.com 200
/usr/bin/python3 /usr/lib/zabbix/externalscripts/cloudflare.py -s example.com Porcentaje_errores_500
```

## Troubleshooting Tips
- **Authentication errors** – Double-check your Cloudflare and Zabbix credentials in `cloudflare.ini`. Remember that the Zabbix account must be a Super Admin to create hosts.
- **Permission denied writing cache** – Ensure `/var/tmp` is writable by the Zabbix server user. You can change the cache directory in `cloudflare.py` if necessary.
- **Missing metrics** – Only status codes returned by the Cloudflare analytics API within the last 30 minutes appear. If traffic is low, some codes may be absent and will return `0` until observed.

## Extending the Integration
The script is intentionally simple. Potential enhancements include adding more Cloudflare analytics (e.g., bandwidth, threats), introducing logging, or porting the workflow to a container for easier deployment. Start by reviewing `cloudflare.py` to understand how discovery payloads and cached metrics are built.

---
Author: Simon Malave (<simongmalav@gmail.com>)
