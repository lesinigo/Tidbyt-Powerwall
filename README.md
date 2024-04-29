# Tidbyt-Powerwall

Show Tesla Powerwall data on your Tidbyt, without giving your Tesla credentials
to anyone!

This script will fetch Powerwall data from its local API, not from the Tesla
servers API. This requires you to have the Powerwall connected via LAN or Wi-Fi
to a network and run this script in the same network[*].

Fetching data from a Powerwall that's connected via its integrated cellular
service is not supported.

[*] of course, advanced users can setup VPNs or reverse proxies and run the
script in a different network.

## configuration

* set your local Powerwall URL and password in environment variables
  `TPW_ADDRESS` and `TPW_PASSWORD`
* set your Tidbyt device ID and API key in environment variables `TPW_DEVICEID`
  and `TPW_APIKEY`
* set your timezone in environment variable `TZ`

## how to run Tidbyt-Powerwall

### in a Python venv

```sh
# install & config - first time only
python3 -m venv <YOUR DIRECTORY OF CHOICE>
<YOUR DIRECTORY OF CHOICE>/bin/pip install .
vim tidbyt_powerwall.env    # export TPW_* configuration variables
# start it
source <YOUR DIRECTORY OF CHOICE>/tidbyt_powerwall.env
<YOUR DIRECTORY OF CHOICE>/bin/tidbyt_powerwall
```

### in a container

```sh
# build & config - first time only
podman build -t tidbyt_powerwall .
vim tidbyt_powerwall.env    # set TPW_* configuration variables
# start it
podman run -d --env-file tidbyt_powerwall.env --restart=always tidbyt_powerwall
```
