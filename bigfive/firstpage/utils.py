# -*- coding: utf-8 -*-
import json
import operator
import os
import random
import PIL.Image as Image

from bigfive.config import es,USER_RANKING,USER_INFORMATION,GROUP_INFORMATION,GROUP_RANKING




def search_group(keyword, page, size, order_name, order_type):
    page = page if page else '1'
    size = size if size else '10'
    if order_name == 'name':
        order_name = 'group_name'
    order_name = order_name if order_name else 'group_name'
    order_type = order_type if order_type else 'asc'
    query = {"query": {"bool": {"must": []}}}
    query['from'] = str((int(page) - 1) * int(size))
    query['size'] = str(size)
    query['sort'] = [{order_name: {"order": order_type}}]
    if keyword:
        group_user_query = '{"wildcard":{"group_name": "*%s*"}}' % keyword
        query['query']['bool']['must'].append(json.loads(group_user_query))
    hits = es.search(index='group_ranking', doc_type='text', body=query)['hits']
    result = {'rows': [], 'total': hits['total']}
    for item in hits['hits']:
        item['_source']['big_five_list'] = []
        item['_source']['dark_list'] = []

        if item['_source']['extroversion_label'] == 0:
            item['_source']['big_five_list'].append({'外倾性': '0'})  # 0代表极端低
        if item['_source']['extroversion_label'] == 2:
            item['_source']['big_five_list'].append({'外倾性': '1'})  # 1代表极端高
        if item['_source']['openn_label'] == 0:
            item['_source']['big_five_list'].append({'开放性': '0'})
        if item['_source']['openn_label'] == 2:
            item['_source']['big_five_list'].append({'开放性': '1'})
        if item['_source']['agreeableness_label'] == 0:
            item['_source']['big_five_list'].append({'宜人性': '0'})
        if item['_source']['agreeableness_label'] == 2:
            item['_source']['big_five_list'].append({'宜人性': '1'})
        if item['_source']['conscientiousness_label'] == 0:
            item['_source']['big_five_list'].append({'尽责性': '0'})
        if item['_source']['conscientiousness_label'] == 2:
            item['_source']['big_five_list'].append({'尽责性': '1'})
        if item['_source']['nervousness_label'] == 0:
            item['_source']['big_five_list'].append({'神经质': '0'})
        if item['_source']['nervousness_label'] == 2:
            item['_source']['big_five_list'].append({'神经质': '1'})

        if item['_source']['machiavellianism_label'] == 0:
            item['_source']['dark_list'].append({'马基雅维里主义': '0'})
        if item['_source']['machiavellianism_label'] == 2:
            item['_source']['dark_list'].append({'马基雅维里主义': '1'})
        if item['_source']['psychopathy_label'] == 0:
            item['_source']['dark_list'].append({'精神病态': '0'})
        if item['_source']['psychopathy_label'] == 2:
            item['_source']['dark_list'].append({'精神病态': '1'})
        if item['_source']['narcissism_label'] == 0:
            item['_source']['dark_list'].append({'自恋': '0'})
        if item['_source']['narcissism_label'] == 2:
            item['_source']['dark_list'].append({'自恋': '1'})

        item['_source']['name'] = item['_source']['group_name']
        item['_source']['id'] = item['_id']
        result['rows'].append(item['_source'])
    return result


