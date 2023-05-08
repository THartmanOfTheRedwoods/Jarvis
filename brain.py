#!/usr/bin/env python

import zmq
import whisper
import numpy
import environment
import json
import uuid
from pyre import Pyre
from pyre import zhelper
from callback_thread import CallbackThread
from typing import List
# from pprint import pprint


class Brain:

    def __init__(self):
        self.id = "Jarvis"
        # pprint(whisper.available_models())
        # Loading whisper language models.
        # model = whisper.load_model("large-v2")
        print("Loading Jarvis language models.")
        self.language = "English"
        self.fp16 = False
        self.model = whisper.load_model("medium.en")  # Models in ~/.cache/whisper
        print("Models loaded...")
        self.curr_thread = 0  # Index for the current active_thread/brain process
        self.thread_limit = 2  # Limits active brain processes
        self.active_threads: List[CallbackThread] = []  # Holds active brain processes
        # TODO: possibly store this in memory cache like REDIS and build other types of indexes
        self.sensory_organs = {}
        # Work to/from autonomous network
        self.context = zmq.Context()
        self.autonomous_pipe = zhelper.zthread_fork(self.context, self.process_autonomous)
        # Work to/from consciousness network
        self.consciousness_pipe = zhelper.zthread_fork(self.context, self.process_consciousness)

    def process_autonomous(self, ctx, pipe):
        n = Pyre(self.id)
        n.set_header("id", self.id)
        n.set_header("type", "brain")
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
            if pipe in items and items[pipe] == zmq.POLLIN:  # Autonomous message to self
                message = pipe.recv().decode('utf-8')
                # print("AUTONOMOUS MESSAGE: %s" % message)
                # message to quit
                if message == "$$STOP":  # This will throw an error if the data is not encoded
                    break
                n.shouts("AUTONOMOUS", message)
            else:  # Autonomous messages from other organs
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
                    if self.get_type_by_organ_id(msg_uuid) == 'ears':
                        # TODO active_threads and curr_thread should be synchronized as we add more organs.
                        i = self.curr_thread % self.thread_limit
                        self.curr_thread += 1
                        # There is a thread still possibly running at circular buffer index i.
                        try:
                            if self.active_threads[i] and self.active_threads[i].is_alive():
                                self.active_threads[i].join()  # Thus, let's wait for it before adding another.
                        except IndexError:
                            pass

                        self.active_threads.insert(i, CallbackThread(
                            target=self.transcribe,
                            callback=self.interpret,
                            callback_args=(msg_type, msg_uuid),
                            args=cmds
                        ))
                        self.active_threads[i].start()
                elif msg_type == "ENTER":  # This is where we register our organs.
                    headers = json.loads(cmds.pop(0).decode('utf-8'))
                    self.sensory_organs[msg_uuid] = headers['type']
                # print("NODE_MSG CONT: %s" % cmds)
        n.stop()

    def get_type_by_organ_id(self, organ_id):
        return self.sensory_organs[organ_id]

    def interpret(self, msg_type, msg_uuid, *, method_return_val):
        # TODO: make this contextual decision also use an AI model
        #  (Q: is this text about me or the conversation I'm in?)
        # Decide if this text is directed to YOU/Your ID
        if self.id.lower() in method_return_val.lower():  # If this is about me, send to consciousness
            print("Passing to consciousness...")
            message = {'from': '{}_ears'.format(self.id), 'message': method_return_val}
            self.consciousness_pipe.send(json.dumps(message).encode('utf-8'))

    def transcribe(self, audio_hex=None):
        if audio_hex:
            audio_bytes = bytes.fromhex(audio_hex.decode('utf-8'))
            # Convert buffer to float32 using NumPy
            audio_as_np_int16 = numpy.frombuffer(audio_bytes, dtype=numpy.int16)
            audio_as_np_float32 = audio_as_np_int16.astype(numpy.float32)
            # Normalise float32 array so that values are between -1.0 and +1.0
            audio_normalised = audio_as_np_float32 * environment.SHORT_NORMALIZE
            print("Transcribing...")
            result = self.model.transcribe(audio_normalised, fp16=self.fp16, language=self.language)
            # Printing the transcribed text
            # print(result['text'])
            return result['text']

    def process_consciousness(self, ctx, pipe):
        n = Pyre(self.id)
        n.set_header("id", self.id)
        n.set_header("type", "brain")
        n.join("CONSCIOUSNESS")
        n.start()

        poller = zmq.Poller()
        poller.register(pipe, zmq.POLLIN)
        # print(n.socket())
        poller.register(n.socket(), zmq.POLLIN)
        # print(n.socket())

        while True:
            items = dict(poller.poll())
            # print(n.socket(), items)
            if pipe in items and items[pipe] == zmq.POLLIN:  # Sent from self!
                message = pipe.recv().decode('utf-8')
                print("CONSCIOUSNESS MESSAGE: %s" % message)
                # message to quit
                if message == "$$STOP":  # This will throw an error if the data is not encoded
                    break
                n.shouts("CONSCIOUSNESS", message)
            else:  # Sent from peer organs
                cmds = n.recv()
                msg_type = cmds.pop(0).decode('utf-8')
                msg_uuid = uuid.UUID(bytes=cmds.pop(0))
                msg_name = cmds.pop(0).decode('utf-8')
                # print("NODE_MSG TYPE: %s" % msg_type)
                # print("NODE_MSG PEER: %s" % msg_uuid)
                # print("NODE_MSG NAME: %s" % msg_name)
                print("NODE_MSG CONT: %s" % cmds)

        n.stop()


if __name__ == '__main__':
    b = Brain()
