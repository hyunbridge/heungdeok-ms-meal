# ██╗  ██╗██████╗ ███╗   ███╗███████╗ █████╗ ██╗
# ██║  ██║██╔══██╗████╗ ████║██╔════╝██╔══██╗██║
# ███████║██║  ██║██╔████╔██║█████╗  ███████║██║
# ██╔══██║██║  ██║██║╚██╔╝██║██╔══╝  ██╔══██║██║
# ██║  ██║██████╔╝██║ ╚═╝ ██║███████╗██║  ██║███████╗
# ╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝
# Copyright 2019, Hyungyo Seo
# modules/skill.py - Skill 응답 데이터를 만드는 스크립트입니다.

import datetime
import json
import os
import re
import time
from itertools import groupby
from threading import Thread
import jwt
import requests
from modules import getData, cache, user, log, LoL


# Skill 응답용 JSON 생성
def skill(msg):
    return {'version': '2.0',
            'data': {
                'msg': msg
            }
            }


def skill_simpletext(msg):
    return {'version': '2.0',
            'template': {
                'outputs': [
                    {
                        'simpleText': {
                            'text': msg
                        }
                    }
                ]
            }
            }


# 요일 처리
def wday(date):
    if date.weekday() == 0:
        return "월"
    elif date.weekday() == 1:
        return "화"
    elif date.weekday() == 2:
        return "수"
    elif date.weekday() == 3:
        return "목"
    elif date.weekday() == 4:
        return "금"
    elif date.weekday() == 5:
        return "토"
    else:
        return "일"


# 식단조회 코어
def meal_core(year, month, date, wday, req_id, debugging):
    if wday >= 5:  # 주말
        return "급식을 실시하지 않습니다. (주말)"
    meal = getData.meal(year, month, date, req_id, debugging)
    if not "message" in meal:  # 파서 메시지 있는지 확인, 없으면 만들어서 응답
        return "%s:\n\n%s\n\n열량: %s kcal" % (meal["date"], meal["menu"], meal["kcal"])
    if meal["message"] == "등록된 데이터가 없습니다.":
        cal = getData.schdl(year, month, date, req_id, debugging)
        if not cal == "일정이 없습니다.":
            return "급식을 실시하지 않습니다. (%s)" % cal
    return meal["message"]


# Skill 식단 조회
def meal(reqdata, req_id, debugging):
    log.info("[#%s] meal@modules/skill.py: New Request" % req_id)
    try:
        sys_date = json.loads(json.loads(reqdata)["action"]["params"]["sys_date"])["date"]  # 날짜 가져오기
    except Exception:
        log.err("[#%s] meal@modules/skill.py: Error while Parsing Request" % req_id)
        return skill("오류가 발생했습니다.\n요청 ID: " + req_id)
    try:
        # 년월일 파싱
        year = datetime.datetime.strptime(sys_date, "%Y-%m-%d").timetuple()[0]
        month = datetime.datetime.strptime(sys_date, "%Y-%m-%d").timetuple()[1]
        date = datetime.datetime.strptime(sys_date, "%Y-%m-%d").timetuple()[2]
        wday = datetime.datetime.strptime(sys_date, "%Y-%m-%d").timetuple()[6]
    except ValueError:  # 파싱중 값오류 발생시
        log.err("[#%s] meal@modules/skill.py: ValueError while Parsing Date" % req_id)
        return skill("오류가 발생했습니다.\n요청 ID: " + req_id)
    if debugging:
        print(sys_date)
        print(year)
        print(month)
        print(date)
        print(wday)
    return skill(meal_core(year, month, date, wday, req_id, debugging))


