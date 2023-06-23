"""
Base Class for DesktopEntry, IconTheme and IconData
"""

import os.path
import codecs

class IniFile:
    filename = ''

    def __init__(self, filename=None):
        self.content = {}
        if filename:
            self.parse(filename)

    def parse(self, filename):
        # for performance reasons
        content = self.content

        if not os.path.isfile(filename):
            return

        # parse file
        try:
            file(filename, 'r')
        except IOError:
            return

        for line in file(filename,'r'):
            line = line.strip()
            if not line or line[0] == '#':
                continue
            index = line.find("=")
            key = line[:index].strip()
            value = line[index+1:].strip()
            if not self.hasKey(key):
                content[key] = value

        self.filename = filename

    def get(self, key):
        if key not in self.content.keys():
            self.set(key, "")
        return self.content[key]

    def write(self, filename = None):
        if not filename and not self.filename:
            return

        if filename:
            self.filename = filename
        else:
            filename = self.filename

        if not os.path.isdir(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        fp = codecs.open(filename, 'w')
        for (key, value) in self.content.items():
            fp.write("%s=%s\n" % (key, value))
        fp.write("\n")

    def set(self, key, value):
        self.content[key] = value

    def removeKey(self, key):
        for (name, value) in self.content.items():
            if key == name:
                del self.content[name]

    def hasKey(self, key):
        return bool(self.content.has_key(key))

    def getFileName(self):
        return self.filename
