import pandas as pd
from binance import Client
from utils import secrets

# map string inputs into Binance variables
interval_map = {
    '1min' : Client.KLINE_INTERVAL_1MINUTE,
    '3min' : Client.KLINE_INTERVAL_3MINUTE,
    '5min' : Client.KLINE_INTERVAL_5MINUTE,
    '15min' : Client.KLINE_INTERVAL_15MINUTE,
    '1hr' : Client.KLINE_INTERVAL_1HOUR,
    '4hr' : Client.KLINE_INTERVAL_4HOUR,
    '8hr' : Client.KLINE_INTERVAL_8HOUR,
    '12hr': Client.KLINE_INTERVAL_12HOUR,
    '1wk' : Client.KLINE_INTERVAL_1WEEK,
}

client = Client(api_key=secrets.APIKEY, api_secret=secrets.SECRETKEY)

def fetchBinance(asset, time_frame, start_date, end_date):
    # file name used as an id for a specific asset and specific time frame
    # using file name helps avoid sending API request for data previously fetched
    file_name = f'{asset}_{time_frame}_{start_date}-{end_date}_raw'
    try:
        df = pd.read_csv(f'data/{file_name}.csv')
    except:
        df = client.get_historical_klines(
                        f'{asset}USDT',
                        interval=interval_map[time_frame],
                        start_str=start_date,
                        end_str=end_date
                    )

        # columns come by default with the Biance API call
        df = pd.DataFrame(data=df,
                        columns=['openTime', 'open', 'high', 'low', 'close', 'volume', 'closeTime', 'quoteAssetVolume', 
                                    'numOfTrades', 'takerBuyBaseAssetVolume', 'takerBuyQuoteAssetVolume', '_'])

        df.to_csv(f'data/{file_name}.csv')
        df = pd.read_csv(f'data/{file_name}.csv')

    return df