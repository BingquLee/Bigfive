#-*-coding=utf-8-*-
import os
import sys
import time
import csv
import heapq
import random
from decimal import *
import jieba

import sys
sys.path.append('../../../')
from config import *
from time_utils import *
from global_utils import ESIterator

ABS_PATH = os.path.dirname(os.path.abspath(__file__))

def load_train():#读取生成之后的tfidf文档，对新的用户进行话题分类

    domain_dict = dict()
    domain_count = dict()
    for i in TOPIC_LIST:
        reader = csv.reader(open(os.path.join(ABS_PATH, 'topic_dict/%s_tfidf.csv' % i), 'r'))
        word_dict = dict()
        count = 0
        for f,w_text in reader:
            f = f.strip('\xef\xbb\xbf')
            word_dict[str(w_text)] = Decimal(f)
            count = count + Decimal(f)
        domain_dict[i] = word_dict
        domain_count[i] = count

    len_dict = dict()
    total = 0
    for k,v in domain_dict.items():
        len_dict[k] = len(v)
        total = total + len(v)
    
    return domain_dict,domain_count,len_dict,total

DOMAIN_DICT,DOMAIN_COUNT,LEN_DICT,TOTAL = load_train()


def sta_dict():#标准化话题字典

    topic_dict = dict()
    for name in TOPIC_LIST:
        topic_dict[name] = 0

    return topic_dict

TOPIC_DICT = sta_dict()


class TopkHeap(object):
    def __init__(self, k):
        self.k = k
        self.data = []
 
    def Push(self, elem):
        if len(self.data) < self.k:
            heapq.heappush(self.data, elem)
        else:
            topk_small = self.data[0][0]
            if elem[0] > topk_small:
                heapq.heapreplace(self.data, elem)
 
    def TopK(self):
        return [x for x in reversed([heapq.heappop(self.data) for x in range(len(self.data))])]

def com_p(word_list,domain_dict,domain_count,len_dict,total):

    p = 0
    test_word = set(word_list.keys())
    train_word = set(domain_dict.keys())
    c_set = test_word & train_word
    p = sum([float(domain_dict[k]*word_list[k])/float(domain_count) for k in c_set])

    return p

def load_weibo(uid_weibo):

    result_data = dict()
    p_data = dict()
    for k,v in uid_weibo.items():
        domain_p = TOPIC_DICT
        for d_k in domain_p.keys():
            domain_p[d_k] = com_p(v,DOMAIN_DICT[d_k],DOMAIN_COUNT[d_k],LEN_DICT[d_k],TOTAL)#计算文档属于每一个类的概率

            end_time = time.time()

        result_data[k] = domain_p
        p_data[k] = rank_result(domain_p)

    return result_data,p_data

def rank_dict(has_word):

    n = len(has_word)
    keyword = TopkHeap(n)
    count = 0
    for k,v in has_word.items():
        keyword.Push((v,k))
        count = count + v

    keyword_data = keyword.TopK()
    return keyword_data,count    

def rank_result(domain_p):
    
    data_v,count = rank_dict(domain_p)
    if count == 0:
        uid_topic = ['life']
    else:
        uid_topic = [data_v[0][1],data_v[1][1],data_v[2][1]]

    return uid_topic

def topic_classfiy(uid_list,uid_weibo):#话题分类主函数
    '''
    用户话题分类主函数
    输入数据示例：
    uidlist:uid列表（[uid1,uid2,uid3,...]）
    uid_weibo:分词之后的词频字典（{uid1:{'key1':f1,'key2':f2...}...}）

    输出数据示例：字典
    用户18个话题的分布：
    {uid1:{'art':0.1,'social':0.2...}...}
    用户关注较多的话题（最多有3个）：
    {uid1:['art','social','media']...}
    '''
    if not len(uid_weibo) and len(uid_list):
        result_data = dict()
        uid_topic = dict()
        for uid in uid_list:
            result_data[uid] = TOPIC_DICT
            uid_topic[uid] = ['life']
        return result_data,uid_topic
    elif len(uid_weibo) and not len(uid_list):
        uid_list = uid_weibo.keys()
    elif not len(uid_weibo) and not len(uid_list):
        result_data = dict()
        uid_topic = dict()
        return result_data,uid_topic
    # elif
    else:
        pass        
        
    result_data,uid_topic = load_weibo(uid_weibo)#话题分类主函数

    for uid in uid_list:
        if uid not in result_data.keys():
            result_data[uid] = TOPIC_DICT
            uid_topic[uid] = ['life']
    
    return result_data,uid_topic


