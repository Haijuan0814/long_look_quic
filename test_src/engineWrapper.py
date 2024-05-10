'''

'''

import sys, os, multiprocessing, time
from pythonLib import *
from doTrafficStuff import DummyNet, TC

obj_set1  = [ '5k.html', '10k.html', '100k.html', '200k.html', '500k.html', '1mb.html', '10mb.html',]  
obj_set2  = [ '1mbx1.html','500kx2.html' ,'200kx5.html' ,'100kx10.html', '10kx100.html', '5kx200.html' ]  

# all rates (scenarios)
# 10_36_1 => 10 Mbits/s , 36 ms RTT , 1% loss
# 100_100J10_0 => 100 Mbits/s, 100ms RTT with 10 ms jitter , 0% loss    ( Latency is varied on local interface to avoid delay )
# 50V150_36_0 => Varying bandwith from 50 Mbits/s to 150 Mbits/s  , 36ms RTT, 0% loss ( Bandwidth is varied in link Bridge to avoid delay [Not Automated])
## BUG in config.read_args when just one --rates="100_36_1" is given . It takes as 100361 . so give min 2 "100_36_1,50_36_1"
ratesX = "10_36_0,50_36_0,100_36_0,10_112_0,50_112_0,100_112_0,10_36_1,50_36_1,100_36_1,10_112J50_0,50_112J50_0,100_112J50_0"

# All objects
indexX = "5k,10k,100k,200k,500k,1mb,10mb,1mbx1,500kx2,200kx5,100kx10,10kx100,5kx200"

# Configs for running experiments , 
# different from configs controlling chrome options, servers etc
def initialize():
    configs = Configs()

    configs.set('project', 'FEC-HTTP')
    configs.set('experiment', 'Q043')
    # give python path of virtual env with all required modules
    configs.set('pythonBinary', '/proj/FEC-HTTP/nenv/bin/python')
    configs.set('mainDir', '')

    configs.set('rates'             ,  "10_36_0,50_36_0,100_36_0,10_112_0,50_112_0,100_112_0,10_36_1,50_36_1,100_36_1,10_112J50_0,50_112J50_0,100_112J50_0")
    # configs.set('qualities'         , 'hd2160,hd1440,hd1080,hd720,large,medium,small,tiny,auto')
    configs.set('stopTime'          , '60')
    # 
    configs.set('indexes'           , "5k,10k,100k,200k,500k,1mb,10mb,1mbx1,500kx2,200kx5,100kx10,10kx100,5kx200")
    configs.set('networkInt'        , 'eth0')
    configs.set('rounds'            , 20)
    configs.set('tcpdump'           , False)
    configs.set('doSideTraffic'     , False)
    configs.set('runQUICserver'     , False)
    configs.set('runTcpProbe'       , False)
    configs.set('doJitter'          , False)
    configs.set('doIperf'           , True)
    configs.set('doPing'            , True)
    configs.set('xvfb'              , True)     # Use xvfb when headless mode is not used
    configs.set('closeDrivers'      , False)
    configs.set('clearCacheConns'   , True)
    configs.set('zeroRtt'           , True)     # Use this along with xvfb, Since some runtime commands don't work in headless mode
    configs.set('separateTCPDUMPs'  , False)
    configs.set('browserPath'       , False)
    configs.set('addPeakRate'       , False)
    configs.set('lossArgs'          , False)
    configs.set('delayArgs'         , False)
    configs.set('changeBW'          , False)
    configs.set('logNetlog'         , False)
    configs.set('latencyOrLimit'    , 'latency')
    configs.set('against'           , 'emulab')
    configs.set('cases'             , 'https,quic')
    configs.set('quic_server_path'  , '')
    configs.set('script2run'        , 'engineChrome_harCapturer.py')
    
    configs.read_args(sys.argv)
    configs.show_all()

    if configs.get('xvfb'):
        configs.set('xvfb-run', 'xvfb-run')
    else:
        configs.set('xvfb-run', '')

    return configs


