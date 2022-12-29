import requests, time, os, datetime, json, threading, random, urllib.parse
from websocket import create_connection

class Client():
    def __init__(self, authToken, uuid, wallet="demo", currency="Crypto IDX"):
        self.headers = {'accept-encoding': 'gzip, deflate', 'accept-language': 'en-US,en;q=0.9', 'authorization-token': authToken, 'cache-control': 'no-cache, no-store, must-revalidate', 'cookie': 'authtoken='+authToken+'; device_id='+uuid+'; device_type=web', 'device-id': uuid, 'device-type': 'web', 'origin': 'https://stockity.id', 'referer': 'https://stockity.id/', 'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-site', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36', 'user-timezone': 'Asia/Bangkok'}
        self.accountWallet= wallet; self.currency = currency; self.history = []; self.lastSend=time.time(); self.ref=1
        for i in self.getAssets()["assets"]:
            if i["name"] == self.currency:self.assetRic=i["ric"]
        self.wsApi = create_connection("wss://ws.stockity.id/?v=2&vsn=2.0.0",header=self.headers)
        self.wsPoll = create_connection("wss://as.stockity.id/",header=self.headers)
        threading.Thread(target=self.hook,daemon=True).start()
        threading.Thread(target=self.pollingMarket,daemon=True).start()
        self.phxJoin()
        print("[ OPERATION ] BOT STARTED...")

    def getLast(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        return requests.get("https://api.stockity.id/candles/v1/"+self.assetRic+"/"+str(now)+"T00:00:00/60?locale=id",headers=self.headers).json()["data"]

    def getHistory(self):
        return requests.get("https://api.stockity.id/bo-deals-history/v3/deals/trade?type="+self.accountWallet+"&locale=en",headers=self.headers).json()["data"]

    def getAssets(self):
        return requests.get("https://api.stockity.id/platform/private/v3/assets/gold?locale=id",headers=self.headers).json()["data"]

    def parseBidTime(self, m=1):
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:00")
        bid = datetime.datetime.strptime(now, "%d/%m/%Y %H:%M:%S")+datetime.timedelta(minutes=m)
        return str(int(time.mktime(bid.timetuple())))

    def getBid(self, status, amount):
        if int(datetime.datetime.now().strftime("%S")) < 30:bidTime=self.parseBidTime()
        else:bidTime=self.parseBidTime(2)
        self.sendWs('{"topic":"bo","event":"create","payload":{"amount":'+str(amount*100)+',"ric":"'+self.assetRic+'","created_at":'+str(int(time.time()))+',"deal_type":"'+self.accountWallet+'","expire_at":'+bidTime+',"option_type":"turbo","tournament_id":null,"trend":"'+status+'","is_state":false},"ref":"~~","join_ref":"~~"}')

    def sendWs(self, data):
        self.wsApi.send(data.replace("~~",str(self.ref)))
        self.ref+= 1; self.lastSend = time.time()

    def phxJoin(self):
        self.sendWs('{"topic":"account","event":"phx_join","payload":{},"ref":"~~","join_ref":"~~"}')
        self.sendWs('{"topic":"user","event":"phx_join","payload":{},"ref":"~~","join_ref":"~~"}')
        self.sendWs('{"topic":"bo","event":"phx_join","payload":{},"ref":"~~","join_ref":"~~"}')
        self.sendWs('{"topic":"cfd_zero_spread","event":"phx_join","payload":{},"ref":"~~","join_ref":"~~"}')
        self.sendWs('{"topic":"tournament","event":"phx_join","payload":{},"ref":"~~","join_ref":"~~"}')
        self.sendWs('{"topic":"asset:'+self.assetRic+'","event":"phx_join","payload":{},"ref":"~~","join_ref":"~~"}')

    def pollingMarket(self):
        self.wsPoll.send('{"action":"subscribe","rics":["'+self.assetRic+'"]}')
        tempData={}; reset=False
        while True:
            data = json.loads(self.wsPoll.recv())
            if "assets" in data["data"][0]:
                timex = data["data"][0]["assets"][0]["created_at"].split(":")[-1].split(".")[0]
                rate = data["data"][0]["assets"][0]["rate"]
                if timex == "01":
                    if reset:
                        if tempData["open"] > tempData["close"]:tempData["stat"]="put"
                        elif tempData["open"] < tempData["close"]:tempData["stat"]="call"
                        else:tempData["stat"]="balance"
                        self.history.append(tempData)
                        print("[ OPERATION ] CANDLE: "+tempData["stat"].upper())
                        tempData={}; reset=False
                    if tempData == {}:tempData["low"]=rate;tempData["high"]=rate;tempData["open"]=rate
                    else:tempData["low"]=min(rate,tempData["low"]);tempData["high"]=max(rate,tempData["high"])
                elif timex == "00" and tempData != {}:
                    if reset == False:reset=True
                    tempData["low"]=min(rate,tempData["low"]);tempData["high"]=max(rate,tempData["high"]);tempData["close"]=rate
                elif tempData != {}:tempData["low"]=min(rate,tempData["low"]);tempData["high"]=max(rate,tempData["high"])

    def hook(self):
        stop = False
        while True:
            data = json.loads(self.wsApi.recv())
            if data["event"] == "opened":
                print("[ OPERATION ] CREATED DEAL AMOUNT: "+str(int(data["payload"]["amount"]/100)))
            elif data["event"] == "asset_changed_v1":
                print("[ OPERATION ] ASSET RATE CHANGED: "+str(data["payload"]["trading_tools_settings"]["standard"]["payment_rate_standard"])+"%")
            elif data["event"] == "balance_changed":
                self.balance = int(data["payload"]["amount"]/100)
                print("[ OPERATION ] BALANCE: "+str(int(data["payload"]["amount"]/100)))
            if time.time() - self.lastSend > 35:
                print("[ OPERATION ] PHOENIX HEARTBEAT")
                self.sendWs('{"topic":"phoenix","event":"heartbeat","payload":{},"ref":"~~"}')
                self.wsPoll.send('{"topic":"phoenix","event":"heartbeat","payload":{}}')
                  
                    
