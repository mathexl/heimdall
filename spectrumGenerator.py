import matplotlib
matplotlib.use('Agg') #required for it to work without a GUI environment
import matplotlib.pyplot as plt
from scipy.io import wavfile
from os import listdir
from os.path import isfile, join
import os
from PIL import Image
from random import shuffle, randrange
import time

################################################################################################################
################################################################################################################
## Heimdall utilizes a secondary NN to provide more context to a recording                                    ##
## by transcribing the audio recording into a spectogram and running it                                       ##
## through MobileNet which has a ~50% level of accuracy. This NN is not utilized                              ##
## to make a prediction - rather - helps sort between two close words that                                    ##
## may be similar by the primary net.                                                                         ##
##                                                                                                            ##
## The same model was trained with Inception architecture for the same accuracy.                              ##
## Exploding the validation set to the entire set had no effect on the training                               ##
## accuracy.                                                                                                  ##
##                                                                                                            ##
## This is a much more effective approach because wake words are short and                                    ##
## can often look different based on vocal form.                                                              ##
##                                                                                                            ##
## In order to train the net, simply run this python file in the same folder that                             ##
## holds all the other directories of images. It is advised to disable the print                              ##
## message if you want it to run in the background since writing to stdout is expensive                       ##
##                                                                                                            ##
## A pre-converted set from Google's open source wake words library into Spectograms                          ##
## was open sourced by this project. I have uploaded them through the following                               ##
## links, which includes 22,500 jpgs sorted by classification. Converting the set                             ##
## took a long long time (much longer than expected, file I/O seems to lock out pretty fast)                  ##
## so it is best to just download the pre-compiled bundle to save time.                                       ##
##                                                                                                            ##
## .zip     | https://storage.googleapis.com/speech-recog/hotwordSpectogramDataset.zip (4.54 GB)              ##
## .tar.gz  | https://storage.googleapis.com/speech-recog/hotwordSpectogramDataset.tar.gz (1.59 GB)           ##
## .tar.bz2 | https://storage.googleapis.com/speech-recog/hotwordSpectogramDataset.tar.bz2 (1.44 GB)          ##
################################################################################################################
################################################################################################################

numeric = randrange(2390, 4902390) #this is a random value so that the file names will be unique


def graph_spectrogram(wav_file, output):
    #should always succeed unless one of your files isnt a wav file.
    try:
        rate, data = get_wav_info(wav_file)
    except:
        return 0


    # I found these next 5 lines of coding on how to create a specgram on Python online
    # Can't find the citation but it is pretty similar to ever public implementation of it.
    nfft = 512  # Length of the windowing segments
    fs = 512    # Sampling frequency
    cmap = plt.get_cmap('viridis')
    pxx, freqs, bins, im = plt.specgram(data, nfft,fs, cmap = cmap)
    plt.axis('off')
    plt.savefig(output,
                dpi=200, # Dots per inch
                frameon='false',
                aspect='normal',
                bbox_inches='tight',
                pad_inches=0) # Spectrogram saved as a .png


    try:
        os.remove(wav_file) #remove the wav file that is converted so it is not double converted
                            #technically concurrent sessions may double convert something (hence the try catch)
                            #but this shouldn't ruin training due to the size of the data set.
    except:
        return 0


def get_wav_info(wav_file):
    rate, data = wavfile.read(wav_file)
    return rate, data



def routine(): # Main function
    dirs = ["cat", "dog", "down", "eight", "five", "four", "go", "happy", "house", "left", "marvin", "nine", "no", "off", "on", "one", "right", "seven", "sheila", "six", "stop", "three", "tree", "two", "up", "wow", "yes", "zero"]

    #current directory names, could be gathered via os but decided to hardcode it so other folders could be in there uneffected
    while(1):
        shuffle(dirs) #i found it efficient to create 9 screen instances and run the file 9 times.
        # de facto multithreading without handling it in the python file.
        # valid since this is a one time thing.

        for mypath in dirs:
                onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f)) and ".wav" in f]
                #########################
                # get all files that are
                # wav files in sibling dirs
                #########################

                g = 0
                shuffle(onlyfiles)
                #useful for multiple programs running concurrently so not everyone
                #is on the same dir at once.
                #further, this switches directories every 10 entries to smooth out
                #how fast files are populated.
                #i queued 3 independent 16 core VM's to do this over the course of 24
                #hours - it still only did a little less than half of google's dataset
                #in that time. That seemed sufficient so I cut it there but it is a
                #very expensive process to mass compute for training .


                for file in onlyfiles:
                        wav_file = mypath + '/' + file # Filename of the wav file
                        #grab wav file
                        print("Saving to " + mypath + '/a' + str(numeric) + '.png')
                        graph_spectrogram(wav_file, mypath + '/a' + str(numeric) + '.png')
                        #create spectogram
                        try:
                            im = Image.open(mypath + '/a' + str(numeric) + '.png')
                            #open png file
                            rgb_im = im.convert('RGB')
                            #convert to jpg format
                            rgb_im.save(mypath + '/a' + str(numeric) + '.jpg')
                            #save jpeg
                        except:
                            g = 10 #if the above failed, it likely is due to some weird issue
                                    # so assuming an overnight run, should jsut switch dirs.
                        g = g + 1
                        if(g == 10):
                                break
                        numeric = numeric + 1