def search_person_and_group(keyword, page, size, person_order_name, group_order_name, person_order_type, group_order_type):
    page = page if page else '1'
    size = size if size else '10'
    person_order_name = person_order_name if person_order_name else 'username'
    group_order_name = group_order_name if group_order_name else 'group_name'
    person_order_type = person_order_type if person_order_type else 'asc'
    group_order_type = group_order_type if group_order_type else 'asc'

    person_query = {"query": {"bool": {"must": []}}}
    group_query = {"query": {"bool": {"must": []}}}
    person_query['from'] = str((int(page) - 1) * int(size))
    person_query['size'] = str(size)
    person_query['sort'] = [{person_order_name: {"order": person_order_type}}]

    group_query['from'] = str((int(page) - 1) * int(size))
    group_query['size'] = str(size)
    group_query['sort'] = [{group_order_name: {"order": group_order_type}}]

    if keyword:
        person_user_query = '{"wildcard":{"username": "*%s*"}}' % keyword
        group_user_query = '{"wildcard":{"group_name": "*%s*"}}' % keyword
        person_query['query']['bool']['must'].append(json.loads(person_user_query))
        group_query['query']['bool']['must'].append(json.loads(group_user_query))

    # print(person_query)
    person_result = es.search(index='user_ranking', doc_type='text', body=person_query)['hits']
    group_result = es.search(index='group_ranking', doc_type='text', body=group_query)['hits']

    result = {'person_rows': [], 'person_total': person_result['total'],
              'group_rows': [], 'group_total': group_result['total']}
    for item in person_result['hits']:
        item['_source']['name'] = item['_source']['username']
        result['person_rows'].append(item['_source'])
    for item in group_result['hits']:
        item['_source']['name'] = item['_source']['group_name']
        result['group_rows'].append(item['_source'])

    return result


def get_statistics_user_info(timestamp):
    user_total_count = es.count(index = "user_information",doc_type = "text")["count"]
    timestamp = int(timestamp)
    # print (user_total_count)
    query_body = {"query": {"bool": {"must":[{"range": {"insert_time": {"gte":timestamp,"lt":timestamp + 24*3600}}}]}},"size" : 0}
    today_insert_user_num = es.search(index = "user_information",doc_type = "text",body = query_body)["hits"]["total"]
    # print (today_insert_user_num)
    personality_index_list = ["machiavellianism_index","narcissism_index","psychopathy_index","extroversion_index","nervousness_index","openn_index","agreeableness_index","conscientiousness_index"]
    personality_label_list = ["machiavellianism_label","narcissism_label","psychopathy_label","extroversion_label","nervousness_label","openn_label","agreeableness_label","conscientiousness_label"]
    aggs_avg_dict = {"aggs": {"aggs_index": {"avg":{}}}}

    result =  {}
    result["user_total_count"] = user_total_count
    result["today_insert_user_num"] = today_insert_user_num

    query = {"size" : 0,"aggs":{}}
    for i in personality_index_list:
        query["aggs"].update({i.split("_")[0]:{'avg':{'field':i}}})
    result.update(es.search(index="user_ranking", doc_type="text", body = query)["aggregations"])

    query_body = {"size" : 0,"aggs":{}}
    for i in personality_label_list:
        query["aggs"].update({i.split("_")[0]:{'terms':{'field':i}}})
    aggregations = es.search(index="user_ranking", doc_type="text", body = query)["aggregations"]
    map_dic = {0:'low',2:'high'}
    for k,v in aggregations.items():
        for bucket in v['buckets']:
            # print(bucket)
            if bucket['key'] not in map_dic.keys():
                continue
            result[k][map_dic[bucket['key']]] = bucket['doc_count']
    # result = {"user_total_count": 15003, "today_insert_user_num": 0, "psychopathy": {"value": 47.57635139638739, "low": 809, "high": 267}, "openn": {"value": 64.91701659668067, "high": 771, "low": 575}, "conscientiousness": {"value": 65.33180030660534, "low": 1487, "high": 784}, "extroversion": {"value": 58.44897687129241, "low": 1296, "high": 820}, "machiavellianism": {"value": 65.33006731986936, "low": 499, "high": 250}, "narcissism": {"value": 54.772045590881824, "low": 1244, "high": 776}, "nervousness": {"value": 62.59268146370726, "low": 798, "high": 550}, "agreeableness": {"value": 73.06891954942346, "high": 776, "low": 489}}
    # result = {"user_total_count": 1006136, "today_insert_user_num": 0, "psychopathy": {"value": 47.57635139638739, "low": 66642, "high": 23475}, "openn": {"value": 64.91701659668067, "high": 63636, "low": 48008}, "conscientiousness": {"value": 65.33180030660534, "low": 120624, "high": 64613}, "extroversion": {"value": 58.44897687129241, "low": 105375, "high": 67521}, "machiavellianism": {"value": 65.33006731986936, "low": 41965, "high": 22164}, "narcissism": {"value": 54.772045590881824, "low": 101192, "high": 64038}, "nervousness": {"value": 62.59268146370726, "low": 65699, "high": 45984}, "agreeableness": {"value": 73.06891954942346, "high": 63998, "low": 41202}}
    return result