# Skill 특정날짜(고정값) 식단 조회
def meal_specific_date(reqdata, req_id, debugging):
    log.info("[#%s] meal_specific_date@modules/skill.py: New Request" % req_id)
    try:
        specific_date = json.loads(reqdata)["action"]["params"]["date"]
    except Exception:
        log.err("[#%s] meal_specific_date@modules/skill.py: Error while Parsing Request" % req_id)
        return skill("오류가 발생했습니다.\n요청 ID: " + req_id)
    try:
        # 년월일 파싱
        year = datetime.datetime.strptime(specific_date, "%Y-%m-%d").timetuple()[0]
        month = datetime.datetime.strptime(specific_date, "%Y-%m-%d").timetuple()[1]
        date = datetime.datetime.strptime(specific_date, "%Y-%m-%d").timetuple()[2]
        wday = datetime.datetime.strptime(specific_date, "%Y-%m-%d").timetuple()[6]
    except ValueError:  # 값오류 발생시
        log.err("[#%s] meal_specific_date@modules/skill.py: ValueError while Parsing Date" % req_id)
        return skill("오류가 발생했습니다.\n요청 ID: " + req_id)
    if debugging:
        print(specific_date)
        print(year)
        print(month)
        print(date)
        print(wday)
    return skill(meal_core(year, month, date, wday, req_id, debugging))


# Skill 시간표 조회 (등록 사용자용)
def tt_registered(reqdata, req_id, debugging):
    log.info("[#%s] tt_registered@modules/skill.py: New Request" % req_id)
    try:
        uid = json.loads(reqdata)["userRequest"]["user"]["id"]
        user_data = user.get_user(uid, req_id, debugging)  # 사용자 정보 불러오기
        tt_grade = user_data[0]
        tt_class = user_data[1]
    except Exception:
        log.err("[#%s] tt_registered@modules/skill.py: Error while Parsing Request" % req_id)
        return skill("오류가 발생했습니다.\n요청 ID: " + req_id)
    if tt_grade and tt_class:  # 사용자 정보 있을 때
        try:
            sys_date = json.loads(json.loads(reqdata)["action"]["params"]["sys_date"])["date"]  # 날짜 파싱
        except Exception:
            log.err("[#%s] tt_registered@modules/skill.py: Error while Parsing Date" % req_id)
            return skill("오류가 발생했습니다.\n요청 ID: " + req_id)
        try:
            date = datetime.datetime.strptime(sys_date, "%Y-%m-%d")
        except ValueError:  # 값오류 발생시
            log.err("[#%s] tt_registered@modules/skill.py: ValueError while Parsing Date" % req_id)
            return skill("오류가 발생했습니다.\n요청 ID: " + req_id)
        if debugging:
            print(tt_grade)
            print(tt_class)
        msg = getData.tt(tt_grade, tt_class, date.year, date.month, date.day, req_id, debugging)
    else:
        log.info("[#%s] tt_registered@modules/skill.py: Non-Registered User" % req_id)
        msg = "힉년/반 정보가 없습니다.\n먼저 내 정보 등록을 해 주시기 바랍니다."
    return skill(msg)


# Skill 시간표 조회 (미등록 사용자용)
def tt(reqdata, req_id, debugging):
    log.info("[#%s] tt@modules/skill.py: New Request" % req_id)
    try:
        tt_grade = json.loads(reqdata)["action"]["params"]["Grade"]  # 학년 파싱
    except Exception:
        log.err("[#%s] tt@modules/skill.py: Error while Parsing Grade" % req_id)
        return skill("오류가 발생했습니다.\n요청 ID: " + req_id)
    try:
        tt_class = json.loads(reqdata)["action"]["params"]["Class"]  # 반 파싱
    except Exception:
        log.err("[#%s] tt@modules/skill.py: Error while Parsing Class" % req_id)
        return skill("오류가 발생했습니다.\n요청 ID: " + req_id)
    try:
        sys_date = json.loads(json.loads(reqdata)["action"]["params"]["sys_date"])["date"]  # 날짜 파싱
    except Exception:
        log.err("[#%s] tt@modules/skill.py: Error while Parsing Date" % req_id)
        return skill("오류가 발생했습니다.\n요청 ID: " + req_id)
    try:
        date = datetime.datetime.strptime(sys_date, "%Y-%m-%d")
    except ValueError:  # 값오류 발생시
        log.err("[#%s] tt@modules/skill.py: ValueError while Parsing Date" % req_id)
        return skill("오류가 발생했습니다.\n요청 ID: " + req_id)
    if debugging:
        print(tt_grade)
        print(tt_class)
    msg = getData.tt(tt_grade, tt_class, date.year, date.month, date.day, req_id, debugging)
    return skill(msg)


