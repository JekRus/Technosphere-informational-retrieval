#!/usr/bin/env python
import os
import sys
import encoding
import pickle
import re
import mmh3

def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)


fd = open("encoder.txt", "r")
encoder_type = fd.readline()
fd.close()
if(encoder_type == "varbyte"):
    encoder = encoding.Varbyte()
else:
    encoder = encoding.Simple9()
URLs = load_obj("urls")
InvIndex = load_obj("index")
Term_dict = {}
fd = open("InvIndexEncoded.txt", "w")
offset = 0
for term in InvIndex:
    encoded_str = encoder.encode(InvIndex[term])
    fd.write(encoded_str)
    term_hash = mmh3.hash64(term.encode('utf-8'))[0]
    Term_dict[term_hash] = [offset, len(encoded_str)]
    offset += len(encoded_str)
fd.close()
save_obj(Term_dict, "dict")
