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

## run in container

```sh
podman build -t tidbyt_powerwall .
vim tidbyt_powerwall.env    # set TPW_* configuration variables
podman run -d --env-file tidbyt_powerwall.env --restart=always tidbyt_powerwall
```

## run in Python venv

```sh
# install & config - first time only
python3 -m venv <YOUR DIRECTORY OF CHOICE>
<YOUR DIRECTORY OF CHOICE>/bin/pip install .
vim tidbyt_powerwall.env    # set TPW_* configuration variables
# start it
source <YOUR DIRECTORY OF CHOICE>/tidbyt_powerwall.env
<YOUR DIRECTORY OF CHOICE>/bin/tidbyt_powerwall
```

## change timezone

Time on the generated Tidbyt screens will be in the default timezone of the
system were the script is running.

If you want to render time in a different timezone simply set the `TZ`
environment variable to the desired timezone.
