'''
Description
'''

try:
    from selenium import webdriver
except ImportError:
    print('\n####################################################################')
    print('SELENIUM NOT AVAILABLE!!! You can only run tests using HAR capturer!!!')
    print('####################################################################\n')
# import sys, os, time, pickle, socket, json, subprocess, traceback, multiprocessing, subprocess
import time 
# import stats                  # Module not found
# import sideTrafficGenerator   # Module not found
from pythonLib import *         # Custom python file
from functools import wraps
import errno
import os
import signal

class TimeoutError(Exception):
    pass

def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator

class TCPDUMP(object):
    def start(self, outFile, interface=None, ports=None, hosts=None):
        self.command = ['sudo', 'tcpdump', '-w', outFile]
        
        if interface:
            self.command += ['-i', interface]
        
        if ports:
            self.command += ['port', ports.pop()]
            while ports:
                self.command += ['or', 'port', ports.pop()]

            if hosts:
                self.command += ['and']
        
        if hosts:
            self.command += ['host', hosts.pop()]
            while hosts:
                self.command += ['or', 'host', hosts.pop()]
        
        self.p  = subprocess.Popen(self.command)
        
        PRINT_ACTION('Sleeping 3 seconds so tcpdump starts', 0)
        time.sleep(3)
        
        self.command = ' '.join(self.command)
        
        return self.command
    
    def stop(self):
        '''
        I cannot use subprocess kill because the process has started with sudo
        Unless I change groups and users and stuff, I do need to run tcpdump
        with sudo.
        '''
        
        os.system('sudo pkill -f "{}"'.format(self.command))
        time.sleep(3)


# SELENIUM version of Driver class. (Not used due to lack of detailed timings)
class Driver(object):
    def __init__(self, chromeDriverPath, browserPath, options, pageLoadTimeOut=None):
        self.chromeDriverPath = chromeDriverPath
        self.browserPath      = browserPath
        self.options          = options
        self.pageLoadTimeOut  = pageLoadTimeOut
        self.driver           = None    

    @timeout(20)
    def open(self):
        webdriver.ChromeOptions.binary_location = self.browserPath
        chromeService = webdriver.chrome.service.Service(self.chromeDriverPath)
        
        self.driver = webdriver.Chrome(service=chromeService, options=self.options)
        
        if self.pageLoadTimeOut:
            self.driver.set_page_load_timeout(self.pageLoadTimeOut)

    @timeout(20)
    def close(self):
        self.driver.close()
        self.driver.quit()
        
    def get(self, url):
        self.driver.get(url)

    def clearCacheAndConnections(self):
        self.driver.execute_script("return chrome.benchmarking.clearCache();")
        self.driver.execute_script("return chrome.benchmarking.clearHostResolverCache();")
        self.driver.execute_script("return chrome.benchmarking.clearPredictorCache();")
        self.driver.execute_script("return chrome.benchmarking.closeConnections();")


def beforeExit(tcpdumpObj=None, drivers=None, modifyEtcHosts=None, logName=False, tcpprobePid=False):
    
    configs = Configs()
    
    #Killing TCPDUMP
    if tcpdumpObj:
        PRINT_ACTION('Killing TCPDUMP', 0)
        if configs.get('tcpdump'):
            tcpdumpObj.stop()
     
    #Asking remote host to stop QUIC server
    
    #Asking remote host to stop tcpProbe
    
    #Reverting modifications to /etc/hosts

    #Closing drivers
    if drivers:
        PRINT_ACTION('Closing drivers', 0)
        for case in drivers:
            try:
                drivers[case].close()
                print("Close Driver Success")
            except TimeoutError:
                print('Got stuck closing drivers! :-s')
    
    time.sleep(3)


