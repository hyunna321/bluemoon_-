from langchain_openai import ChatOpenAI
import json
import requests

#시간 라이브러리
from datetime import datetime

#일반적인 의도 파악 및 메시지를 작성
llm = ChatOpenAI(
	model = 'gpt-4o-mini', 
	api_key = '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',
	temperature= 0.3,
	model_kwargs={'response_format' : {'type':'json_object'}})

llm2 = ChatOpenAI(
	model = 'gpt-4o-mini', 
	api_key = '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',
	temperature= 0.3)

#user_input을 바탕으로, 사용자의 의도를 파악함
#LLM을 사용하는 agent
def classify_intent(state : dict) -> dict :

	#사용자의 입력 문장을 state에서 가져옴
	user_input = state.get('user_input', '')

	prompt = f"""
		당신은 사용자의 자연어 입력을 food / activity / unknown 중 하나로 분류하는 AI입니다.

		입력: "{user_input}"

		분류 기준:
		- 음식 관련 표현 → "food" (예: 배고파, 뭐 먹지, 야식 추천해줘 등)
		- 활동 관련 표현 → "activity" (예: 심심해, 뭐 하지, 놀고 싶어 등)
		- 증상, 감정, 질문, 애매한 표현 → "unknown"

		조금 애매한 표현이라도 의미가 보이면 food 또는 activity로 분류하세요.

		출력은 반드시 다음 중 하나의 JSON 배열 또는 객체로 작성하세요:
		- 배열: ["food"]
		- 객체: {{ "intent": ["food"] }}
		"""

	response = llm.invoke([
		{'role' : 'user', 'content' : prompt.strip()}
		])

	#strip()을 통해 양쪽 공백 제거
	intents = response.content.strip()
	print(f'{user_input}에 대한 GPT의 의도 분류 : {intents}')

	try:
		#intents를 json.loads()로 파싱하여 가져옴
		parsed = json.loads(intents)

		#isinstance(A, B) -> A가 B타입이냐?
		#parsed != None
		#parsed[0]가 food나 activity중에 하나라면~
		if isinstance(parsed, list) and parsed and parsed[0] in ['food', 'activity']:
			
			#**state라는 딕셔너리에,
			#'intent'라는 키와 parsed[0]이라는 값을 
			return {**state, 'intent' : parsed[0]}

		if isinstance(parsed, dict):
			if 'intent' in parsed:
				in_value = parsed['intent']

				if isinstance(in_value, list) and in_value and in_value[0] in ['food', 'activity']:
					
					#number += 1
					#state += {'intent':value}
					return {**state, 'intent':in_value[0]}

				for key in ['food', 'activity']:
					if key in parsed:
						return {**state, 'intent':key}


	except Exception as e :
		print(f'에러 발생 : {e}')

	return {**state, 'intent':'unknown'}


#현재 시각을 기준으로 시간대를 분류
def get_time_slot(state : dict) -> dict :

	#시간 00~24까지
	hour = datetime.now().hour

	if 5 <= hour < 11:
		return {**state, 'time_slot':'아침'}

	elif 11 <= hour < 15:
		return {**state, 'time_slot':'점심'}

	elif 15 <= hour < 18:
		return {**state, 'time_slot':'오후'}

	else:
		return {**state, 'time_slot': '저녁'}


#현재 날짜를 기준으로 계절 분류 
def get_season(state : dict) -> dict:
	month = datetime.now().month

	if 3 <= month <= 5:
		season = '봄'
	elif 6 <= month <= 8:
		season = '여름'
	elif 9 <= month <= 11:
		season = '가을'
	else:
		season = '겨울'
	return {**state, 'season':season} 


#llm을 이용하여 음식 추천을 받음
def recommend_food(state : dict) -> dict:

	#음식 추천에 필요한 데이터 받아옴
	#state.get(a, b) a값을 가져오되, 없으면 b를 가져와.
	user_input = state.get('user_input', '') 
	season = state.get('season', '봄')
	weather = state.get('weather', 'Clear')
	time_slot = state.get('time_slot', '오후')

	prompt = f"""당신은 음식 추천 AI입니다.
		사용자 입력: "{user_input}"
		현재 조건:
		- 계절: {season}
		- 날씨: {weather}
		- 시간대: {time_slot}

		이 조건에 어울리는 음식 2가지를 추천해 주세요.

		사용자가 특정 음식을 언급한 경우(예: "피자")에는 그 음식을 포함하거나,
		관련된 음식 또는 어울리는 음식으로 추천해도 좋습니다.

		결과는 반드시 JSON 배열 형식으로 출력하세요.
		예: ["피자", "떡볶이"]
		"""

	response = llm.invoke([{'role':'user', 'content':prompt.strip()}])

	items = json.loads(response.content)

	#응답 내용을 JSON으로 파싱
	if isinstance(items, dict):
		#flatten(평탄화) -> [[1, 2, 3], [2, 3, 4 ]] -> [1, 2, 3, 2, 3, 4]
		#itertools -> 

		#items = {'1':[1, 2, 3], }
		#(sub if isinstance(sub, list) else [sub]) -> sub가 list인 경우 sub를 반환, 그렇지않으면 [sub]
		items = [i for sub in items.values() for i in (sub if isinstance(sub, list) else [sub])] 
		#[i  for i in (sub if isinstance(sub, list) else [sub])]
		#for sub in items.values()

	elif not isinstance(items, list):
		items = [str(items)]

	return {**state, 'recommend_food': items}



