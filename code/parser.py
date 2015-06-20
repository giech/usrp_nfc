import json
from command import TagType
from reader import Reader
from tag import Tag

# json is array. each entry is dict, 
# entry-> tag/reader
# rands-> array of arrays (each 4 bytes), optional
# for tag: type->ULTRALIGHT/CLASSIC1K, mem -> array of bytes
# for reader: keya, keyb->array of 6 bytes, optional

class Parser:

    def __init__(self, name=None):
        if name:
            f = open(name)
            self._ar = json.load(f)
            f.close()
        else:
            self._ar = []


    def get_reader(self, callback):
        rands = []
        keya = []
        keyb = []
        
        ar = self._ar
        for d in ar:
            if d.get('entry','') == 'reader':
                rands = d.get('rands', [])
                keya = d.get('keya', [])
                keyb = d.get('keyb', [])
                break
        return Reader(callback, rands, keya, keyb)


    def get_tag(self, callback):
        tag_type = TagType.CLASSIC1K
        rands = []
        memory = Tag.generate_1k()

        ar = self._ar
        for d in ar:
            if d.get('entry','') == 'tag':
                rands = d.get('rands', [])
                tp = d.get('type', '')
                if tp == 'ULTRALIGHT':
                    tag_type = TagType.ULTRALIGHT
                memory = d.get('mem', [])
                break

        return Tag(callback, tag_type, memory, rands)
