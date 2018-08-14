# coding: utf-8


import sys
import random
import re
import urllib
from collections import Counter

def extract_features(INPUT_FILE_1, INPUT_FILE_2, OUTPUT_FILE):
	URLs_ex = []
	URLs_gen = []
	#читаем из файлов
	f = open(INPUT_FILE_1, 'r')
	URLs_ex = f.readlines()
	f.close()
	f = open(INPUT_FILE_2, 'r')
	URLs_gen = f.readlines()
	f.close()
	#делаем random sample
	urls_numb = 1000
	URLs = ([ URLs_ex[i] for i in sorted(random.sample(xrange(len(URLs_ex)), urls_numb)) ] + 
			[ URLs_gen[j] for j in sorted(random.sample(xrange(len(URLs_gen)), urls_numb)) ])
	
	#уберем ненужное
	for i in xrange(len(URLs)):
		URLs[i] = re.sub(".+://", "", URLs[i])
		URLs[i] = re.sub("/\n", "", URLs[i])
		URLs[i] = re.sub("\n", "", URLs[i])
	
	#выделяем пути и параметры
	Paths = []
	Parameters = []
	for url in URLs:
		lst_split = re.split(r"\?" , urllib.unquote(unicode(url)))
		#убираем имя хоста
		path = re.split(r"/" , lst_split[0], maxsplit=1)
		if(len(path) == 2):
			Paths.append(path[1])
		if(len(lst_split) == 2):
			Parameters.append(lst_split[1])
	
	Features = Counter()
	
	#вторая и третья фича
	for param in Parameters:
		result = re.split(r"&" , param)
		for p in result: #p = "param=value"
			Features[p] += 1
			param_name = re.split(r'=' , p)[0]
			Features["param_name:"+param_name] += 1
	
	#первая фича + фичи из 4 блока
	for path in Paths:
		key = "segments:" + str(len(re.findall(r'/', path)) + 1)
		Features[key] += 1
		segments = re.split(r"/", path)
		for i , segment in enumerate(segments):
			index = str(i)
			Features["segment_name_"+index+":"+segment] += 1
			Features["segment_len_"+index+":"+str(len(segment))] += 1
			ext = re.search(r"(\.)([^\.]+$)" , segment)
			if(ext):
				Features["segment_ext_"+index+":"+ext.group(2)] += 1
			if(segment.isdigit()):
				Features["segment_[0-9]_"+index+":1"] += 1
			if(re.match(r"[^\d]+\d+[^\d]+$" , segment)):
				Features["segment_substr[0-9]_"+index+":1"] += 1
				if(ext):
					Features["segment_ext_substr[0-9]_"+index+ext.group(2)] += 1
	
	threshold = 100
	f = open(OUTPUT_FILE, 'w')
	Features_sorted = Features.most_common()
	for k, v in Features_sorted:
		if(v < threshold):
			break
		f.write(k+"\t"+str(v)+"\n")
	f.close()
	
	return