def initialize():
    configs = Configs()

    configs.set('waitBetweenLoads'  , 2)
    configs.set('waitBetweenRounds' , 1)
    configs.set('rounds'            , 10)
    configs.set('pageLoadTimeout'   , 120)

    # Debug files
    configs.set('tcpdump'           , False)
    configs.set('separateTCPDUMPs'  , False)

    configs.set('runTcpProbe'       , False)

    configs.set('logNetlog'         , False)

    configs.set('closeDrivers'      , False)
    configs.set('clearCacheConns'   , True)
    configs.set('zeroRtt'           , True)

    configs.set('browserPath'       , False)

    configs.set('quicServerIP'      , "192.168.1.1")
    configs.set('quicServerPort'    , "6121")


    configs.set('httpsServerIP'     , "192.168.1.1")
    configs.set('httpsServerPort'   , "443")

    configs.set('quicDebugPort'     , "9222")
    configs.set('httpsDebugPort'    , "9221")


    configs.set('cases'             , 'https,quic')

    configs.set('mainDir'           , os.path.abspath('../data') + '/results')

    configs.read_args(sys.argv)

    '''
    Important: the following MUST be done AFTER read_args in case "--against" gets overridden 
    '''
    if configs.get('against') == 'emulab':
        configs.set('host', {'quic'         :'www.example-quic.org',
                             'https'        :'www.example-tcp.org',})
        
    configs.check_for(['testDir', 'testPage', 'networkInt', 'quic-version'])
    
    if configs.get('testDir').endswith('/'):
        configs.set( 'testDir', configs.get('testDir')[:-1] )
    
    # configs.set('chromedriver', selectChromeDriverPath(configs.get('browserPath'), configs.get('platform')))
    
    configs.set('testDir', configs.get('mainDir') + '/' + configs.get('testDir') )
    
    if os.path.isdir(configs.get('testDir')):
        print('Test directory already exists! Use another name!')
        sys.exit()
    
    # Add Cert SPKI , Needed for Modern Chrome Browsers
    quic_spki_file = "/proj/FEC-HTTP/long-quic/long-look-quic/quic/out/server_pub_spki.txt"
    if os.path.isfile(quic_spki_file):
        with open(quic_spki_file, 'r') as file:
            quic_spki = file.read()
        configs.set('quic_spki', quic_spki)  
    else:
        print('QUIC server SPKI file does not exists!. Create SPKI using server public key ')
        sys.exit()

    tcp_spki_file = "/proj/FEC-HTTP/long-quic/apache-selfsigned-spki.txt"
    if os.path.isfile(tcp_spki_file):
        with open(tcp_spki_file, 'r') as file:
            tcp_spki = file.read()
        configs.set('tcp_spki', tcp_spki)  
    else:
        print('TCP server SPKI file does not exists!. Create SPKI using server public key')
        sys.exit()


    #Creating the necessary directory hierarchy
    PRINT_ACTION('Creating the necessary directory hierarchy', 0)        
    testDir         = configs.get('testDir')
    resultsDir      = '{}/resultsDir'.format(testDir)
    statsDir        = '{}/statsDir'.format(testDir)
    userDirs        = '{}/userDirs'.format(testDir)
    screenshotsDir  = '{}/screenshots'.format(testDir)
    dataPaths       = '{}/dataPaths'.format(testDir)
    netLogs         = '{}/netLogs'.format(testDir)
    tcpdumpDir      = '{}/tcpdumps'.format(testDir)
    tcpdumpFile     = '{}/{}_tcpdump.pcap'.format(testDir, os.path.basename(testDir))
    configsFile     = '{}/{}_configs.txt'.format(testDir, os.path.basename(testDir))
      
    os.system('mkdir -p {}'.format(resultsDir))
    os.system('mkdir -p {}'.format(statsDir))
    os.system('mkdir -p {}'.format(userDirs))
    os.system('mkdir -p {}'.format(screenshotsDir))
    os.system('mkdir -p {}'.format(dataPaths))
    os.system('mkdir -p {}'.format(netLogs))
    os.system('mkdir -p {}'.format(tcpdumpDir))
     
    #Write configs to file (just for later reference)
    configs.write2file(configsFile)
    
    cases         = configs.get('cases').split(',')
    methods       = {'quic'         :'https', 
                     'https'        :'https'}
    
    uniqeOptions  = {'quic' : [
                             '--enable-quic',
                             '--origin-to-force-quic-on={}:443'.format(configs.get('host')['quic']),
                             '--host-resolver-rules=MAP {}:443 {}:{}'.format(configs.get('host')['quic'], configs.get('quicServerIP'), configs.get('quicServerPort')),
                             '--ignore-certificate-errors-spki-list={}'.format(configs.get('quic_spki')),
                             ],
                    
                    'https': [
                             '--disable-quic',
                             '--host-resolver-rules=MAP {}:443 {}:{}'.format(configs.get('host')['https'], configs.get('httpsServerIP'), configs.get('httpsServerPort')),
                             '--ignore-certificate-errors-spki-list={}'.format(configs.get('tcp_spki')),
                             ],               
                    }
    
    try:
        configs.get('quic-version')
        uniqeOptions['quic'].append('--quic-version={}'.format(configs.get('quic-version')) )
    except KeyError:
        print("quic-version Not found")
        sys.exit()
    
    
    dIPs = {'quic'          : configs.get('quicServerIP'),
            'https'         : configs.get('httpsServerIP'),
            }
    
    return configs, cases, methods, testDir, resultsDir, statsDir, userDirs, screenshotsDir, dataPaths, netLogs, tcpdumpDir, tcpdumpFile, uniqeOptions

