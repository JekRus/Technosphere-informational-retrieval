 # coding: utf-8


import sys
import os
import re
import random
import time
import numpy as np
import urllib
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering, Birch, AffinityPropagation
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import SGDClassifier, LogisticRegression
from sklearn.metrics.pairwise import pairwise_distances
from collections import Counter


class Sekitei:
    def __init__(self, Features=None, X=None, y=None, Quota_for_cluster=None, Qlink_rate_for_cluster=None, Clst=None, Clf=None):
        self.Features = Features
        self.X = X
        self.y = y
        self.Quota_for_cluster = Quota_for_cluster
        self.Qlink_rate_for_cluster = Qlink_rate_for_cluster
        self.Clst = Clst
        self.Clf = Clf
        return

    def define_segments(self, QLINK_URLS, UNKNOWN_URLS, QUOTA):
        ###выделяем фичи, пишем их в counter Features
        ###и для каждого урла пишем список всех его фичей в URL_features
        URLs = QLINK_URLS + UNKNOWN_URLS
        URL_features = {} # {url_idx : feature_list}
        Features = Counter()
        #доп фичи для вики
        for idx, url in enumerate(URLs):
            feature_list = []
            if(re.match(r"http://ru.wikipedia.org/wiki/([^/]+)/?\?previous=yes$", url)):
                key = "wiki_feature_4"
                Features[key] += 1
                feature_list.append(key)
            URL_features[idx] = feature_list
        
        for i in xrange(len(URLs)):
            URLs[i] = re.sub(r".+://", r"", URLs[i])
            URLs[i] = re.sub(r"/$", r"", URLs[i])
            URLs[i] = re.sub(r"\n", r"", URLs[i])
        
        #выделяем пути и параметры
        Paths = []
        Parameters = []
        
        for idx, url in enumerate(URLs):
            feature_list = []
            lst_split = re.split(r"\?" , urllib.unquote(unicode(url)))
            #убираем имя хоста
            path = re.split(r"/" , lst_split[0], maxsplit=1)[1]
            result = []
            if(len(lst_split) == 2):
                param = lst_split[1]
                result = re.split(r"&" , param)
            #вторая и третья фича
            for p in result: #p = "param=value"
                Features[p] += 1
                feature_list.append(p)
                param_name = re.split(r'=' , p)[0]
                Features["param_name:"+param_name] += 1
                feature_list.append("param_name:"+param_name)
            #первая фича + фичи из 4 блока
            key = "segments:" + str(len(re.findall(r'/', path)) + 1)
            Features[key] += 1
            feature_list.append(key)
            #доп фичи для википедии
            
            if(re.match(r"wiki/File:[^/]+\.jpg$", path, flags=re.UNICODE)):
                key = "wiki/File.jpg"
                Features[key] += 1
                feature_list.append(key)
            if(re.match(r"wiki/[^/]+\.jpg$", path, flags=re.UNICODE)):
                key = "wiki/.jpg"
                Features[key] += 1
                feature_list.append(key)
            if(re.match(r"wiki/Category:[^/]+$", path, flags=re.UNICODE)):
                key = "wiki/Category"
                Features[key] += 1
                feature_list.append(key)
            if(re.match(r"wiki/Talk:[^/]+$", path, flags=re.UNICODE)):
                key = "wiki/Talk"
                Features[key] += 1
                feature_list.append(key)
            segments = re.split(r"/", path)
            for j , segment in enumerate(segments):
                index = str(j)
                Features["segment_name_"+index+":"+segment] += 1
                feature_list.append("segment_name_"+index+":"+segment)
                Features["segment_len_"+index+":"+str(len(segment))] += 1
                feature_list.append("segment_len_"+index+":"+str(len(segment)))
                ext = re.search(r"(\.)([^\.]+$)" , segment)
                if(ext):
                    Features["segment_ext_"+index+":"+ext.group(2)] += 1
                    feature_list.append("segment_ext_"+index+":"+ext.group(2))
                if(segment.isdigit()):
                    Features["segment_[0-9]_"+index+":1"] += 1
                    feature_list.append("segment_[0-9]_"+index+":1")
                if(re.match(r"[^\d]+\d+[^\d]+$" , segment)):
                    Features["segment_substr[0-9]_"+index+":1"] += 1
                    feature_list.append("segment_substr[0-9]_"+index+":1")
                    if(ext):
                        Features["segment_ext_substr[0-9]_"+index+ext.group(2)] += 1
                        feature_list.append("segment_ext_substr[0-9]_"+index+ext.group(2))
                if(re.match(r"[^a-zA-Z0-9]$", segment, flags=re.UNICODE)):
                    key = "nonEng"
                    Features[key] += 1
                    feature_list.append(key)
            URL_features[idx] = feature_list
        
        #отрезаем фичи по порогу    
        alpha = 0.01
        threshold = int(alpha * len(URLs))
        Features_sorted = Features.most_common()
        Features = {}
        for k, v in Features_sorted:
            if(v < threshold):
                break
            Features[k] = v
            
        #составляем матрицу признаков
        X = np.zeros((len(URLs), len(Features))).astype(int)
        
        for idx, url in enumerate(URLs):
            for f_idx, feature in enumerate(Features):
                if(feature in URL_features[idx]):
                    X[idx,f_idx] = 1
        #кластеризация
        cluster_numb = 15
        Clst= KMeans(cluster_numb)
        Clst.fit(X)
        y = Clst.labels_
        y_qlink = y[:len(QLINK_URLS)]
        y_unknown = y[len(QLINK_URLS):]
        
        Clf = LogisticRegression(tol=1e-2)
        q_links = np.zeros(len(URLs))
        q_links[:len(QLINK_URLS)] = 1
        Clf.fit(X, q_links)
        #вычисляем квоту на каждый кластер
        Quota_for_cluster = Counter()
        Qlink_rate_for_cluster = {}
        
        for label in y_qlink:
            Quota_for_cluster[label] += 1
        
        min_quota = 100
        
        for key in Quota_for_cluster:
            Qlink_rate_for_cluster[key] = float(Quota_for_cluster[key]/float(len(QLINK_URLS)))
            if(Qlink_rate_for_cluster[key] > 0.1):
                min_quota *= 2
        
        QUOTA -= min_quota * (np.max(y) + 1)
        
        for key in Quota_for_cluster:   
            Quota_for_cluster[key] = min_quota * Qlink_rate_for_cluster[key] * float(len(QLINK_URLS))
            
                
        self.__init__(Features, X, y, Quota_for_cluster, Qlink_rate_for_cluster, Clst, Clf)
        return
        
    def fetch_url(self, url):
        #парсим фичи урла
        feature_list = []
        if(re.match(r"http://ru.wikipedia.org/wiki/([^/]+)/?\?previous=yes$", url)):
            key = "wiki_feature_4"
            feature_list.append(key)
        
        url = re.sub(r".+://", r"", url)
        url = re.sub(r"/$", r"", url)
        url = re.sub(r"\n", r"", url)
        
        lst_split = re.split(r"\?" , urllib.unquote(unicode(url)))
        #убираем имя хоста
        path = re.split(r"/" , lst_split[0], maxsplit=1)[1]
        result = []
        if(len(lst_split) == 2):
            param = lst_split[1]
            result = re.split(r"&" , param)
        #вторая и третья фича
        for p in result: #p = "param=value"
            feature_list.append(p)
            param_name = re.split(r'=' , p)[0]
            feature_list.append("param_name:"+param_name)
        #первая фича + фичи из 4 блока
        key = "segments:" + str(len(re.findall(r'/', path)) + 1)
        feature_list.append(key)
        #доп фичи для википедии
        
        if(re.match(r"wiki/File:[^/]+\.jpg$", path, flags=re.UNICODE)):
            key = "wiki/File.jpg"
            feature_list.append(key)
        if(re.match(r"wiki/[^/]+\.jpg$", path, flags=re.UNICODE)):
            key = "wiki/.jpg"
            feature_list.append(key)
        if(re.match(r"wiki/Category:[^/]+$", path, flags=re.UNICODE)):
            key = "wiki/Category"
            feature_list.append(key)
        if(re.match(r"wiki/Talk:[^/]+$", path, flags=re.UNICODE)):
            key = "wiki/Talk"
            feature_list.append(key)
        
        segments = re.split(r"/", path)
        for j , segment in enumerate(segments):
            index = str(j)
            feature_list.append("segment_name_"+index+":"+segment)
            feature_list.append("segment_len_"+index+":"+str(len(segment)))
            ext = re.search(r"(\.)([^\.]+$)" , segment)
            if(ext):
                feature_list.append("segment_ext_"+index+":"+ext.group(2))
            if(segment.isdigit()):
                feature_list.append("segment_[0-9]_"+index+":1")
            if(re.match(r"[^\d]+\d+[^\d]+$" , segment)):
                feature_list.append("segment_substr[0-9]_"+index+":1")
                if(ext):
                    feature_list.append("segment_ext_substr[0-9]_"+index+ext.group(2))
            if(re.match(r"[^a-zA-Z0-9]$", segment, flags=re.UNICODE)):
                    key = "nonEng"
                    feature_list.append(key)
            
        #составляем вектор признаков урла
        X_url = np.zeros(len(self.Features)).astype(int)
        for f_idx, feature in enumerate(self.Features):
            if(feature in feature_list):
                X_url[f_idx] = 1
        #классифицируем урл
        url_label = int(self.Clst.predict(X_url.reshape(1, -1)))
        is_qlink = bool(self.Clf.predict(X_url.reshape(1, -1)))
        result = False
        if(self.Quota_for_cluster[url_label] > 0):
            if(is_qlink or (random.random() - 0.4 < self.Qlink_rate_for_cluster[url_label])):
                self.Quota_for_cluster[url_label] -= 1
                result = True
            
            
        
        return result
        
        
sekitei = Sekitei();

def define_segments(QLINK_URLS, UNKNOWN_URLS, QUOTA):
    sekitei.define_segments(QLINK_URLS, UNKNOWN_URLS, QUOTA)
    return


#
# returns True if need to fetch url
#
def fetch_url(url):
    global sekitei
    return sekitei.fetch_url(url);
    
    
