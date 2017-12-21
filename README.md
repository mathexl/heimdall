# Heimdall

![](https://dl.dropbox.com/s/yj50zjqjdgoz32v/Screen%20Shot%202017-12-21%20at%2012.35.47%20PM.png?dl=0)

Low CPU Usage that buffers in input to the Neural Nets for analysis only when a disturbance is detected via the Audio's RMS. The original purpose of this project was to implement a low memory runtime for a wake word spotter. However, since I used python, this is a null and void implementation due to the space of its dependencies. 

Heimdall's primary advantage, hence, is its low file I/O and CPU usage by being picky about when to pick up keywords. 

Demo: http://pregasen.com/sr.html

## Pre-Reqs

You likely will need to do a pip install of Pillow, matplotlib, wavfile, tensorflow, and audioop.

Pip version 9.0.1
Python version py2.7

### Running

Simply run by calling

```
python main.py
```

There are a few configurations discussed further below. 

## Generating Your Own Spectogram Library

Heimdall utilizes a secondary NN to provide more context to a recording by transcribing the audio recording into a spectogram and running it through MobileNet which has a ~50% level of accuracy. This NN is not utilized to make a prediction - rather - helps sort between two close words that may be similar by the primary net. The same model was trained with Inception architecture for the same accuracy. Exploding the validation set to the entire set had no effect on the training accuracy.                                                                                                  

A pre-converted set from Google's open source wake words library into Spectograms was open sourced by this project. I have uploaded them through the following links, which includes 22,500 jpgs sorted by classification. Converting the set took a long long time (much longer than expected, file I/O seems to lock out pretty fast) so it is best to just download the pre-compiled bundle to save time.

The spectograms are rendered in the 'viridis' color scheme. You can change the scheme in the file easily. 
                                                                                                           
.zip     | https://storage.googleapis.com/speech-recog/hotwordSpectogramDataset.zip (4.54 GB)              
.tar.gz  | https://storage.googleapis.com/speech-recog/hotwordSpectogramDataset.tar.gz (1.59 GB)           
.tar.bz2 | https://storage.googleapis.com/speech-recog/hotwordSpectogramDataset.tar.bz2 (1.44 GB)

### Options when running

e.g.
```
python main.py --conservative --calibrate --dynamic
```
`--conservative`
Is far more likely (~4x) to pull a segment of audio into the parser 

`--calibrate`
Will calibrate at the start to figure out how "quiet" or noisy the space is that the device is in 

`--dynamic`
Will weight newer samples more when determining when to pass it to the audio in the back

`-history <number of samples>`
Default set to 10. This is how many samples of a disturbance triggers the audio (not how long it is). Around 15 samples = 1 second. 

`--no-analyze`
Don't analyze the content of the speech - good for testing how well the sound snipper works. 


