# -*- coding: utf-8 -*-

from flask import Blueprint,request,jsonify,Response

import json
import os
import traceback

from bigfive.firstpage.utils import *

mod = Blueprint('firstpage',__name__,url_prefix='/firstpage')


@mod.route('/test')
def test():
    result = 'This is firstpage!'
    return json.dumps(result,ensure_ascii=False)


@mod.route('/search', methods=['POST'])
def search():
    parameters = request.form.to_dict()
    keyword = parameters.get('keyword', '').lower()

    page = parameters.get('page', '1')
    size = parameters.get('size', '6')

    order_name = parameters.get('order_name', 'group_name')
    order_type = parameters.get('order_type', 'asc')

    result = search_group(keyword, page, size, order_name, order_type)
    return json.dumps(result, ensure_ascii=False)

# @mod.route('/search/', methods=['GET', 'POST'])
# def search():
#     keyword = request.args.get('keyword', default='').lower()
#
#     page = request.args.get('page', default='1')
#     size = request.args.get('size', default='6')
#
#     person_order_name = request.args.get('person_order_name', default='username')
#     person_order_type = request.args.get('person_order_type', default='asc')
#     group_order_name = request.args.get('group_order_name', default='group_name')
#     group_order_type = request.args.get('group_order_type', default='asc')
#
#     result = search_person_and_group(keyword, page, size, person_order_name, group_order_name, person_order_type, group_order_type)
#     return json.dumps(result, ensure_ascii=False)


@mod.route('/statistics_user_info', methods=['GET', 'POST'])
def statistics_user_info():
    timestamp = request.args.get('timestamp')
    result = get_statistics_user_info(timestamp)
    return json.dumps(result, ensure_ascii=False)


@mod.route('/dark_user_info', methods=['GET', 'POST'])
def dark_user_info():

    result = dark_personality()

    return json.dumps(result, ensure_ascii=False)

@mod.route('/dark_group_info', methods=['GET', 'POST'])
def dark_group_info():

    result = dark_group()

    return json.dumps(result, ensure_ascii=False)

@mod.route('/bigfive_user_info', methods=['GET', 'POST'])
def bigfive_user_info():

    result = bigfive_personality()

    return json.dumps(result, ensure_ascii=False)

@mod.route('/bigfive_group_info', methods=['GET', 'POST'])
def bigfive_group_info():

    result = bigfive_group()

    return json.dumps(result, ensure_ascii=False)


@mod.route('/head', methods=['GET', 'POST'])
def head():
    # 个人和群组头像处理
    id = request.args.get('id')
    img_path = 'head_images/' + id + '.jpg'
    mime = 'image/jpeg'
    if not os.path.exists(img_path):
        # 生成群组头像
        if '_' in id:
            try:
                image_arrange(id)
            except:
                traceback.print_exc()
                return jsonify(0)
        else:
            # print(paths('head_images'))
            img_path = random.choice(paths('head_images'))
            # return jsonify(0)
    with open(img_path,'rb') as fp:
        img = fp.read()
    return Response(img,mimetype=mime)

