#!/usr/bin/env python

import whisper
import pyaudio
import numpy

# from pprint import pprint
# pprint(whisper.available_models())

# Loading whisper language models.
# model = whisper.load_model("large-v2")
print("Loading Jarvis language models.")
model = whisper.load_model("medium.en")

# Set up PyAudio
p = pyaudio.PyAudio()
chunk_size = 1024
sample_format = pyaudio.paInt16
channels = 1
rate = 16000

# Open microphone stream
print("Recording...")
stream = p.open(format=sample_format, channels=channels, rate=rate, frames_per_buffer=chunk_size, input=True)

# Capture audio
frames = []
for i in range(0, int(rate / chunk_size * 5)):
    data = stream.read(chunk_size)
    frames.append(data)

# Stop and close the microphone stream
stream.stop_stream()
stream.close()
p.terminate()

# Convert audio frames to bytes
audio_bytes = b''.join(frames)

# Convert buffer to float32 using NumPy
audio_as_np_int16 = numpy.frombuffer(audio_bytes, dtype=numpy.int16)
audio_as_np_float32 = audio_as_np_int16.astype(numpy.float32)

# Normalise float32 array so that values are between -1.0 and +1.0
max_int16 = 32768  # e.g. 2**15
audio_normalised = audio_as_np_float32 / max_int16

print("Transcribing...")
result = model.transcribe(audio_normalised, fp16=False, language='English')

# Printing the transcribed text
print(result['text'])
