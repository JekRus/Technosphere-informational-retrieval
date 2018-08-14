#!/usr/bin/env python

"""
This just a draft for homework 'near-duplicates'
Use MinshinglesCounter to make result closer to checker
"""

import sys
import re
import gc
from operator import itemgetter
from itertools import groupby
from itertools import combinations, permutations
from collections import Counter
import mmh3
from docreader import DocumentStreamReader

class MinshinglesCounter:
    SPLIT_RGX = re.compile(r'\w+', re.U)

    def __init__(self, window=5, n=20):
        self.window = window
        self.n = n

    def count(self, text):
        words = MinshinglesCounter._extract_words(text)
        shs = self._count_shingles(words)
        mshs = self._select_minshingles(shs)

        if len(mshs) == self.n:
            return mshs

        if len(shs) >= self.n:
            return sorted(shs)[0:self.n]

        return None

    def _select_minshingles(self, shs):
        buckets = [None]*self.n
        for x in shs:
            bkt = x % self.n
            buckets[bkt] = x if buckets[bkt] is None else min(buckets[bkt], x)

        return filter(lambda a: a is not None, buckets)

    def _count_shingles(self, words):
        shingles = []
        for i in xrange(len(words) - self.window):
            h = mmh3.hash(' '.join(words[i:i+self.window]).encode('utf-8'))
            shingles.append(h)
        return sorted(shingles)

    @staticmethod
    def _extract_words(text):
        words = re.findall(MinshinglesCounter.SPLIT_RGX, text)
        return words


def main():
    mhc = MinshinglesCounter()
    URLs = []
    pairs = []
    docid = 0
    for path in sys.argv[1:]:
        for doc in DocumentStreamReader(path):
            URLs.append(doc.url)
            minshingles = mhc.count(doc.text)
            if minshingles:
                for msh in minshingles:
                    pairs.append((msh, docid))
            docid += 1

    pairs.sort()
    grouped_docs = []
    for key, val in groupby(pairs, itemgetter(0)):
        lst = list(val)
        if(len(lst) >= 2):
            grouped_docs.append(sorted(set([x[1] for x in lst])))
    
    counts = Counter()
    for doc in grouped_docs:
        for c in combinations(doc, 2):
            counts[c] += 1
    
    for key in counts:
        N = counts[key]
        similarity = N / float(N + 2*(20.0 - N))
        if(similarity >= 0.75):
            print "%s %s %f" %(URLs[key[0]], URLs[key[1]], similarity)

    return


if __name__ == '__main__':
    main()