def run(configs, link, tc):

    for rate in configs.get('rates').split(','):

        ### Get Traffic condition to test ###
        bw = rate.split('_')[0]
        delay = rate.split('_')[1]
        plr = rate.split('_')[2]

        print("Bandwidth :", bw)
        print("Delay :", delay)
        print("Loss :", plr)

        # If Jitter is required 
        # perform Jitter on local interface using tc
        # Just pass bw to dummynet with 0 latency
        # if 36 ms implicit latency is needed , pass 36 ms to dummynet. and remaining as base for TC
        if 'J' in delay:
            configs.set('doJitter', True)
            base_delay = int(delay.split('J')[0])
            var_delay = int(delay.split('J')[1])
            baseDelayDown = base_delay/2
            baseDelayUp = base_delay/2
            varDelayDown = var_delay/2
            varDelayUp = var_delay/2
            # Don't change via dummynet
            # delay = 0 

            # Change via dummynet
            # implicit latency at dummynet, remaining latency at TC
            implicit_latency = 36
            delay = implicit_latency
            baseDelayDown = (base_delay - implicit_latency)/2
            baseDelayUp = (base_delay - implicit_latency)/2



        bw = int(bw)
        delay = int(delay)
        plr = int(plr)

        # queue is set to (2x) BDP of the current setting in bytes
        # B * Delay
        # For higher bandwith (eg. 500Mbps) the queue will be larger than dummynet limit
        # make sure to update dummynet limit for that many bytes
        # sysctl net.inet.ip.dummynet.pipe_byte_limit=
        queue = int((bw*pow(10, 6)*delay*pow(10, -3))/8) * 2

        print("queue :", queue)
        ### Do traffic shaping ###
        # Validate before
        link.show()

        # Add shapping paramters uniformly for up and down links
        # Bandwidth (bw) : Same bw is applied for both up and down links
        # DELAY : Delay is halved and applied for both up and down links
        # PLR : Loss from range (0-1) [meaning 0-100%] is applies for both links
        link.add(bw, (delay/2), ((plr/2)/100), queue)

        # Validate After 
        link.show()

        if configs.get('doJitter'):
            # Vaidate Before
            tc.show()
            # Set base latency
            
            tc.doDelay(baseDelayDown, baseDelayUp)
            # Vaidate After
            tc.show()

            # Do Jitter
            pJitter  = multiprocessing.Process(target=tc.addJitter, 
                                                args=( baseDelayDown, varDelayDown,baseDelayUp, varDelayUp))
            # Start Jitter Process
            pJitter.start()


        ### Create Directory ###
        dirName = rate
        print('Creating directory')
        os.system('mkdir -p {}/{}'.format(configs.get('mainDir'), dirName))

        

        ### Run network tests ###
        if configs.get('doIperf'):
            print('Running iperf ...')
            if configs.get('against') == 'emulab':
                # iperfServer = "[iPerf should be running on the same host as QUIC/HTTPS server]"
                iperfServer = "192.168.1.1"
            print('./do_iperf.sh {}/{}/ {}'.format(configs.get('mainDir'), dirName, iperfServer))
            os.system('./do_iperf.sh {}/{}/ {}'.format(configs.get('mainDir'), dirName, iperfServer))
            ### Save System Info ###
            print('./do_sysinfo.sh {}/{}/ {}'.format(configs.get('mainDir'), dirName, iperfServer))
            os.system('./do_sysinfo.sh {}/{}/ {}'.format(configs.get('mainDir'), dirName, iperfServer))
        
        if configs.get('doPing'):
            print('Running pings ...')
            if configs.get('against') == 'emulab':
                # pingServer = "[QUIC/HTTPS server host address]"
                pingServer = "192.168.1.1"
            print('./do_ping.sh {}/{}/ {}'.format(configs.get('mainDir') , dirName, pingServer))
            os.system('./do_ping.sh {}/{}/ {}'.format(configs.get('mainDir'), dirName, pingServer))

        ### Run benchmark scripts ###
        for index in configs.get('indexes').split(','):
            cmd  = '{} {} {} '.format(configs.get('xvfb-run'), configs.get('pythonBinary'), configs.get('script2run'))
            cmd += '--against={} --networkInt={} '.format(configs.get('against'), configs.get('networkInt'))
            cmd += '--browserPath={} --quic-version={} '.format(configs.get('browserPath'), configs.get('quic-version') )
            cmd += '--cases={} '.format(configs.get('cases'))
            cmd += '--tcpdump={} separateTCPDUMPs={} '.format(configs.get('tcpdump'), configs.get('separateTCPDUMPs'))
            cmd += '--logNetlog={} '.format(configs.get('logNetlog'))
            cmd += '--xvfb={} ' .format(configs.get('xvfb'))
            cmd += '--mainDir={} '.format(configs.get('mainDir'))
            # for html pages
            cmd += '--testDir={}/{}_html --testPage={}.html '.format(dirName, index, index)
            # for static image objects
            # cmd += '--testDir={}/{}_jpg --testPage=static/{}.jpg '.format(dirName, index, index)
            cmd += '--rounds={} '.format(configs.get('rounds'))
            print('\tThe command:\n\t', cmd)
            os.system(cmd)

        ### Clear network settings and stop process ###
        if configs.get('doJitter'):
            pJitter.terminate() 
            tc.remove()

        link.remove()

        print()        

def main():
    PRINT_ACTION('Reading configs file and args', 0)
    configs = initialize()
    # Create Dummynet Object - Used to change traffic shaping at link bridge
    link = DummyNet(configs.get('project'), configs.get('experiment'), "link_bridge")
    # Create TC object - Used to change traffic shaping locally using TC
    tc = TC(configs.get('networkInt'))

    PRINT_ACTION('Running...', 0)
    run(configs, link, tc)
    
if __name__ == "__main__":
    main()