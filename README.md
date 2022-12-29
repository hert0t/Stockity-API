# Stockity-API

## REQUIREDMENT ##
- authtoken, deviceid (you can inspect by browser)
- german / london / spain vps ( FAST SPEED )
- pip install websocket-client


## EXAMPLE USAGE ##
- BET BUY/SELL
```PY
from lib import Client
client = Client("your_authtoken", "your_device_id", wallet="demo", currency="Crypto IDX")
time.sleep(3) # need time starting first connection
status = client.getBid("call", 14000)

# STATUS: 'call' for buy, 'put' for sell.
# CURRENCY: pair currency (u can get list by https://github.com/hert0t/Binomo-API/blob/main/asset.json).
```

## BINOMO ##
https://github.com/hert0t/Binomo-API

## OLYMPTRADE API ##
https://github.com/hert0t/OlympTrade-API