# Skill 학사일정 조회
def schdl(reqdata, req_id, debugging):
    global msg
    log.info("[#%s] cal@modules/skill.py: New Request" % req_id)
    try:
        data = json.loads(reqdata)["action"]["params"]
    except Exception:
        log.err("[#%s] cal@modules/skill.py: Error while Parsing Request" % req_id)
        return skill("오류가 발생했습니다.\n요청 ID: " + req_id)

    # 특정일자 조회
    if "sys_date" in data:
        try:
            date = datetime.datetime.strptime(json.loads(data["sys_date"])["date"], "%Y-%m-%d")  # 날짜 파싱
        except Exception:
            log.err("[#%s] cal@modules/skill.py: Error while Parsing Date" % req_id)
            return skill("오류가 발생했습니다.\n요청 ID: " + req_id)

        prsnt_schdl = getData.schdl(date.year, date.month, date.day, req_id, debugging)

        prsnt_schdl = prsnt_schdl
        if prsnt_schdl:
            msg = "%s-%s-%s(%s):\n%s" % (str(date.year).zfill(4), str(date.month).zfill(2), str(date.day).zfill(2),
                                         wday(date), prsnt_schdl)  # YYYY-MM-DD(Weekday)
        else:
            msg = "일정이 없습니다."
    # 특정일자 조회 끝

    # 기간 조회
    elif "sys_date_period" in data:  # 기간

        body = str()

        try:
            start = json.loads(data["sys_date_period"])["from"]["date"]  # 시작일 파싱
            start = datetime.datetime.strptime(start, "%Y-%m-%d")
        except Exception:
            log.err("[#%s] cal@modules/skill.py: Error while Parsing StartDate" % req_id)
            return skill("오류가 발생했습니다.\n요청 ID: " + req_id)
        try:
            end = json.loads(data["sys_date_period"])["to"]["date"]  # 종료일 파싱
            end = datetime.datetime.strptime(end, "%Y-%m-%d")
        except Exception:
            log.err("[#%s] cal@modules/skill.py: Error while Parsing EndDate" % req_id)
            return skill("오류가 발생했습니다.\n요청 ID: " + req_id)

        if (end - start).days > 90:  # 90일 이상을 조회요청한 경우,
            head = ("서버 성능상의 이유로 최대 90일까지만 조회가 가능합니다."
                    "\n조회기간이 %s부터 %s까지로 제한되었습니다.\n\n" %
                    (start.date(), (start + datetime.timedelta(days=90)).date()))
            end = start + datetime.timedelta(days=90)  # 종료일 앞당김
        else:
            head = "%s부터 %s까지 조회합니다.\n\n" % (start.date(), end.date())

        schdls = getData.schdl_mass(start, end, req_id, debugging)
        # 년, 월, 일, 일정 정보를 담은 튜플이 리스트로 묶여서 반환됨

        # body 쓰기, 연속되는 일정은 묶어 처리함
        for content, group in groupby(schdls, lambda k: k[3]):
            list = [*group]
            if list[0] != list[-1]:
                start_date = datetime.date(*list[0][:3])
                end_date = datetime.date(*list[-1][:3])
                body = '%s%s(%s)~%s(%s):\n%s\n' % (body, start_date, wday(start_date), end_date, wday(end_date), content)
            else:
                date = datetime.date(*list[0][:3])
                body = '%s%s(%s):\n%s\n' % (body, date, wday(date), content)

        if not body:
            body = "일정이 없습니다.\n"
        msg = (head + body)[:-1]  # 맨 끝의 줄바꿈을 제거함
        # 기간 조회 끝

    else:  # 아무런 파라미터도 넘겨받지 못한 경우
        log.info("[#%s] cal@modules/skill.py: No Parameter" % req_id)
        return skill("오늘, 이번 달 등의 날짜 또는 기간을 입력해 주세요.")

    return skill(msg)


