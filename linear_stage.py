import numpy as np
import serial
import os
import time
import json


class LinearStage():
    """

    """

    def __init__(self, thread_pitch = None, stp_per_rev = None, json_path = None):
        self.thread_pitch = thread_pitch
        self.stp_per_rev = stp_per_rev
        self.json_path = json_path
        return

    def read_json(self):
        if self.json_path:
            json_dict = json.load(self.json_path)
            self.thread_pitch = json_dict["thread_pitch"]
            self.stp_per_rev = json_dict["stp_per_rev"]

        return
