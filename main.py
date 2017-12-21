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

    dynamic = True
    history_samples = 10 #number of history samples .
    ##############################################################################
    # history is the number of samples that exist on average in the outlier zone
    # that triggers a recording a number of samples later. 10 is sensible for a
    # single word. If the wake word was gauranteed to be a full phrase, this number
    # could be even higher to ensure higher accuracy. Because the training is for just
    # words, it is set to 10 here, could be set with -expected flag
    ##############################################################################
    conservative = False
    calibrate = True



    heimdallInit(calibrate, dynamic, history_samples, conservative)
