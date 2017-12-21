import sys
import time
from heimdall import heimdallInit

if __name__ == '__main__':
    print("Starting up Heimdall")
    ##init message / sequence just to give user some time once initializing.
    for i in range (20):
    	sys.stdout.write('.')
    	sys.stdout.flush()
    	time.sleep(0.1)

    dynamic = False
    history_samples = 10 #number of history samples .
    ##############################################################################
    # history is the number of samples that exist on average in the outlier zone
    # that triggers a recording a number of samples later. 10 is sensible for a
    # single word. If the wake word was gauranteed to be a full phrase, this number
    # could be even higher to ensure higher accuracy. Because the training is for just
    # words, it is set to 10 here, could be set with -history flag
    ##############################################################################
    conservative = False
    calibrate = False
    analyze = True

    v = 0
    for h in sys.argv:
        if(v ==- 1):
            history_samples = int(h)
            v = 0
        if(h == "--dynamic"):
            dynamic = True
        if(h == "--calibrate"):
            calibrate = True
        if(h == "--conservative"):
            conservative = True
        if(h == "-history"):
            v = 1
        if(h == "--no-analyze"):
            analyze = False



    heimdallInit(calibrate, dynamic, history_samples, conservative,  analyze)