####################################

def stopwordslist():
    stopwords = [line.strip() for line in open(os.path.join(ABS_PATH, 'stop_words.txt')).readlines()]
    return stopwords


def segment(doc):
    '''
    用jieba分词对输入文档进行分词，并保存至本地（根据情况可跳过）
    '''
    seg_list = " ".join(jieba.cut(doc, cut_all=False)) #seg_list为str类型

    return seg_list


def wordCount(segment_list):
    '''
        该函数实现词频的统计，并将统计结果存储至本地。
        在制作词云的过程中用不到，主要是在画词频统计图时用到。
    '''
    stopwords = stopwordslist()
    word_lst = []
    word_dict = {}
   
    word_lst.append(segment_list.split(' ')) 
    for item in word_lst:
        for item2 in item :
            if item2 not in stopwords:
                if item2 not in word_dict: 
                    word_dict[item2] = 1
                else:
                    word_dict[item2] += 1

    word_dict_sorted = dict(sorted(word_dict.items(), key = lambda item:item[1], reverse=True))#按照词频从大到小排序

    return word_dict_sorted


def get_uid_weibo(uid,index_name):

    uid_word_dict = dict()
    uid_text = ""

    for index_item in index_name:

        query_body ={"query": {"bool": {"must":[{"term": {"uid": uid}}]}}}
        sort_dict = {'_id':{'order':'asc'}}
        try:
            ESIterator1 = ESIterator(0,sort_dict,1000,index_item,"text",query_body,es_weibo)
            while True:
                try:
                    #一千条es数据
                    es_result = next(ESIterator1)
                    if len(es_result):
                        for i in range(len(es_result)):
                            uid_text += es_result[i]["_source"]["text"] 
                    else:
                        pass
                       
                except StopIteration:
                    #遇到StopIteration就退出循环
                    break
        except:
            continue

    if uid_text != "":
        segment_list = segment(uid_text)
        word_count_dict = wordCount(segment_list)
        uid_word_dict[uid] = word_count_dict
    else:
        return uid_word_dict

    return uid_word_dict


