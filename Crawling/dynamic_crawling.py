import json
from selenium.common.exceptions import TimeoutException,NoSuchElementException, WebDriverException
from selenium import webdriver
from bs4 import BeautifulSoup
import collections
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from urllib.request import urlopen

import numpy as np
import platform
from PIL import ImageFont, ImageDraw, Image
import uuid
import time
import requests

api_url = # API_KEY HERE
secret_key = # SECRET_KEY HERE


def to_json(crawl_dict):
    with open('sogang_notices_2.json', 'w', encoding='utf-8') as file :
        json.dump(crawl_dict, file, ensure_ascii=False, indent='\t')
    return

def put_text(image, text, x, y, color=(0, 255, 0), font_size=22):
    if type(image) == np.ndarray:
        color_coverted = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(color_coverted)

    if platform.system() == 'Darwin':
        font = 'AppleGothic.ttf'
    elif platform.system() == 'Windows':
        font = 'malgun.ttf'

    image_font = ImageFont.truetype(font, font_size)
    font = ImageFont.load_default()
    draw = ImageDraw.Draw(image)

    draw.text((x, y), text, font=image_font, fill=color)

    numpy_image = np.array(image)
    opencv_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)

    return opencv_image

def OCR_img(imgNo):
    print("here")
    result_text = ""
    path = './img/' + str(imgNo) + '.jpg'
    files = [('file', open(path, 'rb'))]

    request_json = {'images': [{'format': 'png',
                                'name': 'demo'
                                }],
                    'requestId': str(uuid.uuid4()),
                    'version': 'V2',
                    'timestamp': int(round(time.time() * 1000))
                    }

    payload = {'message': json.dumps(request_json).encode('UTF-8')}

    headers = {
        'X-OCR-SECRET': secret_key,
    }

    response = requests.request("POST", api_url, headers=headers, data=payload, files=files)
    #result = response.json()
    res = json.loads(response.text)

    for dic in res['images'][0]['fields']:
        print(dic['inferText'], end=' ')
        if dic['lineBreak'] is True:
            result_text += "  "

    #img = cv2.imread(path)
    #roi_img = img.copy()
    return result_text


driver = webdriver.Chrome()
cur_page = 1
bbs_nums = [1, 2, 3, 25, 53, 55, 58, 104, 108, 141, 142, 143, 170]

notices_list = []
sogang = 'https://www.sogang.ac.kr'

for bbs_num in bbs_nums:
    for cur_page in range(2,3):
        main_base = sogang + '/front/boardlist.do?bbsConfigFK=' + str(bbs_num)
        '''
        try:
            driver.get(main_base)
            driver.implicitly_wait(5)

            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            notice_links = soup.select('.subject > a')
            for c in notice_links:
                if c.attrs['href'][0] != '/' or c.attrs['href'][0:9] == '/Download':
                    continue
                #notices_list.append(c.attrs['href'])
        except (TimeoutException, WebDriverException, NoSuchElementException) as e:
            print("An exception occurred: ", str(e))
        '''
        list_pages_base = sogang + '/front/boardlist.do?currentPage=' + str(cur_page) + '&menuGubun=1&siteGubun=1&bbsConfigFK=' + str(bbs_num) + '&searchField=ALL&searchValue=&searchLowItem=ALL'
        try:

            driver.get(list_pages_base)
            driver.implicitly_wait(5)

            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            contents = soup.select('a')
            for c in contents:
                if c.attrs['href'][0] != '/' or c.attrs['href'][0:9] == '/Download':
                    continue
                notices_list.append(c.attrs['href'])

        except (TimeoutException, WebDriverException, NoSuchElementException) as e:
            print("An exception occurred: ", str(e))
imgNo = 1
pdfNo = 1
crawled_notices = collections.defaultdict()
for link in notices_list:
    notice_url = sogang + link
    driver.get(notice_url)
    driver.implicitly_wait(20)
    sleep(0.5)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.select_one('div.subject')
    title_txt = title.get_text()
    contents = soup.select('div>p')
    embedded = soup.select_one('iframe')
    embedded_text = ""
    if embedded:
        print("here embeded")

        driver.get(embedded['src'])
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".textLayer span")))
            html2 = driver.page_source
            soup2 = BeautifulSoup(html2, 'html.parser')
            embedded_contents = soup2.select('.textLayer')
            embedded_text += " ".join(block.text for block in embedded_contents)
        except Exception as e:
            print("Unexpected error: ", e)

    images = soup.select('img')
    img_text = ""

    for i in images:
        imgURL = i['src']
        if imgURL[0] == '/':
            imgURL = sogang + imgURL
        print(imgURL)

        try:
            with urlopen(imgURL) as f:
                try:
                    with open('./img/' + str(imgNo) + '.jpg', 'wb') as h:
                        img = f.read()
                        h.write(img)
                        print("h okay")
                        img_text += OCR_img(imgNo)
                        imgNo += 1
                except Exception as e:
                    print("Could not write to file. Error: ", e)
        #except urllib.error.URLError as e:
        #    print("URL Error: ", e)
        except Exception as e:
            print("Unexpected error: ", e)

    fetched_contents = ""
    print('제목', title_txt)
    print('내용\n')
    for i in contents:
        texts = i.get_text()
        if texts.isspace():
            continue
        #print(texts)
        fetched_contents += texts
    fetched_contents += embedded_text
    fetched_contents += img_text
    print(fetched_contents)
    crawled_notices[notice_url] = [{"title": title.get_text(), "contents": fetched_contents}]

#print(notices_list)
to_json(crawled_notices)