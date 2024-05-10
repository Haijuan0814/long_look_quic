# Setup Details

## Building Chromium on Ubuntu 

To make sure of available space for chromium setup
Change HOME dir to /proj/FEC, path which has sufficient space

```bash
sudo apt install gperf
sudo apt install libnss3-dev libgdk-pixbuf2.0-dev libgtk-3-dev libxss-dev
```

Follow 
https://chromium.googlesource.com/chromium/src/+/main/docs/linux/build_instructions.md

chrome --version

## Get chrome driver 

https://chromedriver.chromium.org/getting-started
https://chromedriver.chromium.org/downloads/version-selection

## Building QUIC 

```bash
gn gen out/Debug
```

Follow
https://www.chromium.org/quic/playing-with-quic/

Certs:
* Make sure to update leaf.cnf if you choose to use different domain or IP and then generate certs
* Add ca root key to OS so that client can use that
* Get SPKI of server public key so chromium can accept self-signed certs

```bash
# quic server
out/Debug/quic_server --port=10001 --quic_response_cache_dir=/proj/FEC-HTTP/long-quic/quic-data/www.example.org   --certificate_file=net/tools/quic/certs/out/leaf_cert.pem --key_file=net/tools/quic/certs/out/leaf_cert.pkcs8

# quic client
out/Debug/quic_client --host=10.10.1.1 --port=6121 --allow_unknown_root_cert https://www.example.org/

```

Use Chromium as client


> Due to issue in running chromium --headless in VM with not display. Only selenium script is used.

```bash
out/Default/chrome  --no-sandbox --headless --disable-gpu --remote-debugging-port=9222  --user-data-dir=/tmp/chrome-profile  --ignore-certificate-errors-spki-list=$(cat net/tools/quic/certs/out/server_pub_spki.txt)  --no-proxy-server   --enable-quic   --origin-to-force-quic-on=www.example-quic.org:443   --host-resolver-rules='MAP www.example-quic.org:443 10.10.1.1:10001'
```


## Building HTTPS server ( HTTP/2 , TLS, TCP )

Apache2   
[Get Apache2](https://www.digitalocean.com/community/tutorials/how-to-install-the-apache-web-server-on-ubuntu-22-04)

Flask


## Starting Servers


### TCP

```bash
# simple python server
python server.py  

# OR

# Apache + Flask
# TODO
```

### QUIC

```bash
# start quic server
quic_server
```



## Automating Test

Selenium to driver browser and Python scripts for everything else.


## Getting Metrics

* Selenium
* chrome-har-capturer - Gets details network stats

### HAR capturer

AT Client side

**Install**
npm install -g chrome-har-capturer


#### QUIC

**Start chromium headless for quic**
```bash
out/Default/chrome  --no-sandbox --headless --disable-gpu --remote-debugging-port=9222  --user-data-dir=/tmp/chrome-profile  --ignore-certificate-errors-spki-list=$(cat net/tools/quic/certs/out/server_pub_spki.txt)  --no-proxy-server   --enable-quic   --origin-to-force-quic-on=www.example-quic.org:443   --host-resolver-rules='MAP www.example-quic.org:443 10.10.1.1:6121'
```

**Get request using har-caturer**
```bash
chrome-har-capturer --force --port 9222 -o quic_index.har https://www.example-quic.org/
- https://www.example-quic.org/ ✓
```


#### TCP

**Start chromium headless for tcp**
```bash
out/Default/chrome  --no-sandbox --headless --disable-gpu --remote-debugging-port=9222  --user-data-dir=/tmp/chrome-profile --disk-cache-dir=/dev/null  --ignore-certificate-errors-spki-list=$(cat /proj/FEC-HTTP/long-quic/https/server_pub_spki.txt)  --no-proxy-server   --disable-quic   --origin-to-force-quic-on=www.example-tcp.org:8888   --host-resolver-rules='MAP www.example-tcp.org:8888 10.10.1.1:8000'
```

**Get request using har-caturer**
```bash
chrome-har-capturer --force --port 9222 -o tcp_index.har https://www.example-tcp.org:8888
- https://www.example-tcp.org:8888/ ✓
```


Use metrics in har file to calculate page load time



# Sources:

1. TownesZhou [CS536-Network-Project](https://github.com/TownesZhou/CS536-Network-Project)
