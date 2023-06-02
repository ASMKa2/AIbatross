question_keyword_extraction()

    사용자 질문 입력 시
    키워드 추출 후 elastic query를 아래 형태의 string으로 return

    GET my_index/_search
    {
        "query": {
            "match": {
                "contents" : ""
            }
        }
    }