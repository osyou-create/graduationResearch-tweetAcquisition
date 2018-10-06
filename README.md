# Pythonツイートデータ取得

tweet取得用のpythonコード書いたので、使いたい方がいれば。

## 環境
- python 3.6.2
- pip 10.0.1
- pyenv 1.1.3  
※print文に「formatted string literal」を使用しているので、pythonのバージョンを3.6以上にしてください。  
python2を使用していて、どうしても3.6以上にしたくない人は、str.format()にしてください(python2.6以上)  

## パッケージインストール

```
$ pip install requests_oauthlib
$ pip install python-dotenv
```

その他エラー吐いたら必要なパッケージを適宜pipでインストールしてください。

## dotenvについて
環境変数はdotenvを使用して、外部ファイルから呼び出す形にしています。  
「.env」を生成して、その中にtwitter api keyをそれぞれ入れてください。  
twitter apiは[ここ](https://apps.twitter.com/)から取得してください。

```
CONSUMER_KEY = Gm2retesEcl....
CONSUMER_SECRET = Rckdretse5d3....
ACCESS_TOKEN = 1gsdfs2412-x7....
ACCESS_TOKKEN_SECRET = afsedaf7GvF...
```

## 実行手順
1.  `$ git clone git@github.com:osyou-create/tweet_acp.git`
2.  「.env」ファイル作成
3.  Twitter apiに必要なキー４種類を.envファイルにセット
4.  `$ python main.py`
