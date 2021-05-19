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
    for days in range(0,30,1):
        HistDate = (int(round((datetime.now() - timedelta(days=days)).timestamp())))
        hist_startDate = str(int(round(((datetime.now() - timedelta(days=days)).timestamp()) * 1000)))
        hist_symbol = Symbol
        hist_needExtendedHoursData = True
        hist_endDate = str(int(round(datetime.now().timestamp() * 1000)))
        HistDate = (int(round((datetime.now()).timestamp())))
        HistYear = datetime.fromtimestamp(HistDate).year
        HistMonth = datetime.fromtimestamp(HistDate).month
        HistDay = datetime.fromtimestamp(HistDate).day
        NumbDays = date(HistYear,HistMonth,HistDay).isoweekday()    
        if NumbDays <= 5:
            X_DayMA = TDSession.Historical_Endpoint(symbol=hist_symbol, 
                                                    start_date=hist_startDate,
                                                    end_date=hist_endDate,
                                                    extended_hours=hist_needExtendedHoursData
                                                    )
        else:
            False

