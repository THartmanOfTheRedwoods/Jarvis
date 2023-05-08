#!/usr/bin/env python

from enum import Enum

# Will be used to normalise float32 array so that values are between -1.0 and +1.0
SHORT_NORMALIZE = 3.0517578125e-05  # i.e. (1.0/32768.0) where 32,768 is largest possible 16 bit int i.e. 2**15


class NETWORKS(Enum):
    AUTONOMOUS = '1'
    CONSCIOUSNESS = '2'
