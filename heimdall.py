import pyaudio
import wave
import audioop
import math
import random
import sys
import time


###############################################
#                                             #
#  Takes audio stream and calls forward-pass  #
#  when audio is detected                     #
#                                             #
###############################################

#Learned how to utilize PyAUDIO via jfraj's blog online, linked below
#https://jfraj.github.io/2015/06/17/recording_audio.html
#great tutorial

CHUNK = 2048 #chunk of data per frame
FORMAT = pyaudio.paInt16 #utilizing pyaudio library to take hardware output to wav file
CHANNELS = 2 #stereo
RATE = 44100 #rate of data write in stream
RECORD_SECONDS = 3 #amount of time stored in the buffer at any point.


#base file name - not final. A string is prepended to allow
WAVE_OUTPUT_FILENAME = "output.wav"
#asynchronous evaluate by multiple files at once.

avg_total = 0 #current rolling average of past samples.
###############################################################################
#
# Average Total is not a mean - rather, a weighted average depending on settings
# If dynamic is configured to true, then Average Total will slightly weight the
# more recent recordings more via a linear .999 - .001 additional weighting. I
# found this to be better at maintaining a well-informed average in environments
# where noise will grow less erratically - for instance, where music may start
#
# If dynamic is configured off, Average Total begins tabulation when the stream
# starts (not the optional but recommended pre-recording stage)
#
###############################################################################


variance_measure = 0 #variance pre-set
###############################################################################
# similar to average, when dynamic is configured to True, variance adds extra
# weights to more recent recordings. Variance provides a threshold at a linear
# level to when an outlier is detected. The threshold is STATICALLY held as
# the average + 2*variance to trigger a recording. This seems to test
# well for any intentional invocation of the device.
#
# With the option --conservative, heimdall will treat average + variance as
# sufficient to trigger a recoring. This is arguably WAY too permissive, however,
# may be suitable if the device is looking for a wake word in conversation without
# the intent of waking the device (i.e. something that discreetly performs a function)
###############################################################################

sample_count = 0 #current number of samples
######just the total amount of samples so far#######
history_samples = 10 #number of history samples .
##############################################################################
# history is the number of samples that exist on average in the outlier zone
# that triggers a recording a number of samples later. 10 is sensible for a
# single word. If the wake word was gauranteed to be a full phrase, this number
# could be even higher to ensure higher accuracy. Because the training is for just
# words, it is set to 10 here, could be set with -expected flag
##############################################################################

short_term_memory = [0] * history_samples #recent history
##############################################################################
# List to store the short term memory of a device's history. This is a fixed
# length and added to via mod. Preset to 0.
##############################################################################

diffCoefficient = 0
############initializing diffCoefficient, discussed later in file#############

dynamic = 0

##simple get average function##
def getavg(lst):
	return sum(lst)/len(lst)

##number of total frames in rolling memory - this never grows, keeps low footprint##
##there is no long term recording, just a running average of past data - keeps footprint
##small for a continuous runtime.
frames = [0] * 1000

##init message / sequence just to give user some time once initializing.
print("Starting up Heimdall")
for i in range (20):
	sys.stdout.write('.')
	sys.stdout.flush()
	time.sleep(0.1)



sys.stdout.write('\n')
sys.stdout.flush()
print("Say the words once printed to calibrate mic against background environment")
p = pyaudio.PyAudio() #init main pyAudio file

if(1 == 2):
	calibrateStream = p.open(format=FORMAT,
	  	        channels=CHANNELS,
	            rate=RATE,
	            input=True,
	            frames_per_buffer=CHUNK)

	for i in range(1000):
		sample_count = sample_count + 1; #increment the sample count
		data = calibrateStream.read(CHUNK) #grab data from main stream
		rms = audioop.rms(data, 2)
		frames[i] = rms
		if i == 195:
			print("SAY: 'YES'")

		if i == 495:
			print("SAY: 'HELLO'")

		if i == 695:
			print("SAY: 'HI'")

	sample1 = getavg(frames[205:245])
	sample2 = getavg(frames[505:545])
	sample3 = getavg(frames[705:745])

	baseline = getavg(frames[0:205])*.3 + getavg(frames[246:504] + frames[546:704] + frames[746:])*.7

	variance1 = sample1 - baseline
	variance2 = sample2 - baseline
	variance3 = sample3 - baseline

	if(variance1 <= 0 or variance2 <= 0 or variance3 <= 0):
		diffCoefficient = 1
		print("Sounds Noisy, may be unreliable")
	else:
		varsum = (math.sqrt(variance1) + math.sqrt(variance2) + math.sqrt(variance3))/3
		varsum = varsum**2
		print(varsum)
		print(baseline)
		if(baseline < 10):
			baseline = 10
		diffCoefficient = math.log(varsum, baseline)
		if(diffCoefficient < 1):
			diffCoefficient = 1


	print("diffCoefficient: " + str(diffCoefficient))
	time.sleep(2)
	calibrateStream.stop_stream()
	calibrateStream.close()
	p.terminate()
