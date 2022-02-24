# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

import json

from .json_encoder import JsonEncoder


# This class contains global plugin settings.
# There can only be one global settings. 
class GlobalSettings:
    def __init__(self):
        self.config_version = 2
        self.auto_load_last_config = False

    def save_to_file(self, file_path):
        json_string = json.dumps(self, sort_keys=True, indent=4, cls=JsonEncoder)
        try:
            with open(file_path, 'wt') as writeFile:
                writeFile.writelines(json_string)
        except:
            print('Failed to save global settings {}'.format(file_path))

    def load_from_file(self, file_path):
        try:
            with open(file_path, 'rt') as readFile:
                json_string = readFile.readlines()
                if len(json_string) > 0:
                    json_string = ' '.join(json_string)  # Turn the list of strings into one string.
                    data = json.loads(json_string)
                    if 'auto_load_last_config' in data: self.auto_load_last_config = data['auto_load_last_config']
        except:
            pass