# 캐시 가져오기
def get_cache(reqdata, req_id, debugging):
    log.info("[#%s] get_cache@modules/skill.py: New Request" % req_id)
    # 사용자 ID 가져오고 검증
    uid = json.loads(reqdata)["userRequest"]["user"]["id"]
    if user.auth_admin(uid, req_id, debugging):
        cache_list = cache.get(req_id, debugging)
        if cache_list == "":
            log.info("[#%s] get_cache@modules/skill.py: No Cache" % req_id)
            cache_list = "\n캐시가 없습니다."
        msg = "캐시 목록:" + cache_list
    else:
        log.info("[#%s] get_cache@modules/skill.py: Non-Authorized User" % req_id)
        msg = "사용자 인증에 실패하였습니다.\n당신의 UID는 %s 입니다." % uid
    return skill(msg)


# 캐시 비우기
def purge_cache(reqdata, req_id, debugging):
    log.info("[#%s] purge_cache@modules/skill.py: New Request" % req_id)
    # 사용자 ID 가져오고 검증
    uid = json.loads(reqdata)["userRequest"]["user"]["id"]
    if user.auth_admin(uid, req_id, debugging):
        if cache.purge(req_id, debugging)["status"] == "OK":  # 삭제 실행, 결과 검증
            msg = "캐시를 비웠습니다."
        else:
            log.err("[#%s] purge_cache@modules/skill.py: Failed to Purge Cache" % req_id)
            msg = "삭제에 실패하였습니다. 오류가 발생했습니다."
    else:
        log.info("[#%s] purge_cache@modules/skill.py: Non-Authorized User" % req_id)
        msg = "사용자 인증에 실패하였습니다.\n당신의 UID는 %s 입니다." % uid
    return skill(msg)


# 캐시 상태확인
def check_cache(reqdata, req_id, debugging):
    log.info("[#%s] check_cache@modules/skill.py: New Request" % req_id)
    # 사용자 ID 가져오고 검증
    uid = json.loads(reqdata)["userRequest"]["user"]["id"]
    if user.auth_admin(uid, req_id, debugging):
        health = cache.health_check(req_id, debugging)
        msg = "시간표: %s\n한강 수온: %s\n날씨: %s" % (
            health["Timetable"], health["HanRiverTemperature"], health["Weather"])
    else:
        log.info("[#%s] check_cache@modules/skill.py: Non-Authorized User" % req_id)
        msg = "사용자 인증에 실패하였습니다.\n당신의 UID는 %s 입니다." % uid
    return skill(msg)


# 사용자 관리
def manage_user(reqdata, req_id, debugging):
    log.info("[#%s] manage_user@modules/skill.py: New Request" % req_id)
    try:
        user_grade = json.loads(reqdata)["action"]["params"]["Grade"]  # 학년 파싱
    except Exception:
        log.err("[#%s] manage_user@modules/skill.py: Error while Parsing Grade" % req_id)
        return skill("오류가 발생했습니다.\n요청 ID: " + req_id)
    try:
        user_class = json.loads(reqdata)["action"]["params"]["Class"]  # 반 파싱
    except Exception:
        log.err("[#%s] manage_user@modules/skill.py: Error while Parsing Class" % req_id)
        return skill("오류가 발생했습니다.\n요청 ID: " + req_id)
    try:
        uid = json.loads(reqdata)["userRequest"]["user"]["id"]  # UID 파싱
    except Exception:
        log.err("[#%s] manage_user@modules/skill.py: Error while Parsing UID" % req_id)
        return skill("오류가 발생했습니다.\n요청 ID: " + req_id)
    if debugging:
        print(user_grade)
        print(user_class)
        print(uid)
    req = user.manage_user(uid, user_grade, user_class, req_id, debugging)
    if req == "Registered":
        log.info("[#%s] manage_user@modules/skill.py: Created" % req_id)
        msg = "등록에 성공했습니다."
    elif req == "Same":
        log.info("[#%s] manage_user@modules/skill.py: Same" % req_id)
        msg = "저장된 정보와 수정할 정보가 같아 수정하지 않았습니다."
    elif req == "Updated":
        log.info("[#%s] manage_user@modules/skill.py: Updated" % req_id)
        msg = "수정되었습니다."
    else:
        log.err("[#%s] manage_user@modules/skill.py: Failed to Process Request" % req_id)
        return skill("오류가 발생했습니다.\n요청 ID: " + req_id)
    return skill(msg)