#현재 날씨를 가져옴(api를 활용)
def get_weather(state : dict) -> dict:

	WEATHER_API_KEY = '17c9ba52f1e3f35c690c4cace7c2cd2a'

	#날씨 정보를 물어볼 인터넷 api 주소 
	url = "https://api.openweathermap.org/data/2.5/weather"
	#날씨를 요청할 때 필요한 부가 정보
	params = {
		'q' : 'Cheonan',
		'appid' : WEATHER_API_KEY,
		'lang' : 'kr',
		'units' : 'metric'}

	#정해진 위치로 요청을 보냄
	response = requests.get(url, params=params)

	#응답 코드가 '실패'일 경우 => 오류가 발생하면 오류 상태 코드 확인
	response.raise_for_status()

	weather_data = response.json()
	weather = weather_data['weather'][0]['main'] 

	return {**state, 'weather': weather}


def recommend_activity(state:dict) -> dict:

	#입력 상태에서 정보 추출
	#state.get('a', 'b') ==> a를 가져오되, 없으면 b 
	user_input = state.get('user_input', '')
	season = state.get('season', '봄')
	weather = state.get('weather', 'Clear')
	time_slot = state.get('time_slot', '오후')

	#위의 정보를 바탕으로, 내가 하면 좋을 활동(액티비티)을 추천해달라.
	prompt = f"""당신은 활동 추천 AI입니다.

			사용자 입력: "{user_input}"
			현재 조건:
			- 계절: {season}
			- 날씨: {weather}
			- 시간대: {time_slot}

			이 조건과 입력에 어울리는 활동 2가지를 추천해 주세요.
			실내 활동이 포함되면 더 좋습니다.

			결과는 반드시 JSON 배열 형식으로 출력하세요.
			예: ["북카페 가기", "실내 보드게임"]
			""" 

	response = llm.invoke([{'role':'user', 'content': prompt.strip()}])

	items = json.loads(response.content)

	#응답을 파싱, 우리가 결과물을 JSON으로 보내달라고 함
	# [[1, 2, 3], [2, 3, 4]] -> 1차원으로 평탄화(flatten) : [1, 2, 3, 2, 3, 4] 
	# itertools 
	if isinstance(items, dict):
		items = [i for sub in items.values() for i in (sub if isinstance(sub, list) else [sub])]
		# i for i in (sub if isinstance(sub, list) else [sub])
		# sub in items.values()

	elif not isinstance(items, list):
		items = [str(items)]

	#이 함수의 최종목표 : 추천 활동을 리스트로 만들어서 state에 추가해 보내주기.
	return {**state, 'recommend_activity': items}


#langgraph 플로우 안에 포함되어 있음
#추천된 항목을 바탕으로 장소 검색용 키워드를 생성
#음식 : 냉면 -> 냉면집, 보드게임 -> 보드게임 카페
def generate_search_keyword(state: dict) -> dict:
    """
    GPT를 사용하여 추천 항목을 바탕으로 장소 검색용 키워드를 생성하는 함수입니다.
    예: 김치찌개 → 한식, 책 읽기 → 북카페
    """

    # 추천 항목 리스트 추출 (음식 또는 활동)
    items = state.get("recommended_items", ["추천"])
    if isinstance(items, dict):
        # 딕셔너리인 경우 → 값만 추출 (중첩 flatten)
        items = [i for sub in items.values() for i in (sub if isinstance(sub, list) else [sub])]
    elif not isinstance(items, list):
        items = [str(items)]  # 문자열인 경우 → 리스트로 변환

    item = items[0]  # 첫 번째 추천 항목을 기반으로 키워드 생성

    user_input = state.get("user_input", "")      # 사용자 입력
    intent = state.get("intent", "food")          # food 또는 activity

    # GPT 프롬프트 작성
    prompt = f"""사용자의 입력: "{user_input}"
추천 항목: "{item}"
의도: "{intent}"

이 항목을 장소에서 검색하려고 합니다.
음식이라면 음식 종류(예: 김치찌개 → 한식),
활동이라면 장소 유형(예: 책 읽기 → 북카페)으로 변환하세요.

결과는 반드시 JSON 배열로 출력하세요.
예: ["한식"]
"""  # f-string 끝

    # GPT 호출
    response = llm.invoke([{"role": "user", "content": prompt.strip()}])

    # GPT 응답 파싱
    keywords = json.loads(response.content)

    # dict 형태 응답 → 값 추출
    if isinstance(keywords, dict):
        keywords = [i for sub in keywords.values() for i in (sub if isinstance(sub, list) else [sub])]
    elif not isinstance(keywords, list):
        keywords = [str(keywords)]

    # 생성된 키워드 중 첫 번째를 상태에 추가
    return {**state, "search_keyword": keywords[0] if keywords else item}