def dark_personality():
    query_body = {
        "query": {
            "bool": {
                "must": [
                {
                    "range": {
                        "influence_index": {
                        "gt": "50"
                        }
                    }
                }
            ]
         }
    },"size":15000
    }
    es_result = es.search(index=USER_RANKING,doc_type="text",body = query_body)["hits"]["hits"]
    if es_result:
        user_list = [es_result[i]["_source"] for i in range(len(es_result))]

        final_high_dict = dict()
        final_low_dict = dict()
        for i in ["machiavellianism_index","narcissism_index","psychopathy_index"]:
            sorted_high  = sorted(user_list,key=operator.itemgetter(i),reverse=True)[:5]
            sorted_low = sorted(user_list,key=operator.itemgetter(i),reverse=False)[:5]
            high_index_list = []
            low_index_list = []
            high_dict = dict()
            low_dict = dict()

            for j in range(len(sorted_high)):
                a_dict = dict()
                a_dict["name"] = sorted_high[j]["username"]
                a_dict["id"] = sorted_high[j]["uid"]

                query_body = {"query":{"bool":{"must":[{"term":{"uid":sorted_high[j]["uid"]}}]}}}
                photo_url = es.search(index=USER_INFORMATION,doc_type="text",body = query_body)["hits"]["hits"][0]["_source"]["photo_url"]

                a_dict["photo_url"] = photo_url

                a_dict[i] = sorted_high[j][i]

                high_index_list.append(a_dict)


            for m in range(len(sorted_low)):
                a_dict = dict()
                a_dict["name"] = sorted_low[m]["username"]
                a_dict["id"] = sorted_low[m]["uid"]

                query_body = {"query":{"bool":{"must":[{"term":{"uid":sorted_low[m]["uid"]}}]}}}
                photo_url = es.search(index=USER_INFORMATION,doc_type="text",body = query_body)["hits"]["hits"][0]["_source"]["photo_url"]

                a_dict["photo_url"] = photo_url

                a_dict[i] = sorted_low[m][i]
                low_index_list.append(a_dict)

            final_high_dict[i] = high_index_list
            final_low_dict[i] = low_index_list

        result_dict = dict()
        result_dict["high"] = final_high_dict
        result_dict["low"] = final_low_dict

        return result_dict
    return {}
