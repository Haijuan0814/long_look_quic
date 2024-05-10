'''
Description
'''

import sys, os, time, json, subprocess, traceback, random, string
from pythonLib import *
from engineChrome import TCPDUMP, initialize, beforeExit, timeout, TimeoutError

# This might timeout for large file (10mb) [default: 3*60, extreme: 100*60]
browserLoadTimeout = 3*60

class Driver(object):
    def __init__(self):
        self.process         = None
        self.pageLoadTimeout = str(Configs().get('pageLoadTimeout'))

    # Starts browser
    def open(self, browserPath, options, debugPort):
        self.randomID  = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(10))
        self.debugPort = debugPort
        cmd            = [browserPath] + options + ['--remote-debugging-port={}'.format(self.debugPort), '--randomID={}'.format(self.randomID)]
        self.process   = subprocess.Popen(cmd)
        time.sleep(3)
        
    # Closes browser    
    def close(self):
        '''
        This is a hack I came up with to close the browser. Everytime a browser window is opened, it's ran with a dummy "--randomID" switch.
        When closing, this function kills processes with this randomID in their name.
        '''
        os.system('sudo pkill -f {}'.format(self.randomID))
    
    # Request resource and capture timings using har-capturer
    @timeout(browserLoadTimeout)
    def get(self, capture_options, url, outFile):
        cmd = ['chrome-har-capturer'] + capture_options + [ '--give-up', self.pageLoadTimeout, '--port', self.debugPort, '-o', outFile, url]

        print(' '.join(cmd))
        self.process  = subprocess.Popen(cmd)
        self.process.communicate()

        try:
            with open(outFile, 'r') as f:
                j = json.load(f)
                print('\t\t', j['log']['pages'][0]['pageTimings']['onLoad'])
        except:
            pass

def main():
    #The following line is to make sure the script has sudo privilage to run tcpdump
    os.system('sudo echo')


    #Setting up configs
    PRINT_ACTION('Reading configs file and args', 0)
    configs, cases, methods, testDir, resultsDir, statsDir, userDirs, screenshotsDir, dataPaths, netLogs, tcpdumpDir, tcpdumpFile, uniqeOptions = initialize()
    configs.show_all()

    #Creating options
    '''
    IMPORTANT: --enable-benchmarking --enable-net-benchmarking: to enable the Javascript interface that allows chrome-har-capturer to flush the DNS cache and the socket pool before loading each URL.
               in other words, clear cache and close connections between runs! 
    '''
    PRINT_ACTION('Creating options', 0)
    drivers       = {}    
    # Stats module missing
    chromeOptions = {}      # Options for Chrome
    harcaptureOptions = []  # Options for chrome-har-capturer
