#!/usr/bin/env python

import struct
import pyaudio
import math
import zmq
import environment


class Ears:

    def __init__(self):
        # Set up PyAudio and sensory variables
        self.p = pyaudio.PyAudio()
        self.chunk_size = 1024
        self.sample_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.listen_length = 5
        self.threshold = 20
        # Set up brain connectors
        # Start your:
        # result manager (Consciousness) and workers (Brain) before you start your producers (Eyes, Ears, etc.)
        self.context = zmq.Context()
        self.brain_socket = self.context.socket(zmq.PUSH)
        self.brain_socket.bind("tcp://127.0.0.1:8000")  # was 5557
        self.stream = self.p.open(
            format=self.sample_format, channels=self.channels, rate=self.rate, input=True,
            frames_per_buffer=self.chunk_size
        )

    @staticmethod
    def rms(frame):
        count = len(frame) / 2  # sound width
        f_format = "%dh" % count
        shorts = struct.unpack(f_format, frame)

        sum_squares = 0.0
        for sample in shorts:
            n = sample * environment.SHORT_NORMALIZE
            sum_squares += n * n
        rms = math.pow(sum_squares / count, 0.5)

        return rms * 1000

    def listen(self):
        print('Listening...')
        while True:
            sound = self.stream.read(self.chunk_size)
            rms_val = self.rms(sound)
            if rms_val > self.threshold:
                # Take previous sound and next 5 seconds and transmit to brain.
                frames = [sound]
                for i in range(0, int(self.rate / self.chunk_size * self.listen_length)):
                    sound = self.stream.read(self.chunk_size)
                    frames.append(sound)

                print("Asking the brain to process!")
                self.brain_socket.send_json({'ears': b''.join(frames).hex()})
                # TODO register to body observer ZMQ allowing body to take actions like disabling ears, instead of input
                self.stream.stop_stream()
                input('PAUSED. Press Enter to Continue.')
                self.stream.start_stream()


if __name__ == '__main__':
    ears = Ears()
    ears.listen()
