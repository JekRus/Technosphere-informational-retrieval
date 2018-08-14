#!/usr/bin/env python
import os
import sys
import codecs
import docreader
import pickle
from doc2words import extract_words
from collections import defaultdict

def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)
reader = docreader.DocumentStreamReader(docreader.parse_command_line().files)
encoder_type = docreader.parse_command_line().encoder
fd = open("encoder.txt", "w")
fd.write(encoder_type)
fd.close()

URLs = {}
InvIndex = defaultdict(list)
for idx, doc in enumerate(reader):
    URLs[idx] = doc.url
    Terms = list(sorted(set(extract_words(doc.text))))
    for term in Terms:
        InvIndex[term].append(idx)

save_obj(InvIndex, "index")
save_obj(URLs, "urls")
