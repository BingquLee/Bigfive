#-*-coding=utf-8-*-
# -*- coding: UTF-8 -*-

import sys
sys.path.append('../../')
from config import *
from time_utils import *
from global_utils import * 
import operator

def get_user_list(event_name):
    user_list = []
    iter_num = 0
    iter_get_user = USER_ITER_COUNT
    while (iter_get_user == USER_ITER_COUNT):
        query_body = {
                "_source":["uid"],
                "query": {
                    "bool": {
                        "must": [
                        {
                        "match_all": { }
                        }
                    ]
                }
            },
            'sort':{
                '_uid':{
                    'order':'asc'
                }
            },
            "size":USER_ITER_COUNT,
            "from":iter_num * USER_ITER_COUNT
        }
        es_result = es.search(index=event_name,doc_type='text',body=query_body)['hits']['hits']
        iter_get_user = len(es_result)
        iter_num += 1

        user_list.extend([hit['_source']['uid'] for hit in es_result])
        if len(user_list) == 0:
            break

    user_list_set = list(set(user_list))

    return user_list_set


def get_event_personality(event_id, event_mapping_name, user_list, start_date, end_date):
    #起止时间
    start_ts = int(date2ts(start_date))
    end_ts = int(date2ts(end_date))+DAY

    personality_dict = {
        "event_id":event_id,
        "timestamp":int(date2ts(end_date)),
        "date":end_date
    }
    for personality_label in PERSONALITY_LABEL_LIST:
        query_body_low = {
                    "query":{
                        "bool":{
                            "must":[
                                    {"terms":{"uid":user_list}},
                                    {"term":{personality_label:0}}
                                    ]
                                }
                        },
                    "size":MAX_VALUE

        }
        query_body_high = {
                    "query":{
                        "bool":{
                            "must":[
                                    {"terms":{"uid":user_list}},
                                    {"term":{personality_label:2}}
                                    ]
                                }
                        } ,
                    "size":MAX_VALUE
        }

        es_result_low = es.search(index= USER_RANKING ,doc_type="text",body=query_body_low)["hits"]["hits"]
        es_result_high = es.search(index= USER_RANKING ,doc_type="text",body=query_body_high)["hits"]["hits"]

        low_user_list = [i["_id"] for i in es_result_low]
        high_user_list = [i["_id"] for i in es_result_high]

        event_query_body_high = {
                    "query":{
                        "bool":{
                            "must":[
                                    {"terms":{"uid":high_user_list}},
                                    {"range": {
                                        "timestamp": {
                                            "gte": start_ts,
                                            "lt": end_ts
                                                }
                                            }
                                        }
                                    ]
                                }
                        } ,
                    "aggs":{"sentiment_aggs":{"terms":{"field":"sentiment"}}}
        }

        res = es.search(index=event_mapping_name,doc_type="text",body=event_query_body_high)
        event_result_high = res["aggregations"]["sentiment_aggs"]["buckets"]
        es_result = res["hits"]["hits"]

        mid_list = []
        if es_result != []:
            event_content = [i["_source"] for i in es_result]
            mid_list = [i["mid"] for i in sorted(event_content,key = operator.itemgetter("timestamp"),reverse = True)[:5]]
        event_result_high.append({"mid_list":mid_list})



        event_query_body_low = {
                    "query":{
                        "bool":{
                            "must":[
                                    {"terms":{"uid":low_user_list}},
                                     {"range": {
                                        "timestamp": {
                                            "gte": start_ts,
                                            "lt": end_ts
                                                }
                                            }
                                        }
                                    ]
                                }
                        } ,
                    "aggs":{"sentiment_aggs":{"terms":{"field":"sentiment"}}}
        }

        res_2 = es.search(index=event_mapping_name,doc_type="text",body=event_query_body_low)
        event_result_low = res_2["aggregations"]["sentiment_aggs"]["buckets"]
        es_result_1 = res_2["hits"]["hits"]

        mid_list_1 = []
        if es_result_1 != []:
            event_content = [i["_source"] for i in es_result_1]
            mid_list_1 = [i["mid"] for i in sorted(event_content,key = operator.itemgetter("timestamp"),reverse = True)[:5]]
        event_result_low.append({"mid_list": mid_list_1})

        personality_dict[str(personality_label.split("_label")[0])+"_high"] = event_result_high
        personality_dict[str(personality_label.split("_label")[0])+"_low"] = event_result_low
    
    id_body = {
            "query":{
                "ids":{
                    "type":"text",
                    "values":[
                        str(event_id)+"_"+str(date2ts(end_date))
                    ]
                }
            }
        }
    if es.search(index="event_personality", doc_type='text', body= id_body)["hits"]["hits"] != []:
        es.update(index='event_personality', doc_type='text', id=str(event_id)+"_"+str(date2ts(end_date)), body = {"doc":personality_dict})
    else:
        es.index(index='event_personality', doc_type='text', id=str(event_id)+"_"+str(date2ts(end_date)), body = personality_dict)



if __name__ == '__main__':
    EVENT_INFORMATION_2 = "event_ceshishijianba_1553071017"

    user_list = get_user_list(EVENT_INFORMATION_2)
    get_event_personality("ceshishijianba_1553071017",EVENT_INFORMATION_2,user_list,"2016-11-13","2016-11-27")
    