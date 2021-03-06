# -*- coding: UTF-8 -*-
import sys
sys.path.append('../../../')
sys.path.append('../../')
sys.path.append('../')
sys.path.append('../user/')
import datetime
from config import *
from time_utils import *
from global_utils import *
from user.user_text_analyze import cal_user_text_analyze

def weekly_user_text_analyze(date):
    date = ts2date(int(date2ts(date)) - DAY)
    print(date)
    iter_result = get_user_generator("user_information", {"query":{"bool":{"must":[{"match_all":{}}]}}}, 1000)
    while True:
        try:
            es_result = next(iter_result)
        except:
            break
        uid_list = []
        for k,v in enumerate(es_result):
            uid_list.append(es_result[k]["_source"]["uid"])

        cal_user_text_analyze(uid_list, date, date)


if __name__ == '__main__':
    # for date in get_datelist_v2('2019-03-30','2019-04-10'):
    #     weekly_user_domain(date)

    weekday = datetime.datetime.now().weekday()
    theday = today()
    if weekday == 4:
        print("Calculating user text keywords...")
        weekly_user_text_analyze(theday)
    else: 
        print("not reach calculating user text keywords time")
        pass
    # theday = today()
    # weekly_user_text_analyze(theday)