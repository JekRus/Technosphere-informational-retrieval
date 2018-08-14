#!/usr/bin/env python
import os
import sys
import encoding
import parser
import pickle
import re
import mmh3

def load_obj(name):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)

def exec_tree(query_tree, Term_dict, InvIndexEncoded, num_docID):
    if(query_tree is None):
        return set()
    if(query_tree.is_operator):
        S1 = exec_tree(query_tree.left, Term_dict, InvIndexEncoded, num_docID)
        S2 = exec_tree(query_tree.right, Term_dict, InvIndexEncoded, num_docID)
        op = query_tree.value
        if(op == '!'):
            S = set(range(num_docID))
            return S - S2
        elif(op == '&'):
            return S1 & S2
        elif(op == '|'):
            return S1 | S2
        else:
            print "ERROR"
            return None
    else:
        ###query_tree.is_term == True
        term_hash = mmh3.hash64(query_tree.value)[0]
        if(term_hash in Term_dict):
            substr = InvIndexEncoded[Term_dict[term_hash][0] : Term_dict[term_hash][0] + Term_dict[term_hash][1]]
            return set(encoder.decode(substr))
        else:
            return set()


URLs = load_obj("urls")
Term_dict = load_obj("dict")
fd = open("encoder.txt", "r")
encoder_type = fd.readline()
fd.close()
if(encoder_type == "varbyte"):
    encoder = encoding.Varbyte()
else:
    encoder = encoding.Simple9()
fd = open("InvIndexEncoded.txt", "r")
InvIndexEncoded = fd.read()
fd.close()
for line in sys.stdin:
    line = re.sub("\n", "", line, flags=re.UNICODE)
    query_tree = parser.parse_query(line.decode('UTF-8').lower())
    result = exec_tree(query_tree, Term_dict, InvIndexEncoded, len(URLs))
    print line
    print len(result)
    for docID in sorted(result):
        print URLs[docID]
