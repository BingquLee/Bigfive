import sys
sys.path.append('../../../')

from config import *
from time_utils import *

#计算群组的重要度、活跃度、敏感度、影响力与紧密度，利用群组内用户对应指标在全库中排名的均值计算
#输入：群组id
#输出：将该群组的五项属性以分数与星级的形式存入数据库
def group_attribute(group_id, uid_list, date):
    date_ts = date2ts(date)
    iter_count = 0
    group_all_user_count = len(uid_list)
    importance_list = []
    influence_list = []
    activeness_list = []
    sensitivity_list = []
    while iter_count < group_all_user_count:   #一下获取多个用户以减少查询次数
        print('iter_num: %d' % iter_count)
        iter_uid_list = uid_list[iter_count: iter_count + GROUP_ITER_COUNT]
        iter_uid_list = [uid + '_' + str(date_ts) for uid in iter_uid_list]
        try:
            iter_user_dict_list = es.mget(index=USER_INFLUENCE, doc_type='text', body={'ids':iter_uid_list})['docs']
        except:
            iter_user_dict_list = []

        #利用用户对应属性在全体用户中的排名计算群体的这些属性
        for user_dict in iter_user_dict_list:
            uid = user_dict['_id']
            if user_dict['found'] == False:
                continue
            source = user_dict['_source']
            #影响力
            influence = source['influence']
            influence_rank = get_index_rank(influence, 'influence', date_ts)
            influence_list.append(influence_rank) 
            #重要度
            importance = source['importance']
            importance_rank = get_index_rank(importance, 'importance', date_ts)
            importance_list.append(importance_rank)
            #活跃度
            activeness = source['activity']
            activeness_rank = get_index_rank(activeness, 'activity', date_ts)
            activeness_list.append(activeness_rank)
            #敏感度
            sensitivity = source['sensitivity']
            sensitivity_rank = get_index_rank(sensitivity, 'sensitivity', date_ts)
            sensitivity_list.append(sensitivity_rank)
            # print(uid,importance,influence,activeness)
            # print(uid,importance_rank,influence_rank,activeness_rank)

        iter_count += GROUP_ITER_COUNT

    # print(importance_list,influence_list,activeness_list)
    #计算属性排名的平均值
    try:
        all_user_count = es.count(index=USER_INFLUENCE, doc_type='text', body={'query':{'term':{'timestamp':date_ts}}})['count']
    except Exception as e:
        raise e
    #活跃度
    ave_activeness_rank = float(sum(activeness_list)) / len(activeness_list)
    activity = (all_user_count - ave_activeness_rank) / all_user_count * 100
    if ave_activeness_rank <= GROUP_AVE_ACTIVENESS_RANK_THRESHOLD[0] * all_user_count:
        activeness_star = 5
    elif ave_activeness_rank > GROUP_AVE_ACTIVENESS_RANK_THRESHOLD[1] * all_user_count:
        activeness_star = 1
    else:
        activeness_star = 3
    #影响力
    ave_influence_rank = float(sum(influence_list) / len(influence_list))
    influence = (all_user_count - ave_influence_rank) / all_user_count * 100
    if ave_influence_rank <= GROUP_AVE_INFLUENCE_RANK_THRESHOLD[0] * all_user_count:
        influence_star = 5
    elif ave_influence_rank > GROUP_AVE_INFLUENCE_RANK_THRESHOLD[1] * all_user_count:
        influence_star = 1
    else:
        influence_star = 3
    #重要度
    ave_importance_rank = float(sum(importance_list) / len(importance_list))
    importance = (all_user_count - ave_importance_rank) / all_user_count * 100
    if ave_importance_rank <= GROUP_AVE_IMPORTANCE_RANK_THRESHOLD[0] * all_user_count:
        importance_star = 5
    elif ave_importance_rank > GROUP_AVE_IMPORTANCE_RANK_THRESHOLD[1] * all_user_count:
        importance_star = 1
    else:
        importance_star = 3
    #敏感度
    ave_sensitivity_rank = float(sum(sensitivity_list) / len(sensitivity_list))
    sensitivity = (all_user_count - ave_sensitivity_rank) / all_user_count * 100
    if ave_sensitivity_rank <= GROUP_AVE_SENSITIVITY_RANK_THRESHOLD[0] * all_user_count:
        sensitivity_star = 5
    elif ave_sensitivity_rank > GROUP_AVE_SENSITIVITY_RANK_THRESHOLD[1] * all_user_count:
        sensitivity_star = 1
    else:
        sensitivity_star = 3

    density, density_star = group_density_attribute(uid_list, date, 15)

    dic = {
        'timestamp':date_ts,
        'date':date,
        'group_id':group_id,
        'activity':activity,
        'sensitivity':sensitivity,
        'influence':influence,
        'importance':importance,
        'density':density,
        'activeness_star':activeness_star,
        'influence_star':influence_star,
        'importance_star':importance_star,
        'sensitivity_star':sensitivity_star,
        'density_star':density_star
    }

    es.index(index=GROUP_INFLUENCE,doc_type='text',id=group_id + '_' + str(date_ts),body=dic)

    # return activity, influence, importance, sensitivity, activeness_star, influence_star, importance_star, sensitivity_star

