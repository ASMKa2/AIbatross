# import summarizer in your source code (file.py)
file.py 위치에 따라 summarizer를 import하는 구문이 디르다.

## aibatross/file.py
`from summarizer import Summarizer`

## aibatross/any_dir/file.py
`import sys, os`

`sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))`

`from summarizer.summarizer import Summarizer`

---
# Usage
`clova = Summarizer()`

`title = "YOUR_TITLE"`

`content = "YOUR_CONTENT"`

`text_summarized = clova.summarize(title, content)`

`print(text_summarized)`