def dark_group():
    query_body = {
        "query": {
            "bool": {
                "must": [
                {
                    "range": {
                        "influence_index": {
                        "gt": 20
                        }
                    }
                }
            ]
         }
    },"size":15000
    }
    es_result = es.search(index=GROUP_RANKING,doc_type="text",body = query_body)["hits"]["hits"]
    if es_result:
        es_result = es.search(index=GROUP_RANKING,doc_type="text",body = query_body)["hits"]["hits"]
        user_list = [es_result[i]["_source"] for i in range(len(es_result))]

        final_high_dict = dict()
        final_low_dict = dict()
        for i in ["machiavellianism_index","narcissism_index","psychopathy_index"]:
            sorted_high  = sorted(user_list,key=operator.itemgetter(i),reverse=True)[:5]
            sorted_low = sorted(user_list,key=operator.itemgetter(i),reverse=False)[:5]
            high_index_list = []
            low_index_list = []
            high_dict = dict()
            low_dict = dict()

            for j in range(len(sorted_high)):
                a_dict = dict()
                a_dict["name"] = sorted_high[j]["group_name"]
                a_dict["id"] = sorted_high[j]["group_id"]

                # query_body = {"query":{"bool":{"must":[{"term":{"uid":sorted_high[j]["uid"]}}]}}}
                # photo_url = es.search(index=USER_INFORMATION,doc_type="text",body = query_body)["hits"]["hits"][0]["_source"]["photo_url"]

                # a_dict["photo_url"] = photo_url

                a_dict[i] = sorted_high[j][i]

                high_index_list.append(a_dict)


            for m in range(len(sorted_low)):
                a_dict = dict()
                a_dict["name"] = sorted_low[m]["group_name"]
                a_dict["id"] = sorted_low[m]["group_id"]

                # query_body = {"query":{"bool":{"must":[{"term":{"uid":sorted_low[m]["uid"]}}]}}}
                # photo_url = es.search(index=USER_INFORMATION,doc_type="text",body = query_body)["hits"]["hits"][0]["_source"]["photo_url"]

                # a_dict["photo_url"] = photo_url

                a_dict[i] = sorted_low[m][i]
                low_index_list.append(a_dict)

            final_high_dict[i] = high_index_list
            final_low_dict[i] = low_index_list

        result_dict = dict()
        result_dict["high"] = final_high_dict
        result_dict["low"] = final_low_dict

        return result_dict
    return {}
def bigfive_personality():
    query_body = {
        "query": {
            "bool": {
                "must": [
                {
                    "range": {
                        "influence_index": {
                        "gt": "50"
                        }
                    }
                }
            ]
         }
    },"size":15000
    }
    if es.search(index=USER_RANKING,doc_type="text",body = query_body)["hits"]["hits"]!= []:
        es_result = es.search(index=USER_RANKING,doc_type="text",body = query_body)["hits"]["hits"]
        user_list = [es_result[i]["_source"] for i in range(len(es_result))]

        final_high_dict = dict()
        final_low_dict = dict()
        for i in ["extroversion_index","nervousness_index","openn_index","agreeableness_index","conscientiousness_index"]:
            sorted_high  = sorted(user_list,key=operator.itemgetter(i),reverse=True)[:5]
            sorted_low = sorted(user_list,key=operator.itemgetter(i),reverse=False)[:5]
            high_index_list = []
            low_index_list = []
            high_dict = dict()
            low_dict = dict()

            for j in range(len(sorted_high)):
                a_dict = dict()
                a_dict["name"] = sorted_high[j]["username"]
                a_dict["id"] = sorted_high[j]["uid"]
                a_dict["extroversion_index"] = sorted_high[j]["extroversion_index"]
                a_dict["nervousness_index"] = sorted_high[j]["nervousness_index"]
                a_dict["openn_index"] = sorted_high[j]["openn_index"]
                a_dict["agreeableness_index"] = sorted_high[j]["agreeableness_index"]
                a_dict["conscientiousness_index"] = sorted_high[j]["conscientiousness_index"]


                query_body = {"query":{"bool":{"must":[{"term":{"uid":sorted_high[j]["uid"]}}]}}}
                photo_url = es.search(index=USER_INFORMATION,doc_type="text",body = query_body)["hits"]["hits"][0]["_source"]["photo_url"]

                a_dict["photo_url"] = photo_url

                a_dict[i] = sorted_high[j][i]

                high_index_list.append(a_dict)


            for m in range(len(sorted_low)):
                a_dict = dict()
                a_dict["name"] = sorted_low[m]["username"]
                a_dict["id"] = sorted_low[m]["uid"]
                a_dict["extroversion_index"] = sorted_low[m]["extroversion_index"]
                a_dict["nervousness_index"] = sorted_low[m]["nervousness_index"]
                a_dict["openn_index"] = sorted_low[m]["openn_index"]
                a_dict["agreeableness_index"] = sorted_low[m]["agreeableness_index"]
                a_dict["conscientiousness_index"] = sorted_low[m]["conscientiousness_index"]

                query_body = {"query":{"bool":{"must":[{"term":{"uid":sorted_low[m]["uid"]}}]}}}
                photo_url = es.search(index=USER_INFORMATION,doc_type="text",body = query_body)["hits"]["hits"][0]["_source"]["photo_url"]

                a_dict["photo_url"] = photo_url

                a_dict[i] = sorted_low[m][i]
                low_index_list.append(a_dict)

            final_high_dict[i] = high_index_list
            final_low_dict[i] = low_index_list

        result_dict = dict()
        result_dict["high"] = final_high_dict
        result_dict["low"] = final_low_dict

        return result_dict