else:
	diffCoefficient = 1.15
while(1): #allows crash and reboot if anything goes wrong.

	print(str(int(RATE / CHUNK * RECORD_SECONDS)))

	p = pyaudio.PyAudio() #init main pyAudio file

	stream = p.open(format=FORMAT,
      	        channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)
	#open stream with specific settings.

	print("recording")
	frames = []
	frames = [None] * int(RATE / CHUNK * RECORD_SECONDS) * 2
	# init array of streams that is created just for a window of the record_seconds * 2

	i = 0 #trigger
	soonTrigger = 0 #when triggered, this will write a file of the last frames of the last 50 frames 10 frames later


	sample_count = 0
	while(1):
		i = i + 1 #increment index.
		i = i % (int(RATE / CHUNK * RECORD_SECONDS)) #modulate to current index
		sample_count = sample_count + 1; #increment the sample count
		data = stream.read(CHUNK) #grab data from main stream
		rms = audioop.rms(data, 2) #volume utilizing audioop
		#print(rms)
		modval = rms**(float(1)/float(4 * diffCoefficient))
		lst = avg_total * (sample_count - 1); #current total of quartic root of volume over time (skewed)
		frames[i] = data #save data to a current frame
		short_term_memory[i%history_samples] = modval
		rechist = sum(short_term_memory)/len(short_term_memory)
		thresh = avg_total + (2 * variance_measure)
		print("LTM: " + str(avg_total) + "::LV: " + str(modval) + "::STM: " + str(rechist) + "::THRESH: " + str(thresh) + " ::VAR: " + str(variance_measure))
		if(sample_count > 50 and (rechist > thresh)):
			#pull samples
			if(soonTrigger == 0):
				soonTrigger = sample_count
			if(i%6 == 0): #only every sixth integrate into the average
				avg_total = float((modval + lst) / sample_count) #calculate average of the quartic root of volume
				vari = abs(avg_total - modval)
				variance_measure = float((variance_measure * (sample_count - 1) + vari) / sample_count)
				if(dynamic == 1):
					variance_measure = float(variance_measure * .999) + float((vari) * .001)  #skew to more recent data via a static pull
					avg_total = float(avg_total * .999) + float((modval) * .001)  #skew to more recent data via a static pull

			else:
				sample_count = sample_count - 1
		else:
			avg_total = float((modval + lst) / sample_count) #calculate average of the quartic root of volume
			vari = abs(avg_total - modval)
			variance_measure = float((variance_measure * (sample_count - 1) + vari) / sample_count)
			if(dynamic == 1):
				variance_measure = float(variance_measure * .999) + float((vari) * .001)  #skew to more recent data via a static pull
				avg_total = float(avg_total * .98) + float((modval) * .02)  #skew to more recent data via a static pull

		if(not(soonTrigger == 0) and (sample_count - soonTrigger) == 10):
			stream.stop_stream() #dont want to incur overflow due to file I/O Latency
			#will multithread if time permits to allow conseq

			traceback = 50
			if(i - 50 < 0):
				traceback = i
			sel = frames[(i - traceback):i]
			fil = "generated_samples/" + str(sample_count) + "_" + WAVE_OUTPUT_FILENAME
			wf = wave.open(fil, 'wb')
			wf.setnchannels(CHANNELS)
			wf.setsampwidth(p.get_sample_size(FORMAT))
			wf.setframerate(RATE)
			wf.writeframes(b''.join(sel))
			wf.close()
			for i in range (10):
				print("#####################################################################")
			print("##                                                                 ##")
			print("## WROTE FILE TO " + fil + "....")
			print("##                                                                 ##")
			for i in range (10):
				print("#####################################################################")
			time.sleep(1)
			soonTrigger = 0
			short_term_memory = [0] * history_samples #reset
			stream.start_stream()


	print("* done recording")

	stream.stop_stream()
	stream.close()
	p.terminate()
