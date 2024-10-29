from scholarly import scholarly
import pandas as pd

def crawl_academic_papers():
    keywords = [
        "한국 금융시장", "기업재무", "주식시장 분석",
        "재무회계", "투자론", "기업가치평가"
    ]
    
    papers_data = []
    for keyword in keywords:
        search_query = scholarly.search_pubs(keyword)
        # 각 키워드당 50개의 논문 수집
        for i in range(50):
            try:
                paper = next(search_query)
                papers_data.append({
                    'title': paper.bib.get('title'),
                    'abstract': paper.bib.get('abstract'),
                    'year': paper.bib.get('year'),
                    'url': paper.bib.get('url')
                })
            except StopIteration:
                break
    
    return pd.DataFrame(papers_data) 