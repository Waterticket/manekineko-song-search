from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium import webdriver
import pyperclip
import time
from bs4 import BeautifulSoup
from urllib import parse

joysound_browser = webdriver.Chrome()

joysound_browser.get('https://www.joysound.com') # referer
joysound_browser.get('https://www.joysound.com/web/search/song/757342') # cache

tj_browser = webdriver.Chrome()
tj_browser.get('https://www.tjmedia.com/tjsong/song_search.asp') # reverer

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/search/joysound/{search_keyword}")
def get_items(search_keyword: str):
    joysound_browser.get('https://www.joysound.com/web/search/cross?match=1&keyword=' + parse.quote(search_keyword))
    time.sleep(0.5)

    html = joysound_browser.page_source
    soupCB = BeautifulSoup(html, 'html.parser')
    board = soupCB.select('div.jp-cmp-music-list-song-001')[0]
    items = board.select('a.jp-cmp-table-column')
    count = len(items)

    song_info = []

    for item in items:
        if_available_in_home = False
        url = item["href"]
        song_name = item.select('h3.jp-cmp-music-title-001')[0].text.strip()
        tags = item.select('div.jp-cmp-list-inline-003 li.ng-scope')
        song_number = 0
        for tag in tags:
            tag_title = tag.select('span')[0].text.strip()
            if tag_title == '家庭用カラオケ':
                if_available_in_home = True
                break

        if if_available_in_home:
            joysound_browser.get('https://www.joysound.com/web/' + url)
            html = joysound_browser.page_source
            soupCB = BeautifulSoup(html, 'html.parser')

            detail = soupCB.select('section#jp-cmp-karaoke-household div.jp-cmp-karaoke-details')[0]
            song_number = detail.select('div.jp-cmp-movie-status-001 > dl')[0].select('dt')[0].find_next_sibling("dd").text.strip()
            song_number = int(song_number)

        song_info.append({
            "song_name": song_name,
            "song_number": song_number,
            "available_in_home": if_available_in_home,
            "url": url
        })

    return {
        "keyword": search_keyword,
        "song_list": song_info,
        "count": count,
    }

@app.get("/search/tj/{search_keyword}")
def get_items_tj(search_keyword: str):
    tj_browser.get('https://www.tjmedia.com/tjsong/song_search.asp')

    # 1. 국가 선택
    select_element = tj_browser.find_element_by_class_name('searchSelectSongForm1')
    select_object = Select(select_element)
    select_object.select_by_value("JPN")

    # 2. 곡제목 선택
    select_element = tj_browser.find_element_by_class_name('searchSelectSongForm2')
    select_object = Select(select_element)
    select_object.select_by_value("1")

    # 3. 검색어 입력
    queryInput = tj_browser.find_element_by_class_name('search_input2')
    queryInput.click()
    pyperclip.copy(search_keyword)
    queryInput.send_keys(Keys.CONTROL, 'v')

    # 4. 검색
    queryInput.send_keys(Keys.ENTER)
    time.sleep(1)

    # 5. 파싱
    html = tj_browser.page_source
    soupCB = BeautifulSoup(html, 'html.parser')
    time.sleep(1)

    table = soupCB.select('table.board_type1 > tbody')[0]
    items = table.select('tr')

    song_info = []

    for item in items:
        if len(item.select('td')) <= 3:
            continue

        tds = item.select('td')
        song_name = item.select('td.left')[0].text.strip()
        song_number = int(tds[0].text.strip())
        singer = tds[2].text.strip()

        song_info.append({
            "song_name": song_name,
            "song_number": song_number,
            "singer": singer,
        })

    return {
        "keyword": search_keyword,
        "song_list": song_info,
        "count": len(song_info),
    }
