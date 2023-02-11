**이 Repo는 더 이상 업데이트되지 않습니다. 아래 링크의 Repo를 참조하세요.**

**[https://github.com/hyunbridge/hdmeal-chatbot](https://github.com/hyunbridge/hdmeal-chatbot)**

# 흥덕중 급식봇

흥덕중 급식봇은 흥덕중학교 학교생활에 유용한 정보들을 간단하게 조회할 수 있는 카카오톡 챗봇입니다.

이 프로그램은 카카오 i 오픈빌더의 Skill 서버 및 기타 용도로 사용되기 위해 만들어진 API 서버입니다.

[![채널 추가]( https://developers.kakao.com/assets/img/about/logos/channel/friendadd_large_yellow_rect.png )]( http://pf.kakao.com/_xkxeaGT )



## 기능

흥덕중 급식봇은 이런 기능들을 지원합니다:

* 특정 날짜의 식단 조회 API 제공
* Facebook에 내일의 급식 게시
* 카카오 i 오픈빌더 Skill 서버:
  * 브리핑 (학사일정, 날씨, 급식, 시간표 통합조회)
  * 식단 조회
  * 시간표 조회 (사용자 등록이 가능해 매번 학년/반 정보를 보내지 않아도 됨)
  * 학사일정 조회
  * 한강 수온 조회
  * 사용자 관리



## 설치 & 실행
다음 환경에서 작동이 확인 되었습니다:
```
Python 3.7
Windows 10 x64 (1903) - 개발환경
MS Azure App Services (Linux) - 프로덕션 환경
```

서버의 시간대에 영향을 받습니다. 제대로 된 작동을 위해 **서버의 시단대를 한국 표준시(KST)로 변경**하는 것이 좋습니다.



리포지토리를 로컬PC로 복제합니다:

```bash
git clone https://github.com/hgyoseo/hdmeal.git
```

그런 다음, 프로젝트 폴더에서 다음 명령을 실행하여 패키지 의존성을 해결합니다:

```bash
pip install -r requirements.txt
```

다음 명령으로 서버를 시작할 수 있습니다:

```bash
python application.py
```

실제 프로덕션 환경에서는 gunicorn 등과 함께 이용하시는 것을 추천합니다.