def save_user_topic(uid,timestamp,uid_topic_dict,is_none):
    if is_none == False:
        id_body = {
                                "query":{
                                    "ids":{
                                        "type":"text",
                                        "values":[
                                            str(uid)+"_"+str(timestamp)
                                        ]
                                    }
                                }
                            }
        if es.search(index=USER_DOMAIN_TOPIC, doc_type='text', body= id_body)["hits"]["hits"] != []:#1970833007_1479484800
            
            es.update(index=USER_DOMAIN_TOPIC, doc_type='text', id=str(uid)+"_"+str(timestamp), body = {
            "doc":
            {"timestamp": timestamp,
            "uid":uid,
            "topic_art":uid_topic_dict[uid]["art"],
            "topic_computer":uid_topic_dict[uid]["computer"],
            "topic_economic":uid_topic_dict[uid]["economic"],
            "topic_education":uid_topic_dict[uid]["education"],
            "topic_environment":uid_topic_dict[uid]["environment"],
            "topic_medicine":uid_topic_dict[uid]["medicine"],
            "topic_military":uid_topic_dict[uid]["military"],
            "topic_politics":uid_topic_dict[uid]["politics"],
            "topic_sports":uid_topic_dict[uid]["sports"],
            "topic_traffic":uid_topic_dict[uid]["traffic"],
            "topic_life":uid_topic_dict[uid]["life"],
            "topic_anti_corruption":uid_topic_dict[uid]["anti-corruption"],
            "topic_employment":uid_topic_dict[uid]["employment"],
            "topic_violence":uid_topic_dict[uid]["fear-of-violence"],
            "topic_house":uid_topic_dict[uid]["house"],
            "topic_law":uid_topic_dict[uid]["law"],
            "topic_peace":uid_topic_dict[uid]["peace"],
            "topic_religion":uid_topic_dict[uid]["religion"],
            "topic_social_security":uid_topic_dict[uid]["social-security"],
            "has_new_information":1
         
                }},timeout=50)
        
        else:

            es.index(index=USER_DOMAIN_TOPIC,doc_type="text",id=str(uid)+"_"+str(timestamp),
            body={
            "timestamp": timestamp,
            "uid":uid,
            "topic_art":uid_topic_dict[uid]["art"],
            "topic_computer":uid_topic_dict[uid]["computer"],
            "topic_economic":uid_topic_dict[uid]["economic"],
            "topic_education":uid_topic_dict[uid]["education"],
            "topic_environment":uid_topic_dict[uid]["environment"],
            "topic_medicine":uid_topic_dict[uid]["medicine"],
            "topic_military":uid_topic_dict[uid]["military"],
            "topic_politics":uid_topic_dict[uid]["politics"],
            "topic_sports":uid_topic_dict[uid]["sports"],
            "topic_traffic":uid_topic_dict[uid]["traffic"],
            "topic_life":uid_topic_dict[uid]["life"],
            "topic_anti_corruption":uid_topic_dict[uid]["anti-corruption"],
            "topic_employment":uid_topic_dict[uid]["employment"],
            "topic_violence":uid_topic_dict[uid]["fear-of-violence"],
            "topic_house":uid_topic_dict[uid]["house"],
            "topic_law":uid_topic_dict[uid]["law"],
            "topic_peace":uid_topic_dict[uid]["peace"],
            "topic_religion":uid_topic_dict[uid]["religion"],
            "topic_social_security":uid_topic_dict[uid]["social-security"],
            "has_new_information":1,
            "domain_followers":"other",
            "domain_weibo":"other",
            "domain_verified":"other",
            "main_domain" : "other"
                    },timeout=50)
    else:
        id_body = {
                    "query":{
                        "ids":{
                            "type":"text",
                            "values":[
                                str(uid)+"_"+str(timestamp)
                            ]
                        }
                    }
                }
        if es.search(index=USER_DOMAIN_TOPIC, doc_type='text', body= id_body)["hits"]["hits"] != []:
                
            es.update(index=USER_DOMAIN_TOPIC, doc_type='text', id=str(uid)+"_"+str(timestamp), body = {
            "doc":
            {
                "timestamp": timestamp,
                "uid":uid,
                "topic_art":0,
                "topic_computer":0,
                "topic_economic":0,
                "topic_education":0,
                "topic_environment":0,
                "topic_medicine":0,
                "topic_military":0,
                "topic_politics":0,
                "topic_sports":0,
                "topic_traffic":0,
                "topic_life":0,
                "topic_anti_corruption":0,
                "topic_employment":0,
                "topic_violence":0,
                "topic_house":0,
                "topic_law":0,
                "topic_peace":0,
                "topic_religion":0,
                "topic_social_security":0,
                "has_new_information":0            
                        }},timeout=50)
          
        else:

            es.index(index=USER_DOMAIN_TOPIC,doc_type="text",id=str(uid)+"_"+str(timestamp),
            body={
                "timestamp": timestamp,
                "uid":uid,
                "topic_art":0,
                "topic_computer":0,
                "topic_economic":0,
                "topic_education":0,
                "topic_environment":0,
                "topic_medicine":0,
                "topic_military":0,
                "topic_politics":0,
                "topic_sports":0,
                "topic_traffic":0,
                "topic_life":0,
                "topic_anti_corruption":0,
                "topic_employment":0,
                "topic_violence":0,
                "topic_house":0,
                "topic_law":0,
                "topic_peace":0,
                "topic_religion":0,
                "topic_social_security":0,
                "has_new_information":0,
                "domain_followers":"other",
                "domain_weibo":"other",
                "domain_verified":"other",
                "main_domain" : "other"           
                        },timeout=50)
        


def get_user_topic(uid,start_date,end_date):

    for day in get_datelist_v2(start_date,end_date):
        timestamp = date2ts(day)
        index_list = []
        for i in range(7):
            date = ts2date(date2ts(day) - i*DAY)
            index_list.append('flow_text_%s' % date)

        uid_word_dict = get_uid_weibo(uid,index_list)
        if uid_word_dict == {}:
            save_user_topic(uid,timestamp,{},is_none=True)
        else:
            uid_topic_dict,uid_topic = topic_classfiy([uid],uid_word_dict)
            save_user_topic(uid,timestamp,uid_topic_dict,is_none = False)


if __name__ == '__main__':

    user_topic_run(ES_INDEX_LIST)