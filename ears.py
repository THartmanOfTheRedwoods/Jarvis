#!/usr/bin/env python

import struct
import pyaudio
import math
import zmq
import environment
import json
import uuid
from pyre import Pyre
from pyre import zhelper


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
        # Start your:
        # result manager (Consciousness) and workers (Brain) before you start your producers (Eyes, Ears, etc.)
        self.context = zmq.Context()
        self.autonomous_pipe = zhelper.zthread_fork(self.context, self.ears_message)
        self.stream = self.p.open(
            format=self.sample_format, channels=self.channels, rate=self.rate, input=True,
            frames_per_buffer=self.chunk_size
        )

    def ears_message(self, ctx, pipe):
        n = Pyre(self.id)
        n.set_header("id", self.id)
        n.set_header("type", "ears")
        n.join("AUTONOMOUS")
        n.start()

        poller = zmq.Poller()
        poller.register(pipe, zmq.POLLIN)
        # print(n.socket())
        poller.register(n.socket(), zmq.POLLIN)
        # print(n.socket())

        while True:
            items = dict(poller.poll())
            # print(n.socket(), items)
            if pipe in items and items[pipe] == zmq.POLLIN:  # Sent from self
                message = pipe.recv()
                # print("AUTONOMOUS MESSAGE: %s" % message)
                # message to quit
                try:
                    if message.decode('utf-8') == "$$STOP":  # This will throw an error if the data is not encoded
                        break
                except UnicodeDecodeError:
                    n.shouts("AUTONOMOUS", message.hex())
            else:  # Sent from peer organ
                # TODO: decide what to do with message based on headers.
                cmds = n.recv()
                msg_type = cmds.pop(0).decode('utf-8')
                msg_uuid = uuid.UUID(bytes=cmds.pop(0))
                msg_name = cmds.pop(0).decode('utf-8')
                # print("NODE_MSG TYPE: %s" % msg_type)
                # print("NODE_MSG PEER: %s" % msg_uuid)
                # print("NODE_MSG NAME: %s" % msg_name)
                if msg_type == "SHOUT":
                    msg_group = cmds.pop(0).decode('utf-8')
                    # print("NODE_MSG GROUP: %s" % msg_group)
                elif msg_type == "ENTER":
                    pass
                    # headers = json.loads(cmds.pop(0).decode('utf-8'))
                    # for key in headers:
                    #    print("key = {0}, value = {1}".format(key, headers[key]))
                # print("NODE_MSG CONT: %s" % cmds)
        n.stop()

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