def group_attribute_long(group_id, uid_list, start_date, end_date):
    for day in get_datelist_v2(start_date, end_date):
        print(day)
        try:
            group_attribute(group_id,uid_list,day)
        except:
            pass

###获得对应的数值在用户列表中的排名
def get_index_rank(attr_value, attr_name, timestamp):
    result = 0
    query_body = {
        'query':{
            'bool':{
                'must':[
                    {'term':{'timestamp':timestamp}},
                    {'range':{
                        attr_name:{
                            'from':attr_value,
                            'to': MAX_VALUE
                            }
                        }
                    }
                ]
            }
        }
    }
    index_rank = es.count(index=USER_INFLUENCE, doc_type='text', body=query_body)
    if index_rank['_shards']['successful'] != 0:
       result = index_rank['count']
    else:
        print('es index rank error')
        result = 0
    return result

#计算群组的紧密性，根据转发评论用户之间的边计算
#输入：群组id
#输出：紧密性、紧密性星级
def group_density_attribute(uid_list, date, days):
    date_end_ts = date2ts(date)
    date_start_ts = date_end_ts - 24*3600*days
    iter_count = 0
    group_all_user_count = len(uid_list)
    all_in_record = []
    for uid in uid_list:
        query_body = {
            'query':{
                'filtered':{
                    'filter':{
                        'bool':{
                            'must':[
                                {'term':{'target':uid}},
                                {"range":{
                                    "timestamp":{
                                        "gt":date_start_ts,
                                        "lte":date_end_ts
                                    }
                                }}
                            ]
                        }
                        
                    }
                }
            },
            'size':10000
        }

        res = es.search(index=USER_SOCIAL_CONTACT, doc_type='text', body=query_body)['hits']['hits']
        #取出来的为用户在一段时间内的转发与评论的数量
        user_retweet_result = {}    #{ruid1:count1, ruid2:count2}
        user_comment_result = {}
        for hit in res:
            source_uid = hit['_source']['source']
            target_uid = hit['_source']['target']
            message_type = hit['_source']['message_type']
            if message_type == 2:
                try:
                    user_comment_result[source_uid] += 1
                except:
                    user_comment_result[source_uid] = 1
            if message_type == 3:
                try:
                    user_retweet_result[source_uid] += 1
                except:
                    user_retweet_result[source_uid] = 1

        filter_in_dict = filter_union_dict([user_retweet_result, user_comment_result], uid_list, 'in')
        uid_in_record = [[uid, ruid, filter_in_dict[ruid]] for ruid in filter_in_dict if uid != ruid]
        all_in_record.extend(uid_in_record)   #[[uid1, ruid1,count1],[uid1,ruid2,count2],[uid2,ruid2,count3],...]

    in_inter_edge_count = len(all_in_record)
    in_density = float(in_inter_edge_count) / (len(uid_list) * (len(uid_list) - 1))
    #紧密度
    if in_density <= GROUP_DENSITY_THRESHOLD[0]:
        density_star = 1
    elif in_density > GROUP_DENSITY_THRESHOLD[1]:
        density_star = 5
    else:
        density_star = 3
    in_density = in_density * 100
    return in_density, density_star

#输入转发与评论列表，利用输入的过滤用户列表进行合并与筛选
def filter_union_dict(objs, filter_uid_list, mark):
    _keys = set(sum([list(obj.keys()) for obj in objs], []))   #合并uid并去重
    if mark == 'in&out':
        _in_total = {}
        _in_keys = _keys & set(filter_uid_list)
        for _key in _in_keys:
            _in_total[_key] = sum([int(obj.get(_key,0)) for obj in objs])   #计算转发评论总和
        _out_total = {} 
        _out_keys = _keys - set(filter_uid_list)
        for _key in _out_keys:
            _out_total[_key] = sum([int(obj.get(_key, 0)) for obj in objs])       
        return _in_total, _out_total
    elif mark == 'out':
        _out_total = {}
        _out_keys = _keys - set(filter_uid_list)
        for _key in _out_keys:
            _out_total[_key] = sum([int(obj.get(_key, 0)) for obj in objs])
        return _out_total
    elif mark == 'in':
        _in_total = {}
        _in_keys = _keys & set(filter_uid_list)
        for _key in _in_keys:
            _in_total[_key] = sum([int(obj.get(_key,0)) for obj in objs])
        return _in_total

if __name__=='__main__':
    # group_activity('minggelihai_1551358645','2016-11-21',15)
    # print(group_attribute(es.get(index='group_information',doc_type='text',id='ceshiyi_1542556800')['_source']['userlist'],'2016-11-19')) 
    # print(group_density_attribute(es.get(index='group_information',doc_type='text',id='bingquqiangda_1551420830')['_source']['userlist'],'2016-11-27',15))
    es.delete(index='group_activity',doc_type='text',id='ceshiyi_1542556800_1480176000')
    #minggelihai_1551418489  bingquqiangda_1551420830  xiaoleiniubi_1551418799