# 사용자 삭제
def delete_user(reqdata, req_id, debugging):
    log.info("[#%s] delete_user@modules/skill.py: New Request" % req_id)
    try:
        uid = json.loads(reqdata)["userRequest"]["user"]["id"]  # UID 파싱
    except Exception:
        log.err("[#%s] delete_user@modules/skill.py: Error while Parsing UID" % req_id)
        return skill("오류가 발생했습니다.\n요청 ID: " + req_id)
    if debugging:
        print(uid)
    req = user.delete_user(uid, req_id, debugging)
    if req == "NotExist":
        log.info("[#%s] delete_user@modules/skill.py: User does Not Exist" % req_id)
        msg = "존재하지 않는 사용자입니다."
    elif req == "Deleted":
        log.info("[#%s] delete_user@modules/skill.py: Deleted" % req_id)
        msg = "삭제에 성공했습니다."
    else:
        log.err("[#%s] delete_user@modules/skill.py: Failed to Process Request" % req_id)
        return skill("오류가 발생했습니다.\n요청 ID: " + req_id)
    return skill(msg)


# 한강 수온 조회
def wtemp(req_id, debugging):
    log.info("[#%s] wtemp@modules/skill.py: New Request" % req_id)
    return skill(getData.wtemp(req_id, debugging))


