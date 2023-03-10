# ██╗  ██╗██████╗ ███╗   ███╗███████╗ █████╗ ██╗
# ██║  ██║██╔══██╗████╗ ████║██╔════╝██╔══██╗██║
# ███████║██║  ██║██╔████╔██║█████╗  ███████║██║
# ██╔══██║██║  ██║██║╚██╔╝██║██╔══╝  ██╔══██║██║
# ██║  ██║██████╔╝██║ ╚═╝ ██║███████╗██║  ██║███████╗
# ╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝
# Copyright 2019, Hyungyo Seo
# modules/scheduleParser.py - NEIS 서버에 접속하여 학사일정을 파싱해오는 스크립트입니다.

import json
import urllib.request
from bs4 import BeautifulSoup
from modules import log


# 학교코드와 학교종류를 정확히 입력
school_code = "J100005775"
school_kind = 3  # 1 유치원, 2 초등학교, 3 중학교, 4 고등학교

def parse(year, month, req_id, debugging):

    log.info("[#%s] parse@modules/scheduleParser.py: Started Parsing Schedule(%s-%s)" % (req_id, year, month))

    # 학년도 기준, 다음해 2월까지 전년도로 조회
    if month < 3:
        school_year = year - 1
    else:
        school_year = year

    try:
        url = ("http://stu.goe.go.kr/sts_sci_sf01_001.do?"
               "schulCode=%s"
               "&schulCrseScCode=%s"
               "&schulKndScCode=%s"
               "&ay=%s&mm=%s"
               % (school_code, school_kind, str(school_kind).zfill(2), str(school_year).zfill(4), str(month).zfill(2)))
        req = urllib.request.urlopen(url)

    except Exception as error:
        if debugging:
            print(error)
        return error

    if debugging:
        print(url)

    data = BeautifulSoup(req, 'html.parser')
    data = data.find_all('div', class_='textL')

    calendar = dict()

    # 일정 후처리(잡정보들 삭제)
    def pstpr(cal):
        return cal.replace("토요휴업일", "").strip().replace('\n\n\n', '\n')

    for i in range(len(data)):
        string = data[i].get_text().strip()
        if string[2:].replace('\n', '') and pstpr(string[2:]):
            calendar[int(string[:2])] = pstpr(string[2:])

    if debugging:
        print(calendar)

    if calendar:
        with open('data/cache/Cal-%s-%s.json' % (year, month), 'w',
                  encoding="utf-8") as make_file:
            json.dump(calendar, make_file, ensure_ascii=False, indent="\t")
            print("File Created")

    log.info("[#%s] parse@modules/scheduleParser.py: Succeeded(%s-%s)" % (req_id, year, month))

    return 0

# 디버그
if __name__ == "__main__":
    log.init()
    parse(2019, 8, "****DEBUG****", True)
