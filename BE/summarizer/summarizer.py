#!/usr/bin/env python3
#-*- codig: utf-8 -*-
import sys
import requests
import json

class Summarizer:
    def __init__(self):
        self.client_id = ""
        self.client_secret = ""
        self.headers = {
            "X-NCP-APIGW-API-KEY-ID": self.client_id,
            "X-NCP-APIGW-API-KEY": self.client_secret,
            "Content-Type": "application/json"
        }
        self.language = "ko" # Language of document (ko, ja )
        self.model = "news" # Model used for summaries (general, news)
        self.tone = "0" # Converts the tone of the summarized result. (0, 1, 2, 3)
        self.summaryCount = "5" # This is the number of sentences for the summarized document.
        self.url= "https://naveropenapi.apigw.ntruss.com/text-summary/v1/summarize" 

    def summarize(self, title, content):
        self.title= title
        self.content = content
        self.data = {
            "document": {
                "title": self.title,
                "content" : self.content
            },
            "option": {
                "language": self.language,
                "model": self.model,
                "tone": self.tone,
                "summaryCount" : self.summaryCount
            }
        }

        # print(json.dumps(self.data, indent=4, sort_keys=True))
        response = requests.post(self.url, data=json.dumps(self.data), headers=self.headers)
        rescode = response.status_code
        if(rescode == 200):
            return response.json()['summary']
        else:
            return "Error"

if __name__ == "__main__":
    clova = Summarizer()
    title= "'하루 2000억' 판 커지는 간편송금 시장"
    content = "간편송금 이용금액이 하루 평균 2000억원을 넘어섰다. 한국은행이 17일 발표한 '2019년 상반기중 전자지급서비스 이용 현황'에 따르면 올해 상반기 간편송금서비스 이용금액(일평균)은 지난해 하반기 대비 60.7% 증가한 2005억원으로 집계됐다. 같은 기간 이용건수(일평균)는 34.8% 늘어난 218만건이었다. 간편 송금 시장에는 선불전자지급서비스를 제공하는 전자금융업자와 금융기관 등이 참여하고 있다. 이용금액은 전자금융업자가 하루평균 1879억원, 금융기관이 126억원이었다. 한은은 카카오페이, 토스 등 간편송금 서비스를 제공하는 업체 간 경쟁이 심화되면서 이용규모가 크게 확대됐다고 분석했다. 국회 정무위원회 소속 바른미래당 유의동 의원에 따르면 카카오페이, 토스 등 선불전자지급서비스 제공업체는 지난해 마케팅 비용으로 1000억원 이상을 지출했다. 마케팅 비용 지출규모는 카카오페이가 491억원, 비바리퍼블리카(토스)가 134억원 등 순으로 많았다."
    doc_summarized = clova.summarize(title, content)
    print(doc_summarized)