# 급식봇 브리핑
def briefing(reqdata, req_id, debugging, ):
    log.info("[#%s] briefing@modules/skill.py: New Request" % req_id)
    global briefing_header, hd_err, briefing_schdl, briefing_weather, briefing_meal, briefing_tt
    briefing_header = "일시적인 서버 오류로 헤더를 불러올 수 없었습니다.\n나중에 다시 시도해 보세요."
    briefing_schdl = "일시적인 서버 오류로 학사일정을 불러올 수 없었습니다.\n나중에 다시 시도해 보세요."
    briefing_weather = "일시적인 서버 오류로 날씨를 불러올 수 없었습니다.\n나중에 다시 시도해 보세요."
    briefing_meal = "일시적인 서버 오류로 식단을 불러올 수 없었습니다.\n나중에 다시 시도해 보세요."
    briefing_tt = "일시적인 서버 오류로 시간표를 불러올 수 없었습니다.\n나중에 다시 시도해 보세요."

    if datetime.datetime.now().time() >= datetime.time(11):  # 11시 이후이면
        # 내일을 기준일로 설정
        date = datetime.datetime.now() + datetime.timedelta(days=1)
        date_ko = "내일"
    else:  # 9시 이전이면
        # 오늘을 기준일로 설정
        date = datetime.datetime.now()
        date_ko = "오늘"

    log.info("[#%s] briefing@modules/skill.py: Date: %s" % (req_id, date))

    def logging_time(original_fn):
        def wrapper_fn(*args, **kwargs):
            result = original_fn(*args, **kwargs)
            if debugging:
                start_time = time.time()
                print("{} 실행.".format(original_fn.__name__))
                end_time = time.time()
                print("{} 종료. 실행시간: {} 초".format(original_fn.__name__, end_time - start_time))
            return result

        return wrapper_fn

    # 첫 번째 말풍선
    # 헤더
    @logging_time
    def f_header():
        global briefing_header, hd_err
        if date.weekday() >= 5:  # 주말이면
            log.info("[#%s] briefing@modules/skill.py: Weekend" % req_id)
            hd_err = "%s은 주말 입니다." % date_ko
        else:
            briefing_header = "%s은 %s(%s) 입니다." % (date_ko, date.date().isoformat(), wday(date))
            hd_err = None

    # 학사일정
    @logging_time
    def f_cal():
        global briefing_schdl
        briefing_schdl = getData.schdl(date.year, date.month, date.day, req_id, debugging)
        if not briefing_schdl:
            log.info("[#%s] briefing@modules/skill.py: No Schedule" % req_id)
            briefing_schdl = "%s은 학사일정이 없습니다." % date_ko
        else:
            briefing_schdl = "%s 학사일정:\n%s" % (date_ko, briefing_schdl)

    # 두 번째 말풍선
    # 날씨
    @logging_time
    def f_weather():
        global briefing_weather
        briefing_weather = getData.weather(date_ko, req_id, debugging)

    # 세 번째 말풍선
    # 급식
    @logging_time
    def f_meal():
        global briefing_meal
        briefing_meal = meal_core(date.year, date.month, date.day, date.weekday(), req_id, debugging)
        if "급식을 실시하지 않습니다." in briefing_meal:
            log.info("[#%s] briefing@modules/skill.py: No Meal" % req_id)
            briefing_meal = "%s은 %s" % (date_ko, briefing_meal)
        elif "열량" in briefing_meal:
            briefing_meal = "%s 급식:\n%s" % (date_ko, briefing_meal[16:].replace('\n\n', '\n'))  # 헤더부분 제거, 줄바꿈 2번 → 1번

    # 시간표
    @logging_time
    def f_tt():
        global briefing_tt
        tt_grade = str()
        tt_class = str()
        try:
            uid = json.loads(reqdata)["userRequest"]["user"]["id"]
            user_data = user.get_user(uid, req_id, debugging)  # 사용자 정보 불러오기
            tt_grade = user_data[0]
            tt_class = user_data[1]
        except Exception:
            log.err("[#%s] briefing@modules/skill.py: Failed to Fetch Timetable" % req_id)
            briefing_tt = "시간표 조회 중 오류가 발생했습니다."
        if tt_grade is not None or tt_class is not None:  # 사용자 정보 있을 때
            tt = getData.tt(tt_grade, tt_class, date.year, date.month, date.day, req_id, debugging)
            if tt == "등록된 데이터가 없습니다.":
                briefing_tt = "등록된 시간표가 없습니다."
            else:
                briefing_tt = "%s 시간표:\n%s" % (date_ko, tt.split('):\n\n')[1])  # 헤더부분 제거
        else:
            log.info("[#%s] briefing@modules/skill.py: Non-Registered User" % req_id)
            briefing_tt = "등록된 사용자만 시간표를 볼 수 있습니다."

    # 쓰레드 정의
    th_header = Thread(target=f_header)
    th_cal = Thread(target=f_cal)
    th_weather = Thread(target=f_weather)
    th_meal = Thread(target=f_meal)
    th_tt = Thread(target=f_tt)
    # 쓰레드 실행
    th_header.start()
    th_cal.start()
    th_weather.start()
    th_meal.start()
    th_tt.start()
    # 전 쓰레드 종료 시까지 기다리기
    th_header.join()
    if hd_err:
        return skill_simpletext(hd_err)
    th_cal.join()
    th_weather.join()
    th_meal.join()
    th_tt.join()

    # 응답 만들기
    return {'version': '2.0',
            'template': {
                'outputs': [
                    {
                        'simpleText': {
                            'text': "%s\n\n%s" % (briefing_header, briefing_schdl)
                        }
                    },
                    {
                        'simpleText': {
                            'text': briefing_weather
                        }
                    },
                    {
                        'simpleText': {
                            'text': "%s\n\n%s" % (briefing_meal, briefing_tt)
                        }
                    }
                ]
            }
            }


# 커밋 가져오기
def commits(req_id, debugging):
    log.info("[#%s] commits@modules/skill.py: New Request" % req_id)
    commit_list = getData.commits(req_id, debugging)
    commits_msg = ("급식봇의 기능 개선과 속도 향상, 버그 수정을 위해 노력하고 있습니다.\n"
                   "마지막 서버 업데이트는 %s에 있었습니다.\n"
                   "흥덕중 급식봇의 최근 변경 내역입니다:\n"
                   "%s\n%s\n%s\n%s\n%s" % (
                       commit_list[0], commit_list[1], commit_list[2], commit_list[3], commit_list[4], commit_list[5]))
    log.info("[#%s] commits@modules/skill.py: Started" % req_id)
    return skill(commits_msg)


