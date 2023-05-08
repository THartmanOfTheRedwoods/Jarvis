#!/usr/bin/env python

import zmq
import json
import uuid
from pyre import Pyre
from environment import NETWORKS
# from pprint import pprint


class AfferentNeuron:

    # Template Function for mind/organ processing via Pyre.
    @staticmethod
    def process(organ_id, organ_name: str, pipe, network: NETWORKS,
                handle_introspection=None,  # Function to handle mind/organ messages to self.
                handle_shout=None,  # Function to handle broadcast messages from other organs.
                handle_connection=None):    # Function to handle connecting to new organs.
        # Start-up phase of algorithm. If this needs to be unique, may encapsulate in a subclass method in the future.
        n = Pyre(organ_id)
        n.set_header("id", organ_id)
        n.set_header("type", organ_name)
        n.join(network.value)
        n.start()
        # Set up network poller to garner messages.
        poller = zmq.Poller()
        poller.register(pipe, zmq.POLLIN)
        # print(n.socket())
        poller.register(n.socket(), zmq.POLLIN)
        # print(n.socket())

        # Infinite processing loop.
        while True:
            items = dict(poller.poll())
            # print(n.socket(), items)
            if pipe in items and items[pipe] == zmq.POLLIN:  # Autonomous message to self
                message = pipe.recv()
                if handle_introspection:  # Only handle this internal message if we're told to.
                    if handle_introspection(n, network, message) == "$$STOP":
                        break
            else:  # Autonomous messages from other organs
                cmds = n.recv()
                msg_type = cmds.pop(0).decode('utf-8')
                msg_uuid = uuid.UUID(bytes=cmds.pop(0))
                msg_name = cmds.pop(0).decode('utf-8')
                # print("NODE_MSG TYPE: %s" % msg_type)
                # print("NODE_MSG PEER: %s" % msg_uuid)
                # print("NODE_MSG NAME: %s" % msg_name)
                if msg_type == "SHOUT":
                    msg_group = cmds.pop(0).decode('utf-8')  # Should be same as network.value most times.
                    # print("NODE_MSG GROUP: %s" % msg_group)
                    if handle_shout:  # Only handle network broadcasts if we're told to
                        handle_shout(msg_uuid, msg_name, msg_group, cmds)
                elif msg_type == "ENTER":  # This is where we register our organs.
                    headers = json.loads(cmds.pop(0).decode('utf-8'))
                    if handle_connection:  # Only handle network connections if we're told to
                        handle_connection(msg_uuid, msg_name, network, headers, cmds)
                # print("NODE_MSG CONT: %s" % cmds)
        n.stop()
