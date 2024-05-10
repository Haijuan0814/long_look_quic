# Script to test quic server using chromium as client
# Use server public key's skpi to get chromium to connect 
# to quic server which is using self-signed certificate

from selenium import webdriver
# from selenium.webdriver.common.keys import Keys

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

chrome_options = Options()
#chrome_options.add_argument("--disable-extensions")
#chrome_options.add_argument("--disable-gpu")
#chrome_options.add_argument("--no-sandbox") # linux only
chrome_options.add_argument("--headless")
# chrome_options.headless = True # also works

chrome_options.add_argument('--user-data-dir=/tmp/chrome-profile')
chrome_options.add_argument("--no-proxy-server")
chrome_options.add_argument('--enable-quic')
chrome_options.add_argument('--origin-to-force-quic-on=www.examplequic.org:443')
chrome_options.add_argument('--quic-host-whitelist=www.examplequic.org');
chrome_options.add_argument('--host-resolver-rules=MAP www.examplequic.org:443 10.10.1.1:6121')
chrome_options.add_argument('--ignore-certificate-errors-spki-list=Tz6CyL8WC55nA6yDXagMahDsUFOBBA+slB7q3RphY88=')
chrome_options.add_argument('--allow_unknown_root_cert')

# Speficy custom browser path using chrome options
webdriver.ChromeOptions.binary_location = "/proj/FEC-HTTP/long-quic/chromium/src/out/Default/chrome"
chrome_service = Service("/proj/FEC-HTTP/long-quic/chromedriver_linux64/chromedriver")

# create driver instance
driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

driver.get("https://www.examplequic.org/")

print(driver.title)
print(driver.page_source)

performance_data = driver.execute_script("return window.performance.getEntries();")
print(performance_data[0]['duration'])