#location과 search_keyword를 바탕으로, 
#카카오맵을 활용해서 장소 정보를 가져오는 함
KAKAO_API_KEY='e8f73c7e446929653aebf115efd39887s'
def search_place(state: dict) -> dict:
    """
    사용자의 지역 정보(location)와 검색 키워드(search_keyword)를 바탕으로
    Kakao Local API를 호출하여 근처 장소 정보를 가져오는 함수입니다.
    """

    # 상태에서 검색 키워드 및 지역 정보 추출
    location = state.get("location", "홍대")               # 예: "홍대"
    keyword = state.get("search_keyword", "추천")          # 예: "한식", "북카페"

    # 검색어는 '지역 + 키워드' 조합으로 구성
    query = f"{location} {keyword}"
    print(">>> GPT 생성 키워드 검색:", query)  # 디버깅용 로그

    # Kakao Local Search API endpoint
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {
        "Authorization": f"KakaoAK {KAKAO_API_KEY}"  # API 키 인증
    }
    params = {
        "query": query,   # 검색어
        "size": 5         # 최대 5개의 결과 요청
    }

    print(headers)

    # API 요청 전송
    res = requests.get(url, headers=headers, params=params)
    res.raise_for_status()  # 요청 실패 시 예외 발생

    # 응답 결과 중 첫 번째 장소만 사용
    docs = res.json()["documents"]

    if docs:
        top = docs[0]  # 가장 관련성 높은 장소
        place = {
            "name": top["place_name"],               # 장소 이름
            "address": top["road_address_name"],     # 도로명 주소
            "url": top["place_url"]                  # 지도 링크
        }
    else:
        # 검색 결과 없을 경우 기본 메시지
        place = {
            "name": "추천 장소 없음",
            "address": "",
            "url": ""
        }

    # 추천 장소 정보를 상태에 추가하여 반환
    return {**state, "recommended_place": place}
    


#위의 모든 정보를 토대로 사용자에게 return할 문장을 생성하는 함수이다.
def summarize_messages(state: dict) -> dict:

	#추천 항목 리스트의 항목 추출
	items = state.get('recommend_items', ['추천 항목 없음'])

	if isinstance(items, dict):
		items = list(items.values())

	elif not isinstance(items, list):
		items = [str(items)]

	#item => items 리스트의 가장 첫번째 요소
	item = items[0]

	#state 상태에서 필요한 정보를 추출
	season = state.get('season', '')
	weather = state.get('weather', '')
	time_slot = state.get('time_slot','')
	intent = state.get('intent', 'food')
	place = state.get('recommend_place', {})

	#장소정보
	place_name = place.get('name', '추천 장소 없음')
	place_address = place.get('address', '')
	place_url = place.get('url', '')

	category = '음식' if intent == 'food' else '활동'

	#GPT 프롬프트 구성하기
	prompt = f'''
		현재 사용자는 {category}라는 의도로 질문하였습니다.
		계절은 {season}이고, 날씨는 {weather}, 시간대는 {time_slot}입니다.

		추천할 아이템은 {category} : {item} 이고,
		추천 장소는 {place_name}({place_address}),
		추천 장소의 지도 링크는 {place_url} 입니다.

		위의 정보를 바탕으로 사용자의 의도를 감성적이고 따뜻한 시선으로 해석하여
		추천할 아이템 및 장소에 대해 잘 소개해 주세요.

		추천메시지는 한 문단 정도 길이로, 위의 추천 아이템, 장소, 주소, url이 모두 들어가야 합니다.
	'''

	response = llm2.invoke([
		{'role':'system', 'content': '너는 음식과 활동에 대해 추천할만한 재미있는 장소를 잘 알고있는 여행 보조 AI야.'},
		{'role':'user', 'content':prompt}

	])

	return {**state, 'final_message': response.content.strip()}

def intent_unkown(state:dict)->dict:
	return {**state, 'final_message': '저는 음식이나 활동 관련 추천만 해드릴 수 있어요.'}


# if __name__ == '__main__':
# 	get_weather()