#     commonOptions = ['--no-first-run']
    commonOptions = [
                        '--no-sandbox',
                        '--disable-gpu',
                        '--no-first-run',
                        '--disable-background-networking', 
                        '--disable-client-side-phishing-detection', 
                        '--disable-component-update', 
                        '--disable-default-apps', 
                        '--disable-hang-monitor', 
                        '--disable-popup-blocking', 
                        '--disable-prompt-on-repost', 
                        '--disable-sync', 
                        '--disable-web-resources', 
                        '--metrics-recording-only', 
                        '--password-store=basic', 
                        '--safebrowsing-disable-auto-update', 
                        '--use-mock-keychain', 
                        '--ignore-certificate-errors'
                    ] 
    
    # if Not using xvfb-run , Then use  chrome headless mode
    # Old chrome and chrome-har-capturer doesn't work well
    if not configs.get('xvfb'):
        commonOptions += ['--headless']

    if configs.get('clearCacheConns'):
        commonOptions += ['--enable-benchmarking', '--enable-net-benchmarking']    

    # add options for 0-RTT for quic RFCv1, in new chrome-har-capturer
    # For gQUIC v37, we use old chrome-har-capturer(v0.9.5) version which uses 0-RTT
    if configs.get('zeroRtt') and configs.get('quic-version') == 'RFCv1':
        # To make sure chrome sends 0-RTT packets for quic RFCv1, even after closing connections
        # We do two things , 
        # --cache = Which make sures no new Chrome Context is created (new incognito profile), required for TLS 0-RTT to work 
        # --user-metric = We pass runtime commands to clear cache and close connections , required to close connections without closing browser context.
        harcaptureOptions += ['--cache', '--user-metric',
        'chrome.benchmarking.clearCache();chrome.benchmarking.clearHostResolverCache();chrome.benchmarking.clearPredictorCache();chrome.benchmarking.closeConnections();']

    debugPorts = {
                'https'       : str(configs.get('httpsDebugPort')),
                'quic'        : str(configs.get('quicDebugPort')),
                }

    #Creating driver instances and modifying /etc/hosts
    PRINT_ACTION('Creating driver options and modifying /etc/hosts', 0)
    for case in cases:
        
        drivers[case] = Driver()
        
        chromeOptions[case] = []
        unCommonOptions     = ['--user-data-dir={}/{}'.format(userDirs, case),
                               '--data-path={}/{}'.format(dataPaths, case),
                               ]
        
        if configs.get('logNetlog'):
            unCommonOptions += ['--log-net-log={}/{}.json'.format(netLogs, case),]
         
        chromeOptions[case] = uniqeOptions[case] + commonOptions + unCommonOptions
        
        if not configs.get('closeDrivers'):
            print('\tFor: {}...\t'.format(case), end=' '); sys.stdout.flush()
            drivers[case].open(configs.get('browserPath'), chromeOptions[case], debugPorts[case])
            print('Done')    
            
    # Starting TCPDUMP (Client side)
    if configs.get('tcpdump'):
        # if seperate dumps are enabled for each request, don't start now
        if configs.get('separateTCPDUMPs'):
            tcpdumpObj = None
        # if No seperate dumps are enabled , start now
        else:
            PRINT_ACTION('Starting TCPDUMP', 0)
            tcpdumpObj = TCPDUMP()
            print(tcpdumpObj.start(tcpdumpFile, interface=configs.get('networkInt'), ports=[configs.get("httpsServerPort"), configs.get("quicServerPort")], hosts=[configs.get("httpsServerIP")]))
            tcpdumpObj.start(tcpdumpFile, interface=configs.get('networkInt'), ports=[configs.get("httpsServerPort"), configs.get("quicServerPort")], hosts=[configs.get("httpsServerIP")])
    else:
        tcpdumpObj = None

    # Asking remote host to start QUIC server
    logName     = False
    tcpprobePid = False

    # Asking remote host to start runTcpProbe

    
    # Generate side Traffic

    #Firing off the tests
    PRINT_ACTION('Firing off the tests', 0)
    for round in range(1, configs.get('rounds')+1):
        for case in cases:
            testID = '{}_{}'.format(case, round)
            PRINT_ACTION('Doing: {}/{}'.format(testID, configs.get('rounds')), 1, action=False)            
            
            url = '{}://{}/{}'.format(methods[case], configs.get('host')[case], configs.get('testPage'), testID)            

            # Do stats
            # Do TCP dump, if separate dumps are needed , start here now.    
            if configs.get('separateTCPDUMPs') and configs.get('tcpdump'):
                tcpdumpFile = '{}/{}_{}_tcpdump.pcap'.format(tcpdumpDir, os.path.basename(testDir), testID)
                tcpdumpObj  = TCPDUMP()
                if case == 'https':
                    tcpdumpObj.start(tcpdumpFile, interface=configs.get('networkInt'), ports=[configs.get("httpsServerPort")], hosts=[configs.get("httpsServerIP")])
                elif case == 'quic':
                    tcpdumpObj.start(tcpdumpFile, interface=configs.get('networkInt'), ports=[configs.get("quicServerPort")], hosts=[configs.get("quicServerIP")])
                else: # generic capturing for both
                    tcpdumpObj.start(tcpdumpFile, interface=configs.get('networkInt'), ports=[configs.get("httpsServerPort"), configs.get("quicServerPort")], hosts=[configs.get("httpsServerIP")])

            if configs.get('closeDrivers'):
                PRINT_ACTION('Opening driver: '+ testID, 2, action=False)
                drivers[case].open(configs.get('browserPath'), chromeOptions[case], debugPorts[case])
            try:
                drivers[case].get(harcaptureOptions, url, resultsDir + '/' + testID + '.har')
            except TimeoutError:
                    print('Browser load timeout ({}) happend!!!'.format(browserLoadTimeout))
                    os.system('sudo pkill -f chrome-har-capturer')
                    time.sleep(5)
            except Exception as e:
                print('###### EXCEPTION during {}#######'.format(testID))
                print(e)
                traceback.print_exc()
                continue
            
            if configs.get('separateTCPDUMPs') and configs.get('tcpdump'):
                tcpdumpObj.stop()

            # Save stats

            if configs.get('closeDrivers'):
                PRINT_ACTION('Closing drivers', 0)
                drivers[case].close()
             
            time.sleep(configs.get('waitBetweenLoads'))

        if round != configs.get('rounds'):
            PRINT_ACTION('Sleeping between rounds: {} seconds ...'.format(configs.get('waitBetweenRounds')), 0)
            time.sleep(configs.get('waitBetweenRounds'))
            
    PRINT_ACTION('Running final beforeExit ...', 0)
    # Stop background pings
    if configs.get('closeDrivers'):
        drivers=None
    if configs.get('separateTCPDUMPs'):
        tcpdumpObj=None
    beforeExit(tcpdumpObj=tcpdumpObj, drivers=drivers, modifyEtcHosts=None, logName=logName, tcpprobePid=tcpprobePid)
    

if __name__=="__main__":
    main()    
