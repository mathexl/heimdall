//i wanted to first use node but realized it has two layers of abstraction before it hits the hardware
//decided that was a bad choice and scrapped it. 
var fs = require('fs');
var toWav = require('audiobuffer-to-wav')
const { Writable } = require('stream');
var writeStream = fs.createWriteStream('./output.wav');

const outStream = new Writable({
  write(chunk, encoding, callback) {
    console.log(chunk);
    writeStream.write(chunk);
    callback();
  }
});
let Mic = require('node-microphone');
let mic = new Mic();
let micStream = mic.startRecording();
micStream.pipe( outStream );

mic.on('info', (info) => {
    console.log('Info: ',info);
});
mic.on('error', (error) => {
    console.log('error:', error);
});
mic.on('stop', (stop) => {
    console.log('stop:', stop);
});

setTimeout(() => {
  console.log('stopped recording');
  var toWav = require('audiobuffer-to-wav')
  var wav = toWav(writeStream)
  mic.stopRecording();

}, 8000);