def bigfive_group():
    query_body = {
        "query": {
            "bool": {
                "must": [
                {
                    "range": {
                        "influence_index": {
                        "gt": 20
                        }
                    }
                }
            ]
         }
    },"size":15000
    }
    es_result = es.search(index=GROUP_RANKING,doc_type="text",body = query_body)["hits"]["hits"]
    if es_result:
        user_list = [es_result[i]["_source"] for i in range(len(es_result))]

        final_high_dict = dict()
        final_low_dict = dict()
        for i in ["extroversion_index","nervousness_index","openn_index","agreeableness_index","conscientiousness_index"]:
            sorted_high  = sorted(user_list,key=operator.itemgetter(i),reverse=True)[:5]
            sorted_low = sorted(user_list,key=operator.itemgetter(i),reverse=False)[:5]
            high_index_list = []
            low_index_list = []
            high_dict = dict()
            low_dict = dict()

            for j in range(len(sorted_high)):
                a_dict = dict()
                a_dict["name"] = sorted_high[j]["group_name"]
                a_dict["id"] = sorted_high[j]["group_id"]
                a_dict["extroversion_index"] = sorted_high[j]["extroversion_index"]
                a_dict["nervousness_index"] = sorted_high[j]["nervousness_index"]
                a_dict["openn_index"] = sorted_high[j]["openn_index"]
                a_dict["agreeableness_index"] = sorted_high[j]["agreeableness_index"]
                a_dict["conscientiousness_index"] = sorted_high[j]["conscientiousness_index"]

                # query_body = {"query":{"bool":{"must":[{"term":{"uid":sorted_high[j]["uid"]}}]}}}
                # photo_url = es.search(index=USER_INFORMATION,doc_type="text",body = query_body)["hits"]["hits"][0]["_source"]["photo_url"]

                # a_dict["photo_url"] = photo_url

                a_dict[i] = sorted_high[j][i]

                high_index_list.append(a_dict)


            for m in range(len(sorted_low)):
                a_dict = dict()
                a_dict["name"] = sorted_low[m]["group_name"]
                a_dict["id"] = sorted_low[m]["group_id"]
                a_dict["extroversion_index"] = sorted_low[m]["extroversion_index"]
                a_dict["nervousness_index"] = sorted_low[m]["nervousness_index"]
                a_dict["openn_index"] = sorted_low[m]["openn_index"]
                a_dict["agreeableness_index"] = sorted_low[m]["agreeableness_index"]
                a_dict["conscientiousness_index"] = sorted_low[m]["conscientiousness_index"]

                # query_body = {"query":{"bool":{"must":[{"term":{"uid":sorted_low[m]["uid"]}}]}}}
                # photo_url = es.search(index=USER_INFORMATION,doc_type="text",body = query_body)["hits"]["hits"][0]["_source"]["photo_url"]

                # a_dict["photo_url"] = photo_url

                a_dict[i] = sorted_low[m][i]
                low_index_list.append(a_dict)

            final_high_dict[i] = high_index_list
            final_low_dict[i] = low_index_list

        result_dict = dict()
        result_dict["high"] = final_high_dict
        result_dict["low"] = final_low_dict

        return result_dict


