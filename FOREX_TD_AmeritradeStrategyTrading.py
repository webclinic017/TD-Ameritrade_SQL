from Client_ import TDClient
from config import client_id, password, accntNmber, userName
from datetime import datetime
from datetime import timedelta
from datetime import date
import json
import os
import pandas as pd
import numpy as np
import time
import pprint
#initialize new session with accnt info and caching false
TDSession = TDClient(account_number = accntNmber,
                     account_password = password,
                     redirect_uri = 'http://localhost/',
                     consumer_id = client_id,
                     #cache_state = True
                     )
TDSession.login() 
print(TDSession.state['loggedin']) 
print(TDSession.authstate)
symbol = TDSession.multiple_symbol_watchlist()
for Symbol in symbol:
    hist_symbol = Symbol
    hist_period = 5
    hist_periodType = 'day'
    hist_frequencyType = 'minute'
    hist_frequency = 15
    hist_needExtendedHoursData = True
    #HistDate = (int(round((datetime.now() - timedelta(days=days)).timestamp())))
    #OHLC
    hist_endDate = str(int(round(datetime.now().timestamp() * 1000)))
    HistDate = (int(round((datetime.now()).timestamp())))
    HistYear = datetime.fromtimestamp(HistDate).year
    HistMonth = datetime.fromtimestamp(HistDate).month
    HistDay = datetime.fromtimestamp(HistDate).day
    NumbDays = date(HistYear,HistMonth,HistDay).isoweekday()
    X_DayMA = TDSession.Historical_Endpoint(symbol=hist_symbol, 
                                            period=hist_period,
                                            period_type=hist_periodType,
                                            frequency_type=hist_frequencyType,
                                            frequency=hist_frequency,
                                            end_date=hist_endDate,
                                            extended_hours=hist_needExtendedHoursData
                                            )

