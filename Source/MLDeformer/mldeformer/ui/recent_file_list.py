# -*- coding: utf-8 -*-
# Copyright Epic Games, Inc. All Rights Reserved

import json
import os


# A recent file list that can be loaded and saved.
class RecentFileList:
    def __init__(self):
        self.file_list = list()

    # Add a new entry.
    def add(self, recent_file_to_add):
        if recent_file_to_add in self.file_list:
            return
        self.file_list.append(recent_file_to_add)
        if len(self.file_list) > 15:
            self.file_list.pop(0)

    # Load a recent file list from a given file.
    def load(self, file_to_load):
        try:
            with open(file_to_load, 'rt') as readFile:
                json_string = readFile.readlines()
                if len(json_string) > 0:
                    json_string = ' '.join(json_string)  # Turn the list of strings into one string.
                    data = json.loads(json_string)
                    del self.file_list[:]
                    for item in data['file_list']:
                        if os.path.isfile(item):
                            if not item in self.file_list:
                                self.file_list.append(item)
        except:
            pass

    # Save the recent file list to a file.
    def save(self, file_to_save):
        data = json.dumps(self,
                          default=lambda o: o.__dict__,
                          sort_keys=True,
                          indent=4)
        with open(file_to_save, 'wt') as writeFile:
            writeFile.writelines(data)