def read_files(direction='.'):
    file_list = []
    for file_path, dirs, fs in os.walk(direction):
        for f in fs:
            if file_path == '.' or file_path == '.\\.idea' or file_path == '.\\.ipynb_checkpoints':
                continue
            file_list.append(os.path.join(file_path, f))
            pass
    return file_list


def image_arrange(group_id):
    # query = {"query": {"bool": {"must": [{"term": {"group_id": group_id}}]}}}
    # user_list = es.search(index='group_information', doc_type='text', body=query)['hits']['hits'][0]['_source']['userlist'][0:9]
    # image_names = []
    # for uid in user_list:
    #     image_names.append(uid + '.jpg')

    IMAGES_PATH = 'head_images/'  # 图片集地址
    IMAGE_SIZE = 256  # 每张小图片的大小
    IMAGE_SAVE_PATH = 'head_images/' + group_id + '.jpg'  # 图片转换后的地址
    # # image_names = [image.split('\\')[-1] for image in read_files(IMAGES_PATH)]

    # # 简单的对于参数的设定和实际图片集的大小进行数量判断
    # if len(image_names) == 1:
    #     IMAGE_ROW = 1  # 图片间隔，也就是合并成一张图后，一共有几行
    #     IMAGE_COLUMN = 1  # 图片间隔，也就是合并成一张图后，一共有几列
    # elif len(image_names) == 2:
    #     IMAGE_ROW = 1
    #     IMAGE_COLUMN = 1
    #     image_names = image_names[0:1]
    # elif len(image_names) == 3:
    #     IMAGE_ROW = 1
    #     IMAGE_COLUMN = 1
    #     image_names = image_names[0:1]
    # elif len(image_names) == 4:
    #     IMAGE_ROW = 2
    #     IMAGE_COLUMN = 2
    # elif len(image_names) == 5:
    #     IMAGE_ROW = 2
    #     IMAGE_COLUMN = 2
    #     image_names = image_names[0:4]
    # elif len(image_names) == 6:
    #     IMAGE_ROW = 2
    #     IMAGE_COLUMN = 2
    #     image_names = image_names[0:4]
    # elif len(image_names) == 7:
    #     IMAGE_ROW = 2
    #     IMAGE_COLUMN = 2
    #     image_names = image_names[0:4]
    # elif len(image_names) == 8:
    #     IMAGE_ROW = 2
    #     IMAGE_COLUMN = 2
    #     image_names = image_names[0:4]
    # else:
    #     IMAGE_ROW = 3
    #     IMAGE_COLUMN = 3
    #     image_names = image_names[0:9]
    IMAGE_ROW = 3
    IMAGE_COLUMN = 3
    image_names = random.sample(paths('head_images'),9)
    to_image = Image.new('RGB', (IMAGE_COLUMN * IMAGE_SIZE, IMAGE_ROW * IMAGE_SIZE))  # 创建一个新图
    # 循环遍历，把每张图片按顺序粘贴到对应位置上
    for y in range(1, IMAGE_ROW + 1):
        for x in range(1, IMAGE_COLUMN + 1):
            # print(IMAGES_PATH + image_names[IMAGE_COLUMN * (y - 1) + x - 1])
            from_image = Image.open(image_names[IMAGE_COLUMN * (y - 1) + x - 1]).resize(
                (IMAGE_SIZE, IMAGE_SIZE), Image.ANTIALIAS)
            to_image.paste(from_image, ((x - 1) * IMAGE_SIZE, (y - 1) * IMAGE_SIZE))
    to_image.save(IMAGE_SAVE_PATH)  # 保存新图


def paths(path):
    path_collection=[]
    for dirpath,dirnames,filenames in os.walk(path):
        for file in filenames:
            if file.endswith('jpg') and '_' not in file:
                fullpath=os.path.join(dirpath,file)
                path_collection.append(fullpath)
    return path_collection