def lol(reqdata, req_id, debugging):
    log.info("[#%s] lol@modules/skill.py: New Request" % req_id)
    try:
        summoner_name = json.loads(reqdata)["action"]["params"]["summonerName"]
    except Exception:
        log.err("[#%s] lol@modules/skill.py: Error while Parsing Summoner Name" % req_id)
        return skill("오류가 발생했습니다.\n요청 ID: " + req_id)

    # 소환사명 16자 초과하면
    if len(summoner_name) > 16:
        log.info("[#%s] lol@modules/skill.py: Summoner Name is Too Long" % req_id)
        return {'version': '2.0',
                'template': {
                    'outputs': [
                        {
                            "basicCard": {
                                "title": "소환사명이 너무 김",
                                "description": "소환사명이 너무 깁니다.\n"
                                               "소환사명은 영문 16자, 한글 8자 이내입니다.\n"
                                               "잘못 입력하진 않았는지 확인해주세요.",
                                "buttons": [
                                    {
                                        "action": "message",
                                        "label": "다시 검색하기",
                                        "messageText": "롤 전적 조회하기"
                                    }
                                ]
                            }
                        }
                    ]
                }
                }

    try:
        summoner_data = LoL.parse(summoner_name, req_id, debugging)
    except Exception:
        log.err("[#%s] lol@modules/skill.py: Error while Parsing Summoner Data" % req_id)
        return skill_simpletext("오류가 발생했습니다.\n요청 ID: " + req_id)

    if summoner_data == 'Invalid Token':
        log.err("[#%s] lol@modules/skill.py: Invalid Token" % req_id)
        return skill_simpletext("오류가 발생했습니다.\n요청 ID: " + req_id)
    elif summoner_data:
        # 솔랭 전적 구하기
        if summoner_data["ranked_solo"]:
            solo = ("솔랭 전적:\n"
                    "%s %s (%s LP)\n"
                    "%s승 %s패 (%s%%)\n\n" %
                    (summoner_data["ranked_solo"]["tier"], summoner_data["ranked_solo"]["rank"],
                     summoner_data["ranked_solo"]["leaguePoints"],
                     summoner_data["ranked_solo"]["wins"],
                     summoner_data["ranked_solo"]["losses"],
                     summoner_data["ranked_solo"]["winningRate"]))
        else:
            solo = "솔랭 전적이 없습니다. 분발하세요!\n\n"

        # 자유랭 전적 구하기
        if summoner_data["ranked_flex"]:
            flex = ("자유랭 전적:\n"
                    "%s %s (%s LP)\n"
                    "%s승 %s패 (%s%%)\n\n" %
                    (summoner_data["ranked_flex"]["tier"], summoner_data["ranked_flex"]["rank"],
                     summoner_data["ranked_flex"]["leaguePoints"],
                     summoner_data["ranked_flex"]["wins"],
                     summoner_data["ranked_flex"]["losses"],
                     summoner_data["ranked_flex"]["winningRate"]))
        else:
            flex = "자유랭 전적이 없습니다. 분발하세요!\n\n"

        # 통계 내기
        if summoner_data["games"]:
            if summoner_data["preferredLane"]:
                preferred_lane = "%s(%s%%)" % (summoner_data["preferredLane"][0], summoner_data["preferredLane"][1])
            else:
                preferred_lane = "정보없음"
            if summoner_data["preferredChampion"]:
                preferred_champion = ("%s(%s%%)" %
                                      (summoner_data["preferredChampion"][0], summoner_data["preferredChampion"][1]))
            else:
                preferred_champion = "정보없음"
            preferences = ("최근 %s번의 매치를 바탕으로 분석한 결과입니다:\n"
                           "많이한 라인: %s\n"
                           "많이한 챔피언: %s") % (summoner_data["games"], preferred_lane, preferred_champion)
        else:
            preferences = "통계가 없습니다. 분발하세요!"

        return {'version': '2.0',
                'template': {
                    'outputs': [
                        {
                            "basicCard": {
                                "title": "%s (레벨 %s)"
                                         % (summoner_data["summoner"]["name"], summoner_data["summoner"]["level"]),
                                "description": solo + flex + preferences,
                                "thumbnail": {
                                    "imageUrl": summoner_data["summoner"]["profileIcon"]
                                },
                                "buttons": [
                                    {
                                        "action": "webLink",
                                        "label": "OP.GG에서 보기",
                                        "webLinkUrl": summoner_data["summoner"]["OPGG"]
                                    },
                                    {
                                        "action": "message",
                                        "label": "다른 소환사 검색하기",
                                        "messageText": "롤 전적 조회하기"
                                    }
                                ]
                            }
                        }
                    ]
                }
                }
    else:
        return {'version': '2.0',
                'template': {
                    'outputs': [
                        {
                            "basicCard": {
                                "title": "소환사를 찾을 수 없음",
                                "description": summoner_name + " 소환사를 찾을 수 없습니다.\n"
                                                               "한국 서버에 등록된 소환사가 맞는지, "
                                                               "잘못 입력하진 않았는지 확인해주세요.",
                                "buttons": [
                                    {
                                        "action": "message",
                                        "label": "다시 검색하기",
                                        "messageText": "롤 전적 조회하기"
                                    }
                                ]
                            }
                        }
                    ]
                }
                }


