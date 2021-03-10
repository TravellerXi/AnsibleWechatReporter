#!/usr/bin/env python3
# coding:utf-8
from flask import Flask, request, json
import requests
import re, time
from datetime import datetime, timedelta
app = Flask(__name__)

#################################
# 定义企业微信区域
CorpID = ""
CorpSecret = ""
proxy = {'http': "", 'https': ""}
#proxy = {'http': None, 'https': None}
AgentID = 0

#################################

def SendMarkDownToApp(UserId, Content:list):
    """
    UserID:str
    Content:str
    发送更新卡片，Markdown语言支持
    """
    GetResponse = requests.get(
        "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=" + CorpID + "&corpsecret=" + CorpSecret,
        proxies=proxy).json()
    access_token = (GetResponse['access_token'])

    rawdata = {
        "touser": UserId,
        "msgtype": "markdown",
        "agentid": AgentID,
        "markdown": {
            "content": Content
        },
        "enable_duplicate_check": 0,
        "duplicate_check_interval": 1800
    }

    post_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + access_token
    requests.post(post_url, json.dumps(rawdata), proxies=proxy)
    return 0

class GenerateContent:
    def GenerateFinishTime(Time):
        if Time is None:
            TimeStamp = "进行中..."
        else:
            TimeStamp_tmp = datetime.strptime(str(Time).replace("+00:00", ""), "%Y-%m-%dT%H:%M:%S.%f")
            TimeStamp_tmp = TimeStamp_tmp + timedelta(hours=8)
            TimeStamp = TimeStamp_tmp.strftime("%Y-%m-%d %H:%M:%S")
        return TimeStamp
    def GenerateStartTime(Time,CurrentTime):
        if Time is None:
            TimeStamp = CurrentTime
        else:
            TimeStamp_tmp = datetime.strptime(str(Time).replace("+00:00", ""), "%Y-%m-%dT%H:%M:%S.%f")
            TimeStamp_tmp = TimeStamp_tmp + timedelta(hours=8)
            TimeStamp = TimeStamp_tmp.strftime("%Y-%m-%d %H:%M:%S")
        return TimeStamp

    def GenerateTitle(Contents):
        if Contents["status"] == "running":
            title = "正在开启: '" + Contents["name"] + "'"
        elif Contents["status"] == "success":
            title = "开启成功: '" + Contents["name"] + "'"
        elif Contents["status"] == "failed":
            title = "开启失败: '" + Contents["name"] + "'"
        return title
    def GenerateDetails(Contents):
        Details=Contents["body"]
        Keywords={
            "\n":"\n >",
            "Workflow job summary:":"",
            "spawns job #":"子任务ID: ",
            "which finished with status failed":"该任务执行失败",
        }
        for key in Keywords:
            Details = re.sub(key, Keywords[key], Details)
        pattern=re.compile(r"node #\d+") #去除 类似 node #199
        Details=re.sub(pattern,'',Details,count=0)
        if Details.find("spawns no job")>-1:
            return "任务准备启动中"
        return Details
    def GenerateStatus(Status):
        Keywords = {
            "running": "运行中",
            "success": "成功",
            "failed": "失败"
        }
        for key in Keywords:
            if Status==key:
                Staus = re.sub(key, Keywords[key], Status)
        return Staus

    def GenerateWechatContent(Contents,CurrentTime):
        if Contents["status"]=="failed":
            FontClor="warning"
        else:
            FontClor="info"
        Content = """<font color='"""+FontClor+"""'>""" + GenerateContent.GenerateTitle(Contents) + """</font>
>开始时间：""" + GenerateContent.GenerateStartTime(Contents["started"],CurrentTime=CurrentTime) + """
>完成时间：""" + GenerateContent.GenerateFinishTime(Contents["finished"]) + """
>详细链接：""" + Contents["url"] + """
>创建者：""" + Contents["created_by"] + """
>任务状态：<font color='"""+FontClor+"""'>""" + GenerateContent.GenerateStatus(Contents["status"]) + """</font>
>详情：""" + GenerateContent.GenerateDetails(Contents)
        return Content

    def GenerateMsg(Contents,CurrentTime):
        Content="""【运维自动化】"""+GenerateContent.GenerateTitle(Contents)+', '+\
                "开始时间:"+GenerateContent.GenerateStartTime(Contents["started"],CurrentTime=CurrentTime)+', '+"完成时间:"+GenerateContent.GenerateFinishTime(Contents["finished"])+', '\
                +"创建者: "+Contents["created_by"]+', '+\
            "任务状态:"+GenerateContent.GenerateStatus(Contents["status"])+', '+"详情: "+GenerateContent.GenerateDetails(Contents)
        Keywords = {
            '"': '',
            ">": "",
            "\n": "",
            "\r":""
        }
        for key in Keywords:
            Content = re.sub(key, Keywords[key], Content)
        return Content




@app.route('/', methods=['POST'])
def basic_get():
    CurrentTime=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    WechatSenders=str(request.headers.get("wechatid")).split(",")
    Contents= (json.loads(request.data))
    print(WechatSenders,Contents)

    for WeSender in WechatSenders:
        SendMarkDownToApp(WeSender,GenerateContent.GenerateWechatContent(Contents,CurrentTime))
    print(GenerateContent.GenerateMsg(Contents,CurrentTime))
    return ""

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10086)
