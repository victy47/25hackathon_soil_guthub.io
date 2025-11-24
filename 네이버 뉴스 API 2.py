import requests
import re
import pandas as pd
from datetime import datetime
import time

class NaverNewsAPI:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = "https://openapi.naver.com/v1/search/news.json"
    
    def search_news(self, query, display=100, start=1, sort="date"):
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort
        }
        
        try:
            response = requests.get(self.api_url, headers=headers, params=params)
            if response.status_code == 401:
                print("❌ API 키 인증 실패!")
                return None
            elif response.status_code == 403:
                print("❌ API 접근 권한 없음!")
                return None
            elif response.status_code != 200:
                print(f"❌ API 오류: {response.status_code}")
                return None
            
            result = response.json()
            if start == 1:
                total = result.get('total', 0)
                print(f"✅ API 연결 성공! 전체 검색 결과: {total}개")
            
            return result
        except Exception as e:
            print(f"❌ 오류: {e}")
            return None
    
    def search_news_by_period(self, include_keywords, exclude_keywords=None,
                             start_date=None, end_date=None, max_results=1000):
        
        print(f"포함 키워드 리스트: {include_keywords}")
        if exclude_keywords:
            print(f"제외 키워드 리스트: {exclude_keywords}")
        if start_date and end_date:
            print(f"기간: {start_date} ~ {end_date}")
        print("=" * 60)
        
        filter_by_date = bool(start_date and end_date)
        if filter_by_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        
        # 1단계: 키워드별로 기사 수집 (exclude 필터링 없이)
        all_articles = []
        
        for kw in include_keywords:
            print(f"\n🔍 키워드 검색 시작: {kw}")
            start_pos = 1
            
            while start_pos <= max_results:
                print(f"   검색 중... (위치: {start_pos})")
                result = self.search_news(kw, display=100, start=start_pos, sort="date")
                
                if not result or 'items' not in result:
                    break
                
                items = result['items']
                if not items:
                    break
                
                for item in items:
                    try:
                        pub_date_str = item['pubDate']
                        pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
                        pub_date_naive = pub_date.replace(tzinfo=None)
                        
                        # 날짜 필터링만 적용
                        if filter_by_date:
                            if pub_date_naive < start_dt or pub_date_naive > end_dt:
                                continue
                        
                        title = re.sub(r'<[^>]+>', '', item.get('title', ''))
                        description = re.sub(r'<[^>]+>', '', item.get('description', ''))
                        
                        all_articles.append({
                            '제목': title,
                            '내용': description,
                            '링크': item.get('link'),
                            '발행일': pub_date_naive.strftime("%Y-%m-%d %H:%M:%S"),
                            '원본링크': item.get('originallink', '')
                        })
                    except Exception as e:
                        continue
                
                start_pos += 100
                if start_pos > 1000:
                    print("   → API 검색 한계 도달 (start > 1000)")
                    break
                
                time.sleep(0.1)
        
        print(f"\n📊 1단계 완료: 총 수집된 기사 {len(all_articles)}개")
        
        # 2단계: 중복 제거 (링크 기준)
        seen = set()
        unique_articles = []
        for art in all_articles:
            link = art.get('링크')
            if link and link not in seen:
                seen.add(link)
                unique_articles.append(art)
        
        print(f"📊 2단계 완료: 중복 제거 후 {len(unique_articles)}개")
        
        # 3단계: 제외 키워드 필터링
        if exclude_keywords:
            filtered_articles = []
            for art in unique_articles:
                title = art.get('제목', '')
                description = art.get('내용', '')
                
                # 제외 키워드가 제목이나 내용에 포함되어 있는지 확인
                has_exclude = any(exc in title or exc in description for exc in exclude_keywords)
                
                if not has_exclude:
                    filtered_articles.append(art)
            
            print(f"📊 3단계 완료: 제외 키워드 필터링 후 {len(filtered_articles)}개")
            return filtered_articles
        
        print(f"\n✅ 최종 수집 완료: {len(unique_articles)}개")
        return unique_articles
    
    def save_to_csv(self, articles, filename):
        if articles:
            df = pd.DataFrame(articles)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"✅ {len(articles)}개 기사 CSV 저장 완료: {filename}")
        else:
            print("⚠️ 저장할 기사 없음")
    
    def save_to_excel(self, articles, filename):
        if articles:
            df = pd.DataFrame(articles)
            df.to_excel(filename, index=False, engine='openpyxl')
            print(f"✅ {len(articles)}개 기사 Excel 저장 완료: {filename}")
        else:
            print("⚠️ 저장할 기사 없음")

if __name__ == "__main__":
    client_id = "ec_FtupnwjtWaskgBSsp"
    client_secret = "0rGrlHT_2Q"
    
    api = NaverNewsAPI(client_id, client_secret)
    
    include_keywords = ["에스오일", "에쓰오일", "S-OIL", "히즈아지", "S오일"]
    exclude_keywords = ["진학사", "퀵리포트", "주요단신", "석유와가스업종", "톡톡생활정보", "주가정보", "부고", "별세", "임직원평균연봉"]
    
    start_date = "2025-11-01"
    end_date = "2025-11-20"
    
    articles = api.search_news_by_period(
        include_keywords=include_keywords,
        exclude_keywords=exclude_keywords,
        start_date=start_date,
        end_date=end_date,
        max_results=1000
    )
    
    if articles:
        api.save_to_csv(articles, "news_results.csv")
    