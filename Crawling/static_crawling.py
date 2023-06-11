import collections
from bs4 import BeautifulSoup
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from selenium.common.exceptions import TimeoutException,NoSuchElementException, WebDriverException
from selenium import webdriver
import time
import json
urllib3.disable_warnings(InsecureRequestWarning)

# 딕셔너리를 JSON 포맷 파일로 작성
def to_json(crawl_dict):
    with open('sogang.json', 'w', encoding='utf-8') as file :
        json.dump(crawl_dict, file, ensure_ascii=False, indent='\t')
    return


# 서강대학교 홈페이지 BASE URL
base_url = "https://www.sogang.ac.kr"
# 크롤링할 selenium의 webdriver
driver = webdriver.Chrome()

# 웹 페이지 로드
driver.get("https://www.sogang.ac.kr/sitemap.html")
# 동적으로 생성되는 콘텐츠가 로드될 때까지 대기
driver.implicitly_wait(5)
html = driver.page_source

soup = BeautifulSoup(html, 'html.parser')
# a 태그를 모두 추출해서 links 리스트에 저장
links = soup.select('a')
result = collections.defaultdict()
urls = set()

for i in links:
    ref = i.get('href')
    if not ref:
        continue
    print(ref)
    if ref in urls:
        continue
    time.sleep(1)
    if ref[0:4] == 'http':
        # 서강대학교 홈페이지 외부의 링크의 경우 스킵
        # ex : "http://cs.sogang.ac.kr/"
        continue
    try:
        # a 태그에 걸린 링크 추출해서 새롭게 탐색할 페이지 만들기
        new_url = base_url + ref
        driver.get(new_url)
        driver.implicitly_wait(1)
        html = driver.page_source
        urls.add(ref)
        soup = BeautifulSoup(html, 'html.parser')

        # main class (본문) 하위 모든 text 추출
        contents = soup.select('.main')
        # title 추출
        title = soup.select_one('#sub_page_title')
        if not title:
            # 없을 경우 (ex. 메인페이지 ("/"))
            title_text = ""
        else:
            title_text = title.get_text()

        iframes = soup.select('#mainFrm')
        if len(iframes):
            # 동적페이지이므로 넘어감
            continue

        new_links = soup.select('div.row>a')
        print()
        print("===newlinks====")
        for added_link in new_links:
            print(added_link.get('href'))
        print("==============")
        links += new_links
        fetched_content = ""
        for t in contents:
            fetched_content += t.get_text()
        result[new_url] = [{"title": title_text, "contents": fetched_content}]
    except (TimeoutException, WebDriverException, NoSuchElementException) as e:
        print("An exception occurred: ", str(e))
    #links += new_links

# 브라우저 종료
driver.quit()
to_json(result)