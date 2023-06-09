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
            {
                "role": "system",
                "content": 'You are a helpful assistant that generates answers to questions based on the documents given. Questions and documents will be given in the following form\n' +
                           '[{"role": "user", "content": "\'Question: "{text}"\', \'Doc1: "{text}"\', \'Doc2: "{text}"\', ..."}]\n' +
                           'You must find the information in the documents above and produce the correct answer to the question. Even if you don\'t find the right information to generate a question, you must create a plausible answer. You must answer in Korean.'
            }
        ]

        self.temp_message = []

        self.model = "gpt-3.5-turbo-0301"

        # clova summarizer
        self.clova = Summarizer()

    def num_tokens_from_messages(self, flag):
        if flag == 1:
            messages = self.temp_message
        else:
            messages = self.messages

        try:
            self.encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")

        if self.model == "gpt-3.5-turbo-0301":  # note: future models may deviate from this
            num_tokens = 0
            for message in messages:
                num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
                for key, value in message.items():
                    num_tokens += len(self.encoding.encode(value))
                    if key == "name":  # if there's a name, the role is omitted
                        num_tokens -= 1  # role is always required and always 1 token
            num_tokens += 3  # every reply is primed with <im_start>assistant -> response까지 생각해서 내가 임의로 하나 더해줬음.
            return num_tokens
        else:
            raise NotImplementedError(
                f"""num_tokens_from_messages() is not presently implemented for model {self.model}.""")

    def func(self, question, query):
        # 검색 요청
        scroll_size = 5
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
        i = 1
        for hit in result['hits']['hits']:
            title = f"{hit['_source']['title']}"
            content = f"{hit['_source']['contents']}"
            print("title")
            print(title)
            print("content")
            print(content)
            self.temp_message.append({"role": "user", "content": f"{content}"})
            if self.num_tokens_from_messages(1) < 600:
                print("no summarized")
                doc_summarized += ", Doc" + f"{i}" + ": " + title + content
                i = i + 1
            else:
                hit_summarized = self.clova.summarize(title=title, content=content)
                print("hit_summarized")
                print(hit_summarized)
                print(type(hit_summarized))
                if hit_summarized == "Error":
                    document_num -= 1
                    doc_url += f"{hit['_source']['url']}" + " \n"
                    print("doc_url")
                    print(doc_url)
                    if document_num == 0:
                        print("죄송합니다. 문서 내용이 길어 요약이 불가능합니다. 아래 링크를 참조해주세요. \n\n " + doc_url)
                        answer = "죄송합니다. 문서 내용이 길어 요약이 불가능합니다. 아래 링크를 참조해주세요. \n\n " + doc_url
                        return answer
                else:
                    doc_summarized += ", Doc" + f"{i}" + ": " + hit_summarized
                    i = i + 1
            self.temp_message.pop(0)
        print("doc_summarized")
        print(doc_summarized)

        #question += " 아래 내용을 바탕으로 답변해줘\n"
        question = "Question: " + question
        question += doc_summarized
        print("question")
        print(question)
        self.messages.append({"role": "user", "content": f"{question}"})

        if self.num_tokens_from_messages(0) > 3900:
            while self.num_tokens_from_messages(0) > 3900:
                self.messages.pop(1)
                self.messages.pop(1)
        if len(self.messages) == 1:
            print("죄송합니다. 이번 답변은 못 할 것 같습니다.")
            answer = "죄송합니다. 이번 답변은 못 할 것 같습니다."
            return answer

        print("question")
        print(question)

        print("self.num_tokens_from_messages(0)")
        print(self.num_tokens_from_messages(0))

        response = openai.ChatCompletion.create(
            model = self.model,
            messages = self.messages
        )

        print("response.usage and finish_reason")
        print(response.usage)
        print(response.choices[0]['finish_reason'])
        if response.choices[0]['finish_reason'] != "stop":
            answer = "GPT API에서 오류가 발생하였습니다."
            return answer
        answer = response.choices[0]['message']['content']
        self.messages.append({"role": "assistant", "content": f"{answer}"})
        return answer