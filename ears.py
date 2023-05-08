#!/usr/bin/env python

import struct
import pyaudio
import math
import zmq
from environment import SHORT_NORMALIZE, NETWORKS
import json
import uuid
from pyre import Pyre
from pyre import zhelper
from afferent_neuron import AfferentNeuron


class Ears:

    def __init__(self):
        # Set up PyAudio and sensory variables
        self.id = "Ears001"
        self.p = pyaudio.PyAudio()
        self.chunk_size = 1024
        self.sample_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.listen_length = 5
        self.threshold = 20
        # Set up autonomous brain connectors
        self.context = zmq.Context()
        self.autonomous_pipe = zhelper.zthread_fork(self.context, self.ears_message)
        self.stream = self.p.open(
            format=self.sample_format, channels=self.channels, rate=self.rate, input=True,
            frames_per_buffer=self.chunk_size
        )

    def handle_introspection(self, n: Pyre, network: NETWORKS, message) -> str:
        try:
            if message.decode('utf-8') == "$$STOP":  # This will throw an error if the data is not encoded
                return "$$STOP"
        except UnicodeDecodeError:
            n.shouts(network.value, message.hex())
            return ""

    def ears_message(self, ctx, pipe):
        AfferentNeuron.process(self.id, "ears", pipe, NETWORKS.AUTONOMOUS, self.handle_introspection)

    @staticmethod
    def rms(frame):
        count = len(frame) / 2  # sound width
        f_format = "%dh" % count
        shorts = struct.unpack(f_format, frame)

        sum_squares = 0.0
        for sample in shorts:
            n = sample * SHORT_NORMALIZE
            sum_squares += n * n
        rms = math.pow(sum_squares / count, 0.5)

        return rms * 1000

    def listen(self):
        print('Listening...')
        while True:
            try:
                sound = self.stream.read(self.chunk_size)
                rms_val = self.rms(sound)
                if rms_val > self.threshold:
                    # Take previous sound and next 5 seconds and transmit to autonomous network.
                    frames = [sound]
                    for i in range(0, int(self.rate / self.chunk_size * self.listen_length)):
                        sound = self.stream.read(self.chunk_size)
                        frames.append(sound)

                    print("Sending to autonomous network for processing!")
                    self.autonomous_pipe.send(b''.join(frames))
                    # TODO register to body observer ZMQ allowing body to take actions like disabling ears,
                    # instead of input
                    self.stream.stop_stream()
                    input('PAUSED. Press Enter to Continue.')
                    self.stream.start_stream()
            except (KeyboardInterrupt, SystemExit):
                break
        self.autonomous_pipe.send('$$STOP'.encode('utf_8'))


if __name__ == '__main__':
    ears = Ears()
    ears.listen()
