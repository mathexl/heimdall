#i was curious if i could build a system to provide another metric that was the overall averages o the RGB values per Pixels
#unlike normal image classifiers, spectograms have a fixed width and height in terms o measurements
#this ran terribly tho - giving a high level of correlation to almost every image ~80%.
#i realized there were two issues - one is that the RGB variance is very high but with a very limited range (just high likelihoo of variance)
#i think i could still accomplish this if the audio is better cropped at the hard start and hard finish and intend to
#do that over the break. That way it is a lot more normalized - else the data set rn has a bunch of audio at the very start
#or the very finish. I could to this prior to the spectrumGenerator by feeding it into pyaudio, finding the RMS and cutting it off
#prior to the curve jump. However, didn't plan ahead enough to run that preprocessing sequence and then recompile the image library
#since both take a lot of CPU's + days. I will email you when I do the crop of audio + rerun this direct RGB averager since I am
#REALLY CONVINCED it could be a decent indication %70ish accuracy without barely any compute power to train.

from PIL import Image, ImageFilter
from numpy import exp, array, random, dot, vdot, tensordot
import matplotlib.pyplot as plt
from scipy.io import wavfile
from os import listdir
import random as rand
from os.path import isfile, join
import os

numeric = 0

if __name__ == '__main__': # Main function
    dirs = ["bed", "one"]
    input_behemoth = []
    neg_input_behemoth = []
    output_classification = []
    for mypath in dirs:
        classification = mypath
        mypath = "../audio/" + mypath
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        g = 0
        for fil in onlyfiles:
            if(".png" in fil): #is a png
                g = g + 1
                if(g == 4):
                    break
                print("File: " + str(mypath + "/" + fil))
                img = Image.open(mypath + "/" + fil)
                img = img.resize((256, 256), Image.ANTIALIAS)
                rbg_matrix = []
                for i in range(1, 255):
                    rbg_matrix.append([])
                    for j in range(1, 255):
                        mat = img.getpixel((i - 1, j - 1))[0:3] + img.getpixel((i, j - 1))[0:3] + img.getpixel((i + 1, j - 1))[0:3]
                        mat = mat + img.getpixel((i - 1, j))[0:3] + img.getpixel((i, j))[0:3] + img.getpixel((i + 1, j))[0:3]
                        mat = mat + img.getpixel((i - 1, j + 1))[0:3] + img.getpixel((i, j + 1))[0:3] + img.getpixel((i + 1, j + 1))[0:3]
                        mat = [x / 9 for x in mat]
                        rbg_matrix[i - 1].append(mat)
                if(classification == "bed"):
                    input_behemoth.append(rbg_matrix)
                if(classification == "one"):
                    neg_input_behemoth.append(rbg_matrix)
                numeric = numeric + 1
    dummyFilter = [ [ [ 0 for i in range(3) ] for j in range(254) ] for k in range(254)]
    rand.shuffle(input_behemoth)
    for g in range(len(input_behemoth)):
        for row in range(254):
            for col in range(254):
                for pixel in range(3):
                    dummyFilter[row][col][pixel] = float(dummyFilter[row][col][pixel] + input_behemoth[g][row][col][pixel])
    for row in range(254):
        for col in range(254):
            for pixel in range(3):
                dummyFilter[row][col][pixel] = float(dummyFilter[row][col][pixel] / float(len(input_behemoth)))
    for g in range(len(input_behemoth)):
        tot = 0
        negatedPixels = 0
        for row in range(254):
            for col in range(254):
                if(input_behemoth[g][row][col][0] == 255 and input_behemoth[g][row][col][0] == 255 and input_behemoth[g][row][col][0] == 255):
                    negatedPixels = negatedPixels + 3
                else:
                    for pixel in range(3):
                        if(pixel == 0):
                            tot = tot + 3 - 3*float(float(abs(dummyFilter[row][col][pixel] - input_behemoth[g][row][col][pixel])) / float(255))
        print("Negated Pixels: " + str(negatedPixels) + "Average Probability of Match is: " + str(float(tot / (254 * 254 * 3 - negatedPixels))))
    print("OPPOSITE SET: ")
    for g in range(len(neg_input_behemoth)):
        tot = 0
        negatedPixels = 0
        for row in range(254):
            for col in range(254):
                if(neg_input_behemoth[g][row][col][0] == 255 and neg_input_behemoth[g][row][col][0] == 255 and neg_input_behemoth[g][row][col][0] == 255):
                    negatedPixels = negatedPixels + 3
                else:
                    for pixel in range(3):
                        if(pixel == 0):
                            tot = tot + 3 - 3*float(float(abs(dummyFilter[row][col][pixel] - neg_input_behemoth[g][row][col][pixel])) / float(255))
        print("Negated Pixels: " + str(negatedPixels) + "Average Probability of Match is: " + str(float(tot / (254 * 254 * 3 - negatedPixels))))
