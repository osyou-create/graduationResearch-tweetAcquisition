import sys
import MeCab
m = MeCab.Tagger ("-Ochasen")
text = input("入力してください>>")
print(m.parse (text))
