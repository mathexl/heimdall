from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pyaudio
import wave
import audioop
import math
import random
import sys
import time
import matplotlib
matplotlib.use('Agg') #required for it to work without a GUI environment
import matplotlib.pyplot as plt
import colormaps as cmaps
from scipy.io import wavfile
from os import listdir
from os.path import isfile, join
import os
from PIL import Image
import matplotlib.colors





import argparse
import sys

import tensorflow as tf

# pylint: disable=unused-import
from tensorflow.contrib.framework.python.ops import audio_ops as contrib_audio
# pylint: enable=unused-import

plt.register_cmap(name='viridis', cmap=cmaps.viridis)

############ FROM TENSORFLOW FUNCTIONS #######################

def get_wav_info(wav_file):
    rate, data = wavfile.read(wav_file)
    return rate, data

def load_graph(filename):
  """Unpersists graph from file as default graph."""
  with tf.gfile.FastGFile(filename, 'rb') as f:
    graph_def = tf.GraphDef()
    graph_def.ParseFromString(f.read())
    tf.import_graph_def(graph_def, name='')


def load_labels(filename):
  """Read in labels, one label per line."""
  return [line.rstrip() for line in tf.gfile.GFile(filename)]


def run_graph(wav_data, labels, input_layer_name, output_layer_name,
              num_top_predictions):
  """Runs the audio data through the graph and prints predictions."""
  with tf.Session() as sess:
    # Feed the audio data as input to the graph.
    #   predictions  will contain a two-dimensional array, where one
    #   dimension represents the input image count, and the other has
    #   predictions per class
    softmax_tensor = sess.graph.get_tensor_by_name(output_layer_name)
    predictions, = sess.run(softmax_tensor, {input_layer_name: wav_data})

    # Sort to show labels in order of confidence
    top_k = predictions.argsort()[-num_top_predictions:][::-1]
    for node_id in top_k:
      human_string = labels[node_id]
      score = predictions[node_id]
      print('%s (score = %.5f)' % (human_string, score))

    return 0


def label_wav(wav, labels, graph, input_name, output_name, how_many_labels):
  """Loads the model and labels, and runs the inference to print predictions."""
  if not wav or not tf.gfile.Exists(wav):
    tf.logging.fatal('Audio file does not exist %s', wav)

  if not labels or not tf.gfile.Exists(labels):
    tf.logging.fatal('Labels file does not exist %s', labels)

  if not graph or not tf.gfile.Exists(graph):
    tf.logging.fatal('Graph file does not exist %s', graph)

  labels_list = load_labels(labels)

  # load graph, which is stored in the default session
  load_graph(graph)

  with open(wav, 'rb') as wav_file:
    wav_data = wav_file.read()

  run_graph(wav_data, labels_list, input_name, output_name, how_many_labels)


def im_load_image(filename):
  """Read in the image_data to be classified."""
  return tf.gfile.FastGFile(filename, 'rb').read()


def im_load_labels(filename):
  """Read in labels, one label per line."""
  return [line.rstrip() for line in tf.gfile.GFile(filename)]


def im_load_graph(filename):
  """Unpersists graph from file as default graph."""
  with tf.gfile.FastGFile(filename, 'rb') as f:
    graph_def = tf.GraphDef()
    graph_def.ParseFromString(f.read())
    tf.import_graph_def(graph_def, name='')


def im_run_graph(image_data, labels, input_layer_name, output_layer_name,
              num_top_predictions):
  with tf.Session() as sess:
    # Feed the image_data as input to the graph.
    #   predictions will contain a two-dimensional array, where one
    #   dimension represents the input image count, and the other has
    #   predictions per class
    softmax_tensor = sess.graph.get_tensor_by_name(output_layer_name)
    predictions, = sess.run(softmax_tensor, {input_layer_name: image_data})

    # Sort to show labels in order of confidence
    top_k = predictions.argsort()[-num_top_predictions:][::-1]
    for node_id in top_k:
      human_string = labels[node_id]
      score = predictions[node_id]
      print('%s (score = %.5f)' % (human_string, score))

    return 0

############ END FROM TENSORFLOW FUNCTIONS #######################