# This is for using selenium only, not called in our experiments
def main():
    #The following line is to make sure the script has sudo privilage to run tcpdump
    os.system('sudo echo')


    #Setting up configs
    PRINT_ACTION('Reading configs file and args', 0)
    # configs, cases, methods, testDir, resultsDir, statsDir, userDirs, screenshotsDir, dataPaths, netLogs, tcpdumpDir, tcpdumpFile, uniqeOptions, modifyEtcHosts = initialize()
    # configs.show_all()
    
    uniqeOptions  = {'quic' : [
                            '--enable-quic',
                            '--origin-to-force-quic-on={}:443'.format("www.example.org"),
                            # '--quic-host-whitelist={}'.format(configs.get('host')['quic']),
                            '--no-proxy-server',
                            '--host-resolver-rules=MAP {}:443 {}:{}'.format("www.example.org", "10.10.1.1", "6121"),
                            ],       
                    'http' : [
                             '--disable-quic',
                             ],
                    
                    'https': [
                             '--disable-quic',
                             ],        
                }

    #Creating options
    # '''
    # IMPORTANT: --enable-benchmarking --enable-net-benchmarking: to enable the Javascript interface that allows chrome-har-capturer to flush the DNS cache and the socket pool before loading each URL.
    #            in other words, clear cache and close connections between runs! 
    # '''
    PRINT_ACTION('Creating options', 0)
    drivers         = {}
    # stat           = stats.Stats() 
    chromeOptions   = {}
    commonOptions   = ['--no-first-run']

    clearCacheConns = True
    if clearCacheConns:
        commonOptions += ['--enable-benchmarking', '--enable-net-benchmarking']

    #Creating driver instances and modifying /etc/hosts
    PRINT_ACTION('Creating driver options and modifying /etc/hosts', 0)
    cases = ['quic'] # add quic

    for case in cases:

        
        # create chrome driver options
        chromeOptions[case] = webdriver.ChromeOptions()
        
        unCommonOptions     = ['--user-data-dir={}/{}'.format('tmp', 'chrome-profile'),
                            # '--data-path={}/{}'.format(dataPaths, case),
#                                '--log-net-log={}/{}.json'.format(netLogs, case),
                            ]
        extraOptions = ['--headless', '--ignore-certificate-errors-spki-list', '--allow_unknown_root_cert']

        for option in uniqeOptions[case] + commonOptions + unCommonOptions + extraOptions :
            chromeOptions[case].add_argument(option)

        print("Chrome Options")
        print(chromeOptions[case])
        # creating driver instances
        drivers[case] = Driver("/proj/FEC-HTTP/long-quic/chromedriver_linux64/chromedriver", "/proj/FEC-HTTP/long-quic/chromium/src/out/Default/chrome", chromeOptions[case])

        drivers[case].open()


    #Firing off the tests
    PRINT_ACTION('Firing off the tests', 0)
    no_of_round = 1
    for round in range(1, no_of_round+1):
        url = "https://www.example.org"
        # stat.start()

        try:
            drivers[case].get(url)
        except Exception as e:
            print('###### EXCEPTION during {}#######'.format(testID))
            print(e)
            traceback.print_exc()
            continue
        # Stop TCP dump
        print("Title")
        print(drivers[case].driver.title)
        print("Source")
        print(drivers[case].driver.page_source)
        windowPerformance = drivers[case].driver.execute_script("return window.performance.getEntriesByType('resource');")

        # print(windowPerformance[0]['duration'])
        print(windowPerformance)

        # json dump performance resource timing

        # statsRes = stat.stop()
        # stat.save("stat.json")

        drivers[case].driver.save_screenshot('{}_{}.png'.format("screenshotsDir", "testID"))

        # Not working due to chrom not found error in execute script
        # Not sure if har-capturer solves this
        # Temp Fix , close chrome between every runs
        # if True:
            # drivers[case].clearCacheAndConnections()

        if True:
            try:
                drivers[case].close()
            except TimeoutError:
                print('Got stuck closing driver! :-s')

        waitBetweenRounds = 1
        time.sleep(waitBetweenRounds)


if __name__=="__main__":
    main()