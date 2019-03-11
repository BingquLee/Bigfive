import time
import sys
import json
sys.path.append('../')
sys.path.append('event')
sys.path.append('event/event_river')
from xpinyin import Pinyin

from config import *
from time_utils import *
from portrait.cron_portrait import user_ranking, cal_user_personality, group_create, group_ranking, cal_group_personality
from portrait.group.cron_user import user_portrait
from portrait.group.cron_group import group_portrait
from cron_event import event_create, get_text_analyze
from event_mapping import create_event_mapping

#对用户进行批量计算，流数据接入时会自动入库批量计算
def user_main(uid_list, username_list, start_date, end_date):
    print('Start calculating user personality...')
    cal_user_personality(uid_list, start_date, end_date)

    print('Start calculating user portrait...')
    for uid in uid_list:
        print(uid)
        user_portrait(uid, end_date)
    
    print('Start calculating user ranking...')
    user_ranking(uid_list, username_list, end_date)

#检测任务表，有新任务会进行计算，默认取计算时间段的结束日期为创建日期，开始日期为结束日期前的n天
def group_main(args_dict, keyword, remark, group_name, create_time):
    days = 15
    end_date = ts2date(create_time)
    start_date = ts2date(create_time - days * 24 *3600)
    print('Start finding userlist...')
    group_dic = group_create(args_dict, keyword, remark, group_name, create_time, start_date, end_date)

    print('Start calculating group personality...')
    cal_group_personality(group_dic['group_id'], group_dic['userlist'], end_date)

    print('Start calculating group portrait...')
    group_portrait(group_dic['group_id'], group_dic['userlist'], start_date, end_date)
    
    print('Start calculating group ranking...')
    group_ranking(group_dic['group_id'], group_dic['group_name'], group_dic['userlist'], end_date)


def event_main(keywords, event_id, start_date, end_date):
    print('Start creating event...')
    event_mapping_name = 'event_%s' % event_id
    create_event_mapping(event_mapping_name)
    userlist = event_create(event_mapping_name, keywords, start_date, end_date)
    es.update(index=EVENT_INFORMATION,doc_type='text',body={'doc':{'userlist':userlist}},id=event_id)

    print('Start text analyze...')
    # get_text_analyze(event_id, event_mapping_name)
    

if __name__ == '__main__':
    # user_main()
    # group_main(1,2,3,4,5)

    event_name = "测试事件三"
    event_pinyin = Pinyin().get_pinyin(event_name, '')
    create_time = 1551942139 #int(time.time())
    create_date = ts2date(create_time)
    start_date = '2016-11-13'
    end_date = '2016-11-27'
    keywords = "崛起"
    progress = 2
    event_id = event_pinyin + "_" + str(create_time)
    dic = {
        'event_name':event_name,
        'event_pinyin':event_pinyin,
        'create_time':create_time,
        'create_date':create_date,
        'keywords':keywords,
        'progress':progress,
        'event_id':event_id,
        'start_date':start_date,
        'end_date':end_date
    }
    es.index(index=EVENT_INFORMATION,doc_type='text',body=dic,id=event_id)
    time.sleep(1)
    event_main(keywords, event_id, start_date, end_date)