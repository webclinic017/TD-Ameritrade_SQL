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
HistoricalContent = TDSession.Historical_Endpoint(symbol=symbol)
#Create_Database = TDSession.cursor()
#Create_Table = TDSession.createTable()
#importData = TDSession.dataImport_Table()