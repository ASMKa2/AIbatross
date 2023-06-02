from elasticsearch import Elasticsearch
import openai
import os
import tiktoken
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from summarizer.summarizer import Summarizer

class Station:
    def __init__(self):
        self.es = Elasticsearch(
            cloud_id="",
            http_auth=("elastic", ""),
        )

        # OpenAI API Key 설정
        os.environ["OPENAI_API_KEY"]=""
        assert "OPENAI_API_KEY" in os.environ, "환경 변수에 OPENAI_API_KEY가 설정되어 있어야 합니다."
        openai.api_key = os.environ["OPENAI_API_KEY"]

        self.messages = [
            {"role": "system", "content": "You are a helpful assistant that "}
        ]

        self.model = "gpt-3.5-turbo-0301"

        # clova summarizer
        self.clova = Summarizer()

    def num_tokens_from_messages(self):
        try:
            self.encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        if self.model == "gpt-3.5-turbo-0301":  # note: future models may deviate from this
            num_tokens = 0
            for message in self.messages:
                num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
                for key, value in message.items():
                    num_tokens += len(self.encoding.encode(value))
                    if key == "name":  # if there's a name, the role is omitted
                        num_tokens += -1  # role is always required and always 1 token
            num_tokens += 3  # every reply is primed with <im_start>assistant -> response까지 생각해서 내가 임의로 하나 더해줬음.
            return num_tokens
        else:
            raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {self.model}.""")

    def func(self, question, query):
        # 검색 요청
        scroll_size = 1
        result = self.es.search(index="aibatross", body={
            "query": {
                "match": {
                    "contents": {
                        "query": query
                    }
                }
            }
        }, scroll="1m", size=scroll_size)

        print("Elasticsearch 검색 결과")
        document_num = result['hits']['total']['value']
        print("document_num")
        print(document_num)
        if document_num > 0:
            for hit in result['hits']['hits']:
                print(hit['_source'])
        else:
            print("검색 결과가 없습니다.")
            answer = "검색 결과가 없습니다. 보다 일반적인 키워드로 질문해주세요."
            return answer

        # extract 'title' and 'content' from search result
        doc_summarized = ""
        doc_url = ""
        for hit in result['hits']['hits']:
            title = ''
            content = f"{hit['_source']}"
            if len(content) > 2000:
                document_num -= 1
                doc_url += f"{hit['_source']['url']}" + " \n"
                print("doc_url")
                print(doc_url)
                if document_num == 0:
                    print("죄송합니다. 문서 내용이 길어 요약이 불가능합니다. 아래 링크를 참조해주세요. \n\n " + doc_url)
                    answer = "죄송합니다. 문서 내용이 길어 요약이 불가능합니다. 아래 링크를 참조해주세요. \n\n " + doc_url
                    return answer
            else:
                hit_summarized = self.clova.summarize(title=title, content=content)
                print("hit_summarized")
                print(hit_summarized)
                doc_summarized += hit_summarized + "\n"
        print("doc_summarized")
        print(doc_summarized)

        question += " 아래 내용을 바탕으로 답변해줘\n"
        question += doc_summarized
        self.messages.append({"role": "user", "content": f"{question}"})

        if self.num_tokens_from_messages() > 4000:
            while self.num_tokens_from_messages() > 4000:
                self.messages.pop(1)
                self.messages.pop(1)
        if len(self.messages) == 1:
            print("죄송합니다. 이번 답변은 못 할 것 같습니다.")
            answer = "죄송합니다. 이번 답변은 못 할 것 같습니다."
            return answer

        print("self.num_tokens_from_messages()")
        print(self.num_tokens_from_messages())

        response = openai.ChatCompletion.create(
            model = self.model,
            messages = self.messages
        )

        print("response.usage and finish_reason")
        print(response.usage)
        print(response.choices[0]['finish_reason'])
        answer = response.choices[0]['message']['content']
        self.messages.append({"role": "assistant", "content": f"{answer}"})
        return answer
