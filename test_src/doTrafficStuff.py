'''
Script modified to work for 
Dummynet commands on Link Bridge Node
TC commands on Local (client) node
'''

import sys, os, random, time, multiprocessing, subprocess
from pythonLib import *

class DummyNet(object):
    def __init__(self, projectName, experimentName, nodeName, pipe1='60111', pipe2='60121'):
        self.projectName = projectName
        self.experimentName = experimentName
        self.nodeName = nodeName
        self.pipe1 = pipe1
        self.pipe2 = pipe2 
        self.pipes = [pipe1, pipe2]
        self.sshNode = "ssh {}.{}.{}.emulab.net ".format(nodeName, experimentName, projectName)

    def show(self):
        print('Dummynet on {}:'.format("Link Bridge"))
        os.system("{} 'sudo ipfw pipe show'".format(self.sshNode))

    def remove(self):
        # Remove shaping
        print("Removing traffic shaping...")
        for p in self.pipes:
            # Remove Bandwidth, Set queue to default
            os.system("{} 'sudo ipfw pipe {} config bw  0Mbit/s delay  0ms plr  0 queue 50'".format(self.sshNode,p))


    def add(self, bw, delay, plr, queue):
        dummyCmd1 = 'sudo ipfw pipe {} config '.format(self.pipe1)
        dummyCmd2 = 'sudo ipfw pipe {} config '.format(self.pipe2)

        if bw:
            dummyCmd1 += 'bw {}Mbit/s '.format(bw)
            dummyCmd2 += 'bw {}Mbit/s '.format(bw)

        if delay:
            dummyCmd1 += 'delay  {}ms '.format(delay)
            dummyCmd2 += 'delay  {}ms '.format(delay)
        
        if plr:
            dummyCmd1 += 'plr {} '.format(plr)
            dummyCmd2 += 'plr {} '.format(plr)
        
        if queue:
            dummyCmd1 += 'queue {}bytes '.format(queue)
            dummyCmd2 += 'queue {}bytes '.format(queue)

        print("Add traffic shaping")
        os.system("{} {}".format(self.sshNode, dummyCmd1))
        os.system("{} {}".format(self.sshNode, dummyCmd2))

    # For variable bandwitdh
    def changeBW_linkbridge(self, what, delay, baseBW, varBW, sleep):
        if what == 'start':
            dummyCmd = 'python bandwidth_oscillator_on_linkbridge.py  {} {} {} {} {} {}'.format(self.pipe1, self.pipe2, delay, baseBW, varBW, sleep)
            os.system("{} {}", self.sshNode, dummyCmd)
        if what == 'stop':
            # Testing kill command
            pass

    # Performa Jitter locally on link_bridge 
    # to achieve high frequency change in latency 
    def addJitter(self, bw, baseDelayDown, varDelayDown, baseDelayUp, varDelayUp, interval=0.1):
        counter     = 0
        prevDelayDown = -1
        prevDelayUp   = -1

        print("baseDelayDown, varDelayDown, baseDelayUp, varDelayUp")
        print(baseDelayDown, varDelayDown, baseDelayUp, varDelayUp)

        while True:
            # build command
            dummyCmd1 = 'sudo ipfw pipe {} config '.format(self.pipe1)
            dummyCmd2 = 'sudo ipfw pipe {} config '.format(self.pipe2)
        
            if bw:
                dummyCmd1 += 'bw {}Mbit/s '.format(bw)
                dummyCmd2 += 'bw {}Mbit/s '.format(bw)

            counter += 1
            if baseDelayDown == 0:
                delayDown = 0
            else:
                delayDown = random.randrange(baseDelayDown-varDelayDown, baseDelayDown+varDelayDown)
            if baseDelayUp == 0:
                delayUp = 0
            else:
                delayUp   = random.randrange(baseDelayUp-varDelayUp, baseDelayUp+varDelayUp)

            if (delayDown < prevDelayDown) or (delayUp < prevDelayUp):
                steps = 2
                gapDown = prevDelayDown - delayDown
                gapUp   = prevDelayUp   - delayUp
            
                for i in range(1, steps+1):
                    tmpDelayDown = prevDelayDown - i*gapDown/steps
                    tmpDelayUp   = prevDelayUp - i*gapUp/steps

                    # Add tmpDelayDown , tmpDelayUp
                    # print("Adding Delay T: ", tmpDelayDown," ",tmpDelayUp)
                    if tmpDelayUp+tmpDelayDown:
                        dummyCmd1 += 'delay  {}ms '.format(tmpDelayUp)
                        dummyCmd2 += 'delay  {}ms '.format(tmpDelayDown)
                    
                    os.system("{} && {}".format(dummyCmd1, dummyCmd2))
                    time.sleep(interval/steps)
            else:
                # Add delay delayDown, delayUp
                # print("Adding Delay : ", delayDown," ", delayUp)
                if delayUp+ delayDown:
                    dummyCmd1 += 'delay  {}ms '.format(delayUp)
                    dummyCmd2 += 'delay  {}ms '.format(delayDown)

                os.system("{} && {}".format(dummyCmd1, dummyCmd2))
                time.sleep(interval)

            prevDelayDown = delayDown
            prevDelayUp   = delayUp         


