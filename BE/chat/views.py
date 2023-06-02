from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Answer
from .serializers import AnswerSerializer

from question_keyword.question_keyword_extraction import QKE
from station.station import Station

st = Station() 

# Create your views here.
@api_view(['GET'])
def helloAPI(request):
    return Response("hello world!");

@api_view(['POST'])
def chatAnswer(request):
	# get question from request
	print(request)
	print(request.data)
	question = request.data.get("question")
	print(question)

	# get elastic query from question
	keyword_query = QKE.question_keyword_extraction(question)
	print(keyword_query)

	# search elastic cloud by keywords
	# send documents and keywords to GPT
	answer = st.func(question, keyword_query)

	return Response({"answer": answer})
