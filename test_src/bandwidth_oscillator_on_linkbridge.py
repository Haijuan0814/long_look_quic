
import sys, os, random, time


def bandwitdh_oscillator(pipe1, pipe2, delay, minBW, maxBW, sleep):
    """
    Changes bandwidth of link between min and max BW
    """
    while True:
        # build command
        dummyCmd1 = 'sudo ipfw pipe {} config '.format(pipe1)
        dummyCmd2 = 'sudo ipfw pipe {} config '.format(pipe2)

        if delay:
            dummyCmd1 += 'delay {}ms '.format(delay)
            dummyCmd2 += 'delay {}ms '.format(delay)


        bw = random.randrange(minBW, maxBW)

        if bw:
            dummyCmd1 += 'bw {}Mbit/s '.format(bw)
            dummyCmd2 += 'bw {}Mbit/s '.format(bw) 

        print("{} && {}".format(dummyCmd1, dummyCmd2))  
        os.system("{} && {}".format(dummyCmd1, dummyCmd2))  
        time.sleep(sleep)

if __name__ == '__main__':

    if len(sys.argv) != 7:
        print("Usage: ", sys.argv[0], " <pipe1> <pipe2> <delay> <minBW> <maxBW> <sleep>")
        exit(1)
    else:
        pipe1, pipe2 = sys.argv[1], sys.argv[2]
        delay = int(sys.argv[3])
        minBW, maxBW = int(sys.argv[4]), int(sys.argv[5])
        sleep = int(sys.argv[6])

    bandwitdh_oscillator(pipe1, pipe2, delay, minBW, maxBW, sleep)
    