class TC(object):
    def __init__(self, interface, ifb='ifb0'):
        self.interface = interface
        self.ifb = ifb

    def show(self):
        print('TC on {}: '.format("Local"))
        os.system('sudo tc qdisc show')

    def addIngressInterface(self):
        print('Adding IFB Ingress Interface ...')
        os.system('sudo modprobe ifb numifbs=1')
        os.system('sudo ip link set dev {} up'.format(self.ifb))
        os.system('sudo tc qdisc add dev {} handle ffff: ingress'.format(self.interface))
        os.system('sudo tc filter add dev {} parent ffff: protocol ip u32 match u32 0 0 action mirred egress redirect dev {}'.format(self.interface, self.ifb))

    def remove(self):
        print('Removing current tc stuff on {}...'.format("Local"))
        os.system('sudo tc qdisc del dev {} handle ffff: ingress'.format( self.interface ))
        os.system('sudo tc qdisc del dev {} root'.format( self.interface ))
        os.system('sudo tc qdisc del dev {} root'.format( self.ifb ))
        os.system('sudo ip link set dev {} down'.format( self.ifb ))

    def doDelay(self, delayArgsDown, delayArgsUp):
        self.remove()
        self.addIngressInterface()
        
        os.system('sudo tc qdisc add dev {} root netem delay {}ms'.format(self.interface, delayArgsUp))
        os.system('sudo tc qdisc add dev {} root netem delay {}ms'.format(self.ifb      , delayArgsDown))

    def changeDelay(self, delayDown, delayUp, parent='', handle=''):
        if parent:
            parent = 'parent {}'.format(parent)
        if handle:
            handle = 'handle {}'.format(handle)
        if (not parent) and (not handle):
            parent = 'root'
        
        os.system('sudo tc qdisc change dev {} {} {} netem delay {}ms'.format(self.interface, parent, handle, delayUp ))
        os.system('sudo tc qdisc change dev {} {} {} netem delay {}ms'.format(self.ifb      , parent, handle, delayDown ))

    def addJitter(self, baseDelayDown, varDelayDown, baseDelayUp, varDelayUp, interval=0.1):
        counter       =  0
        prevDelayDown = -1
        prevDelayUp   = -1

        while True:
            counter += 1
            if baseDelayDown == 0:
                delayDown = 0
            else:
                delayDown = random.randrange(baseDelayDown-varDelayDown, baseDelayDown+varDelayDown)
            if baseDelayUp == 0:
                delayUp = 0
            else:
                delayUp   = random.randrange(baseDelayUp-varDelayUp, baseDelayUp+varDelayUp)
                    
            if (delayDown < prevDelayDown) or (delayUp < prevDelayUp):
                steps = 2
                gapDown = prevDelayDown - delayDown
                gapUp   = prevDelayUp   - delayUp
                
                for i in range(1, steps+1):
                    tmpDelayDown = prevDelayDown - i*gapDown/steps
                    tmpDelayUp   = prevDelayUp - i*gapUp/steps
                    
                    self.changeDelay( tmpDelayDown, tmpDelayUp )
                    time.sleep(interval/steps)
            else:
                self.changeDelay( delayDown, delayUp) 
                time.sleep(interval)
            
            prevDelayDown = delayDown
            prevDelayUp   = delayUp

def main():
    
    # Call main function to do jitter direclty on link bridge
    project = "FEC-HTTP"
    experiment = "Q043"
    bw = 100
    link = DummyNet(project, experiment, "link_bridge")
    # build jitter process
    pJitter = multiprocessing.Process(target=link.addJitter, args=(bw,50, 5, 50, 5))

    print("Bandwidth : ", bw )
    # start jitter
    print("Starting Jitter")
    pJitter.start()

    # Wait for 100 sec
    # time.sleep(30)
    
    signal = input("enter stop:")

    if signal == "stop":
        # Stop Jitter
        print("Ending Jitter")
        pJitter.terminate()
    
    # pass    

if __name__ == '__main__':
    main()