import json
import datetime, time, sys
from requests_oauthlib import OAuth1Session
from abc import ABCMeta, abstractmethod

import os
from os.path import join,dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__),".env")
load_dotenv(dotenv_path)

CONSUMER_KEY = os.environ.get("CONSUMER_KEY")
CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
ACCESS_TOKKEN_SECRET = os.environ.get("ACCESS_TOKKEN_SECRET")

#tweet取得クラス
class TweetsGetter(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.session = OAuth1Session(CONSUMER_KEY,CONSUMER_SECRET,ACCESS_TOKEN,ACCESS_TOKKEN_SECRET)

    @abstractmethod
    def specifyUrlAndParams(self, keyword):
        """
        呼出し先 URL、パラメータを返す(このコメント消すとエラー発生)
        """

    @abstractmethod
    def pickupTweet(self, res_text, includeRetweet):
        """
        res_text からツイートを取り出し、配列にセットして返す
        """

    @abstractmethod
    def getLimitContext(self, res_text):
        """
        回数制限の情報を取得 （起動時）
        """

    def collect(self, total = -1, onlyText = False,includeRetweet = False):
        self.checkLimit()

        url, params = self.specifyUrlAndParams()
        params["include_rts"] = str(includeRetweet).lower()

        count = 0
        unavailableCount = 0
        while True:
            res = self.session.get(url, params = params)
            #コード503 : リクエストが多い。503が帰ってきたら次にリクエスト可能になるまでsleepさせる。
            if res.status_code == 503:
                raise Exception(f"Twitter APIエラー : {res.status_code}")
                unavailableCount += 1
                print(u"サービス利用不可 503")
                self.waitUntilReset(time.mktime(datetime.datetime.now().timetuple())) + 30
                continue
            #コード200 : リクエスト成功
            if res.status_code != 200:
                raise Exception(f"Twitter APIエラー : {res.status_code}")
            #帰ってきたjsonの中身が0->ループを抜ける. !0->処理。
            tweets = self.pickupTweet(json.loads(res.text))
            if len(tweets) == 0:
                break
            for tweet in tweets:
                if(("retweeted_status" in tweet) and (includeRetweet is False)):
                    pass
                else:
                    if onlyText is True:
                        yield tweet["text"]
                    else:
                        yield tweet
                    count += 1
                    if count % 100 == 0:
                        print(f"{count}件")
                    if total > 0 and count >= total:
                        return
            params["max_id"] = tweet["id"] -1

            #ヘッダー確認
            if("X-Rate-Limit-Remaining" in res.headers and "X-Rate-Limit-Reset" in res.headers):
                if(int(res.headers["X-Rate-Limit-Remaining"]) == 0):
                    self.waitUntilReset(int(res.headers["X-Rate-Limit-Reset"]))
                    self.checkLimit()

    #回数制限を問い合わせ、アクセス可能になるまで待つ
    def checkLimit(self):
        unavailableCount = 0
        while True:
            url = "https://api.twitter.com/1.1/application/rate_limit_status.json"
            res = self.session.get(url)

            if res.status_code == 503:
                if unavailableCount > 10:
                    raise Exception(f"Twitter APIエラー{res.status_code}")
                unavailableCount += 1
                print(u"サービス利用不可 503")
                self.waitUntilReset(time.mktime(datetime.datetime.now().timetuple()) + 30)
                continue
            unavailableCount = 0

            if res.status_code != 200:
                raise Exception(f"Twitter APIエラー{res.status_code}")

            remaining, reset = self.getLimitContext(json.loads(res.text))
            if(remaining == 0):
                self.waitUntilReset(reset)
            else:
                break

    #reset時間までsleep
    def waitUntilReset(self,reset):
        seconds = reset - time.mktime(datetime.datetime.now().timetuple())
        seconds = max(seconds, 0)
        print(f"\n 残り{seconds}秒")
        sys.stdout.flush()
        time.sleep(seconds + 10)

    @staticmethod
    def bySearch(keyword):
        return TweetsGetterBySearch(keyword)

    @staticmethod
    def byUser(screen_name):
        return TweetsGetterByUser(screen_name)

#キーワード検索クラス(継承：tweet取得クラス)
class TweetsGetterBySearch(TweetsGetter):
    def __init__(self, keyword):
        super(TweetsGetterBySearch, self).__init__()
        self.keyword = keyword

    #呼び出し先 URL,パラメータを返す
    def specifyUrlAndParams(self):
         url = "https://api.twitter.com/1.1/search/tweets.json"
         params = {"q":self.keyword,"count":100}
         return url,params

    #resツイートからツイートを取り出し、配列にセットして返す
    def pickupTweet(self, res_text):
        result = []
        for tweet in res_text["statuses"]:
            result.append(tweet)
        return result

    #回数制限の情報を取得
    def getLimitContext(self, res_text):
        remaining = res_text["resources"]["search"]["/search/tweets"]["remaining"]
        reset = res_text["resources"]["search"]["/search/tweets"]["reset"]
        return int(remaining), int(reset)

#ユーザー指定クラス(継承:tweet取得クラス)
class TweetsGetterByUser(TweetsGetter):
    def __init__(self, screen_name):
        super(TweetsGetterByUser, self).__init__()
        self.screen_name = screen_name

    def specifyUrlAndParams(self):
        url = "https://api.twitter.com/1.1/statuses/user_timeline.json"
        params = {"screen_name":self.screen_name,"count":200}
        return url, params

    def pickupTweet(self, res_text):
        results = []
        for tweet in res_text:
            results.append(tweet)
        return results

    def getLimitContext(self, res_text):
        remaining = res_text['resources']['statuses']['/statuses/user_timeline']['remaining']
        reset     = res_text['resources']['statuses']['/statuses/user_timeline']['reset']

        return int(remaining), int(reset)

if __name__ == "__main__":
    serch_text = ""

    print("モードを選択してください\n1.文字検索\n2.id検索")
    sel = int(input("番号入力>"))
    if(sel == 1):
        print("文字検索でデータを取得します。")
        search_text = input("検索キーワードを入力してください>")
        result = TweetsGetter.bySearch(search_text)
    elif(sel == 2):
        print("id検索でデータを取得します。")
        search_text = input("検索キーワードを入力してください>")
        result = TweetsGetter.byUser(search_text)
    else:
        print("正しい値を入力してください")
        sys.exit()

    for tweet in result.collect(total = 3000):
        file = open(f"{search_text}.txt","a")
        file.write(tweet["text"])
        file.flush()
        file.close()
