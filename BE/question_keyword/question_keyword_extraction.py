from konlpy.tag import Hannanum

class QKE:
	def __init__(self):
		pass


	def question_keyword_extraction(str):
		hannanum = Hannanum()

		pos_list = hannanum.pos(str)
		keyword_list = []

		for p in pos_list:
			if p[1] == 'P' or p[1] == 'N' or p[1] == 'M':
				keyword_list.append(p[0])

		query1 = ""
		
		for k in keyword_list:
			query1 += k + " "

		return query1