def user_settings_web(reqdata, jwt_secret, req_id, debugging):
    url = os.getenv("SETTINGS_URL")
    try:
        uid = json.loads(reqdata)["userRequest"]["user"]["id"]
    except Exception:
        log.err("[#%s] briefing@modules/skill.py: Failed to Fetch Timetable" % req_id)
        return skill_simpletext("토큰 생성 중 오류가 발생했습니다.")
    encoded = jwt.encode({'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=300),
                          'uid': uid}, jwt_secret, algorithm='HS384')
    return {'version': '2.0',
            'template': {
                'outputs': [
                    {
                        "basicCard": {
                            "title": "내 정보 관리",
                            "description": "아래 버튼을 클릭해 관리 페이지로 접속해 주세요.\n"
                                           "링크는 5분 뒤 만료됩니다.",
                            "buttons": [
                                {
                                    "action": "webLink",
                                    "label": "내 정보 관리",
                                    "webLinkUrl": url + "?token=" + encoded.decode("UTF-8")
                                }
                            ]
                        }
                    }
                ]
            }
            }


def notify(reqdata, req_id, debugging):
    now = datetime.datetime.now()
    try:
        onesignal_app_id = json.loads(reqdata)["OneSignal"]["AppID"]
        onesignal_api_key = json.loads(reqdata)["OneSignal"]["APIKey"]
    except Exception:
        return {"message": "OneSignal AppID 또는 APIKey 없음"}, 401
    try:
        title = json.loads(reqdata)["Title"]
        url = json.loads(reqdata)["URL"]
    except Exception:
        return {"message": "올바른 요청이 아님"}, 400
    if now.weekday() >= 5:
        return {"message": "알림미발송(주말)"}
    meal = getData.meal(now.year, now.month, now.day, req_id, debugging)
    if not "menu" in meal:
        return {"message": "알림미발송(정보없음)"}
    reqbody = {
        "app_id": onesignal_app_id,
        "headings": {
            "en": title
        },
        "contents": {
            "en": meal["date"]+" 급식:\n"+re.sub(r'\[[^\]]*\]', '', meal["menu"]).replace('⭐', '')
        },
        "url": url,
        "included_segments": [
            "All"
        ]
    }
    reqheader = {
        "Content-Type": "application/json",
        "Authorization": "Basic " + onesignal_api_key
    }
    try:
        request = requests.post("https://onesignal.com/api/v1/notifications", data=json.dumps(reqbody), headers=reqheader)
    except Exception as error:
        return error
    return {"message": "성공"}


# 디버그
if __name__ == "__main__":
    log.init()
    # print(skill("msg"))
    print(lol(None, "****DEBUG****", True))