def heimdallInit(calibrate = False, dynamic = True, history_samples = 10, conservative = False, analyze = True):
	###############################################
	#                                             #
	#  Takes audio stream and calls forward-pass  #
	#  when audio is detected                     #
	#                                             #
	###############################################

	#Learned how to utilize PyAUDIO via jfraj's blog online, linked below
	#https://jfraj.github.io/2015/06/17/recording_audio.html
	#great tutorial

	CHUNK = 1024 #chunk of data per frame
	FORMAT = pyaudio.paInt16 #utilizing pyaudio library to take hardware output to wav file
	CHANNELS = 1 #mono
	RATE = 16000 #rate of data write in stream
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

	##simple get average function##
	def getavg(lst):
		return sum(lst)/len(lst)

	##number of total frames in rolling memory - this never grows, keeps low footprint##
	##there is no long term recording, just a running average of past data - keeps footprint
	##small for a continuous runtime.
	frames = [0] * 3000


	sys.stdout.write('\n')
	sys.stdout.flush()
	print("Say the words once printed to calibrate mic against background environment")
	p = pyaudio.PyAudio() #init main pyAudio file

	if(calibrate):
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
		diffCoefficient = 1
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
		frames = ['\xff'] * int(RATE / CHUNK * RECORD_SECONDS) * 2 * 10000
		# init array of streams that is created just for a window of the record_seconds * 2

		i = 100 #trigger
		soonTrigger = 0 #when triggered, this will write a file of the last frames of the last 50 frames 10 frames later


		sample_count = 0
		j = 0
		while(1):
			i = i + 1 #increment index.
			j = j + 1 #independent counter (helpful)
			i = i % ((int(RATE / CHUNK * RECORD_SECONDS)) * 2 * 10000 - 1)#modulate to current index
			sample_count = sample_count + 1; #increment the sample count
			data = stream.read(CHUNK) #grab data from main stream
			rms = audioop.rms(data, 2) #volume utilizing audioop
			#print(rms)
			modval = rms**(float(1)/float(4 * diffCoefficient))
			lst = avg_total * (sample_count - 1); #current total of quartic root of volume over time (skewed)
			frames[i] = data #save data to a current frame
			short_term_memory[i%history_samples] = modval
			rechist = sum(short_term_memory)/len(short_term_memory)
			if(conservative == True):
				thresh = avg_total + (variance_measure)
			else:
				thresh = avg_total + (2 * variance_measure)
			if(i%6 == 0):
				print("LTM: " + str(avg_total) + "::LV: " + str(modval) + "::STM: " + str(rechist) + "::THRESH: " + str(thresh) + " ::VAR: " + str(variance_measure))
			if(sample_count > 50 and (rechist > thresh)):
				#pull samples
				if(soonTrigger == 0):
					soonTrigger = j
				if(i%6 == 0): #only every sixth integrate into the average
					avg_total = float((modval + lst) / sample_count) #calculate average of the quartic root of volume
					vari = abs(avg_total - modval)
					variance_measure = float((variance_measure * (sample_count - 1) + vari) / sample_count)
					if(dynamic == True):
						variance_measure = float(variance_measure * .999) + float((vari) * .001)  #skew to more recent data via a static pull
						avg_total = float(avg_total * .999) + float((modval) * .001)  #skew to more recent data via a static pull

				else:
					sample_count = sample_count - 1
			else:
				avg_total = float((modval + lst) / sample_count) #calculate average of the quartic root of volume
				vari = abs(avg_total - modval)
				variance_measure = float((variance_measure * (sample_count - 1) + vari) / sample_count)
				if(dynamic == True):
					variance_measure = float(variance_measure * .999) + float((vari) * .001)  #skew to more recent data via a static pull
					avg_total = float(avg_total * .98) + float((modval) * .02)  #skew to more recent data via a static pull

			if(not(soonTrigger == 0) and (j - soonTrigger) > 10):
				stream.stop_stream() #dont want to incur overflow due to file I/O Latency
				#will multithread if time permits to allow conseq

				traceback = 20
				if(i - 20 < 0):
					traceback = i
				sel = frames[(i - traceback):i]
				fil = "generated_samples/" + str(sample_count) + "_" + WAVE_OUTPUT_FILENAME
				wf = wave.open(fil, 'wb')
				wf.setnchannels(CHANNELS)
				wf.setsampwidth(p.get_sample_size(FORMAT))
				wf.setframerate(RATE)
				try:
					wf.writeframes(b''.join(sel))
				except:
					wf.close()
					stream.start_stream()
					print(sel)
					print("MISS")
					print(str(i - traceback) + " :: " + str(i))
					wf.writeframes(b''.join(sel))
					continue
				wf.close()
				for i in range (10):
					print("#####################################################################")
				print("##                                                                 ##")
				print("## WROTE FILE TO " + fil + "....")
				print("##                                                                 ##")
				for i in range (10):
					print("#####################################################################")
				time.sleep(1)
				if(analyze == True):
					try:
						rate, data = get_wav_info(fil)
						# I found these next 5 lines of coding on how to create a specgram on Python online
						# Can't find the citation but it is pretty similar to ever public implementation of it.
						nfft = 512  # Length of the windowing segments
						fs = 512    # Sampling frequency
						cmap = plt.get_cmap('viridis') #colorscheme of training data
						pxx, freqs, bins, im = plt.specgram(data, nfft,fs, cmap=cmap)
						plt.axis('off')
						plt.savefig("generated_spectograms/temp.png",
						            dpi=200, # Dots per inch
						            frameon='false',
									cmap=cmap,
						            aspect='normal',
						            bbox_inches='tight',
						            pad_inches=0) # Spectrogram saved as a .png

						im = Image.open("generated_spectograms/temp.png")
						#open png file
						rgb_im = im.convert('RGB')
						#convert to jpg format
						rgb_im.save("generated_spectograms/temp.jpg")
						image_data = im_load_image("generated_spectograms/temp.jpg")

						# load labels
						labels = im_load_labels("imagelabel.txt")

						# load graph, which is stored in the default session
						im_load_graph("tensor_graph_larger_2.pb")
						print("#######LESS RELIABLE SPECTOGRAM METRIC:")
						im_run_graph(image_data, labels, 'DecodeJpeg/contents:0', 'final_result:0', 3)
						print("")
						print("")
					except:
						print("Image Recognition Failed!")
					#from my spectrumGenerator.py file
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

					try:
						print("#######MORE RELIABLE AUDIO METRIC:")

						label_wav(fil, "model/conv_labels.txt", "model/tensormodel.pb", 'wav_data:0',
					              'labels_softmax:0', 3)
					except:
						print("Audio Recognition Failed!")


					time.sleep(5)
				else:
					time.sleep(0.5)
				soonTrigger = 0
				short_term_memory = [0] * history_samples #reset
				stream.start_stream()




		print("* done recording")

		stream.stop_stream()
		stream.close()
		p.terminate()
