from flask import Flask
import requests
from PIL import Image, ImageSequence
import numpy as np
import matplotlib.pyplot as plt
from wordcloud import WordCloud, ImageColorGenerator
import jieba.analyse
from html2text import html2text
from time import sleep
from collections import OrderedDict
from flask import render_template, request
import PySide2

# 创建一个Flask应用
app = Flask(__name__)


#用户信息
def get_user_info(uid):
    result = requests.get('https://m.weibo.cn/api/container/getIndex?type=uid&value={}'.format(uid))
    json_data = result.json()

    if json_data['ok'] == 1:
        userInfo=OrderedDict()
        userInfo = {
            #'user_id': json_data['data']['userInfo']['id'],
            'screen_name': json_data['data']['userInfo']['screen_name'],
            'profile_image_url': json_data['data']['userInfo']['profile_image_url'],
            # 'gender':(json_data['data']['userInfo']['gender']=='f'?'女':'男'),
            'followers_count': json_data['data']['userInfo']['followers_count'],
            'follow_count': json_data['data']['userInfo']['follow_count'],
            'verified': json_data['data']['userInfo']['verified'],
            # 'verified_reason':(verified?json_data['data']['userInfo']['verified_reason']:'')
            #'containerid': json_data['data']['tabsInfo']['tabs'][1]['containerid']  # 此字段在获取博文中需要
        }
        if json_data['data']['userInfo']['gender'] == 'f':
            gender = '女'
        elif json_data['data']['userInfo']['gender'] == 'm':
            gender = '男'
        else:
            gender='未知'

        if userInfo['verified']:
            verified_reason = json_data['data']['userInfo']['verified_reason']
        else:
            verified_reason = ''
        userInfo['gender'] = gender
        userInfo['verified_reason'] = verified_reason

        data={
            'uid':json_data['data']['userInfo']['id'],
            'containerid':json_data['data']['tabsInfo']['tabs'][1]['containerid'],
            'userInfo':'<br>'.join(['{}:{}'.format(k,v) for k,v in userInfo.items()])
        }
        return data

#爬取微博
def get_all_posts(uid,containerid):
    page=0
    posts=[]
    while page<20:
        result=requests.get('https://m.weibo.cn/api/container/getIndex?type=uid&value={}&containerid={}&page={}'
                              .format(str(uid), str(containerid), str(page)))
        json_data=result.json()
        # 当博文获取完毕，退出循环
        if not json_data['data']['cards']:
            break
        #print(json_data['data']['cards'][0]['mblog']['text'])
        for x in json_data['data']['cards']:
            if x['card_type']==9:               #不是所有的元素都有mblog键,只有card_type==9的有, 不加上判断条件会报错
                posts.append(x['mblog']['text'])
        #for x in json_data['data']['cards']:
        #    posts.append(x['mblog']['text'])
        page+=1
        sleep(0.5)
    return posts

#生成云图
def wordcloud(uid,posts):
    content = ' '.join([html2text(x) for x in posts])
    result = jieba.analyse.textrank(content, topK=1000, withWeight=True)
    keyword = {}
    for x in result:
        keyword[x[0]] = x[1]
    alice_mask = np.array(Image.open('alice_color.png'))
    # f=open('stopwords.txt','r')
    # stopword=
    # stopwords暂时没有实现
    wc = WordCloud(font_path='simhei.ttf', background_color="white", max_words=2000, mask=alice_mask, max_font_size=100,
                   random_state=42)
    wc.generate_from_frequencies(keyword)
    image_colors = ImageColorGenerator(alice_mask)
    # 显示图片
    plt.imshow(wc)
    plt.imshow(wc.recolor(color_func=image_colors))
    plt.axis("off")  # 关闭图像坐标系
    #plt.show()
    plt.savefig('{}.png'.format(uid))
    return '{}.png'.format(uid)

#定义路由, 指定根路径请求的响应函数
@app.route('/',methods=['GET','POST'])
def index():
    #初始化为空
    userInfo={}
    # 如果是一个Post请求,并且有微博用户id,则获取微博数据并生成相应云图
    # request.method的值为请求方法
    # request.form既为提交的表单
    if request.method=='POST' and request.form.get('uid'):
        uid=request.form.get('uid')
        userInfo=get_user_info(uid)
        posts=get_all_posts(uid,userInfo['containerid'])
        dest_img=wordcloud(uid,posts)
        userInfo['personas']=dest_img
    return render_template('index.html',**userInfo)

if __name__=='__main__':
    app.run()
