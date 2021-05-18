from config import client_id,accntNmber,password,redirect_uri
from Stream import TDStreamerClient
from urllib.parse import urlparse
from datetime import datetime
from datetime import timedelta
import urllib.parse
import urllib3
import uuid
import os
import json
import requests
import dateutil.parser
import time
import csv
import pandas as pd
import numpy as np
import os
from os import path
from openpyxl import load_workbook




class TDClient():

    def __init__(self,**kwargs):
        self.config = {'consumer_id': client_id,
                       'account_number': accntNmber,
                       'account_password': password,
                       'api_endpoint': 'https://api.tdameritrade.com',
                       'redirect_uri': redirect_uri,
                       'resource': 'https://api.tdameritrade.com',
                       'api_version': '/v1',
                       'cache_state': True,
                       'authenticaiton_url': 'https://auth.tdameritrade.com',
                       'auth_endpoint': 'https://auth.tdameritrade.com' + '/auth?',
                       'token_endpoint': 'https://api.tdameritrade.com' + '/v1' + '/oauth2/token',
                       'refresh_enabled': True
                       }
        self.endpoint_arguments = {
                                   'get_user_principals': {'fields': ['streamerSubscriptionKeys', 'streamerConnectionInfo', 'preferences', 'surrogateIds']}
                                  }
        for key in kwargs:
            if key not in self.config:
                print('Warning: the argument {} is an unknown argument'.format(key))
                raise KeyError('Invalid Argument Name.')
        self.config.update(kwargs.items())
        self.state_manager('init')
        self.authstate = False
    def __repr__(self):
        if self.state['loggedin']:
            logged_in_state = 'True'
        else:
            logged_in_state = 'False'
        str_representation = '<TDAmeritrade Client (logged_in = {}, authorized = {})>'.format(logged_in_state, self.authstate)
        return str_representation
    def headers(self, mode=None, token=None) -> dict:
        token = self.state['access_token']
        headers = {'Authorization': 'Bearer {token}'.format(token = self.state['access_token'])}
        if mode == 'application/json':
            headers['Content-Type'] = 'application/json'
        if mode == 'json':
            headers['Content-Type'] = 'application/json'
        return headers
    def api_endpoint(self, endpoint: str, resource: str = None) -> str:
        if resource:
            parts = [resource, self.config['api_version'], endpoint]
        else:
            parts = [self.config['api_endpoint'], self.config['api_version'], endpoint]
        return '/'.join(parts)
    def state_manager(self, action):
        initialized_state = {'access_token': None,
                             'refresh_token': None,
                             'access_token_expires_at': 0,
                             'refresh_token_expires_at': 0,
                             'authorization_url': None,
                             'redirect_code': None,
                             'token_scope': '',
                             'loggedin': False}
        #dir_path = os.path.dirname(os.path.realpath(__file__))
        dir_path = r'C:\SourceCode\FOREX_TD-AmeritradeAPI\TD-Ameritrade_SQL'
        filename = 'TDAmeritradeState.json'
        file_path = os.path.join(dir_path, filename)
        if action == 'init':
            self.state = initialized_state
            if self.config['cache_state'] and os.path.isfile(file_path):
                with open(file_path, 'r') as fileHandle:
                    self.state.update(json.load(fileHandle))
            elif not self.config['cache_state'] and os.path.isfile(os.path.join(dir_path,filename)):
                os.remove(file_path)
        elif action == 'save' and self.config['cache_state']:
            with open(file_path, 'w') as fileHandle:
                json_string = {key:self.state[key] for key in initialized_state}
                json.dump(json_string, fileHandle)
    def login(self):
        if self.config['cache_state']:
            if self.silent_sso():
                self.authstate = 'Authenticated'
                return True
        self.authstate = 'Authenticated'
        payload = {'response_type':'code',
                   'redirect_uri':'http://localhost/',
                   'client_id':self.config['consumer_id'] + '@AMER.OAUTHAP'}
        params = urllib.parse.urlencode(payload)
        url = self.config['auth_endpoint'] + params
        self.state['authorization_url'] = url
        print('Please go to url provided authorize your account: {}'.format(self.state['authorization_url']))
        my_response = input('Paste the full URL redirect here: ')
        self.state['redirect_code'] = my_response
        self.grab_access_token()
    def logout(self):
        self.state_manager('init')
    def grab_access_token(self):
        url_dict = urllib.parse.parse_qs(self.state['redirect_code'])
        url_values = list(url_dict.values())
        url_code = url_values[0][0]
        data = {'grant_type':'authorization_code',
                'client_id':self.config['consumer_id'],
                'access_type':'offline',
                'code':url_code,
                'redirect_uri':'http://localhost/'
               }
        print(url_code)
        token_response = requests.post(url = self.config['token_endpoint'], data=data, verify=True)
        print(token_response)
        self.token_save(token_response)
        if token_response and token_response.ok:
            self.state_manager('save')
    def silent_sso(self):
        if self.token_seconds(token_type='access_token') > 0:
            return True
        elif self.token_seconds(token_type='refresh_token') <= 0:
            return False
        elif self.state['refresh_token'] and self.token_refresh():
            return True
        return False
    def token_refresh(self):
        data = {'grant_type':'refresh_token',
                'client_id':self.config['consumer_id'] + '@AMER.OAUTHAP',
                'refresh_token':self.state['refresh_token'],
                'access_type':'offline'
               }
        response = requests.post(url = self.config['token_endpoint'], data=data, verify=True) 
        if response.status_code == 401:
            print('The Credentials you passed through are invalid.')
            return False
        elif response.status_code == 400:
            print('Validation was unsuccessful.')
            return False
        elif response.status_code == 500:
            print('The TD Server is experiencing an error, please try again later.')
            return False
        elif response.status_code == 403:
            print("You don't have access to this resource, cannot authenticate.")
            return False
        elif response.status_code == 503:
            print("The TD Server can't respond, please try again later.")
            return False
        else:
            self.token_save(response)
            self.state_manager('save')
            return True
    def token_save(self, response):
        json_data = response.json()
        if 'access_token' not in json_data:
            self.logout()
            return False
        self.state['access_token'] = json_data['access_token']
        self.state['refresh_token'] = json_data['refresh_token']
        self.state['loggedin'] = True
        self.state['access_token_expires_at'] = time.time() + int(json_data['expires_in'])
        self.state['refresh_token_expires_at'] = time.time() + int(json_data['refresh_token_expires_in'])
        return True
    def token_seconds(self, token_type = 'access_token'):
        if token_type == 'access_token':
            if not self.state['access_token'] or time.time() >= self.state['access_token_expires_at']:
                return 0
            token_exp = int(self.state['access_token_expires_at'] - time.time())
        elif token_type == 'refresh_token':
            if not self.state['refresh_token'] or time.time() >= self.state['refresh_token_expires_at']:
                return 0
            token_exp = int(self.state['refresh_token_expires_at'] - time.time())
        return token_exp
    def token_validation(self, nseconds = 5):
        if self.token_seconds() < nseconds and self.config['refresh_enabled']:
            self.token_refresh()
    def _create_token_timestamp(self, token_timestamp = None):
        token_timestamp = datetime.strptime(token_timestamp, "%Y-%m-%dT%H:%M:%S%z")
        token_timestamp = int(token_timestamp.timestamp()) * 1000
        return token_timestamp
# CREATE STREAMING SESSION
    def validate_arguments(self, endpoint=None, parameter_name=None, parameter_argument=None):
        parameters_dictionary = self.endpoint_arguments[endpoint]
        parameter_possible_arguments = parameters_dictionary[parameter_name]
        if type(parameter_argument) is list:
            validation_result = [
                argument not in parameter_possible_arguments for argument in parameter_argument]
            if any(validation_result):
                print('\nThe value you passed through is not valid, please choose one of the following valid values: {} \n'.format(
                    ' ,'.join(parameter_possible_arguments)))
                raise ValueError('Invalid Value.')
            elif not any(validation_result):
                return True
        elif parameter_argument not in parameter_possible_arguments:
            print('\nThe value you passed through is not valid, please choose one of the following valid values: {} \n'.upper(
            ).format(' ,'.join(parameter_possible_arguments)))
            raise ValueError('Invalid Value.')
        elif parameter_argument in parameter_possible_arguments:
            return True
    def prepare_arguments_list(self, parameter_list=None):
        if type(parameter_list) is list:
            delimeter = ','
            parameter_list = delimeter.join(parameter_list)
        return parameter_list
    def get_quotes(self, instruments=None):
        self.token_validation()
        merged_headers = self.headers()
        instruments = self.prepare_arguments_list(parameter_list=instruments)
        data = {'apikey': self.config['consumer_id'],
                'symbol': instruments}
        endpoint = '/marketdata/quotes'
        url = self.api_endpoint(endpoint)
        return requests.get(url=url, headers=merged_headers, params=data, verify=True).json()
    def get_user_principals(self, fields=None):
        self.token_validation()
        self.validate_arguments(endpoint='get_user_principals',parameter_name='fields', parameter_argument=fields)
        merged_headers = self.headers()
        fields = self.prepare_arguments_list(parameter_list=fields)
        endpoint = '/userprincipals'
        data = {'fields': fields}
        url = self.api_endpoint(endpoint)
        return requests.get(url=url, headers=merged_headers, params=data, verify=True).json()
    def create_streaming_session(self):
        userPrincipalsResponse = self.get_user_principals(fields = ['streamerConnectionInfo'])
        tokenTimeStamp = userPrincipalsResponse['streamerInfo']['tokenTimestamp']
        socket_url = userPrincipalsResponse['streamerInfo']['streamerSocketUrl']
        tokenTimeStampAsMs = self._create_token_timestamp(token_timestamp=tokenTimeStamp)
        print(tokenTimeStamp, socket_url,tokenTimeStampAsMs)
        credentials = {'userid':userPrincipalsResponse['accounts'][0]['accountId'],
                       'token':userPrincipalsResponse['streamerInfo']['token'],
                       'company':userPrincipalsResponse['accounts'][0]['company'],
                       'segment':userPrincipalsResponse['accounts'][0]['segment'],
                       'cddomain':userPrincipalsResponse['accounts'][0]['accountCdDomainId'],
                       'usergroup':userPrincipalsResponse['streamerInfo']['userGroup'],
                       'accesslevel':userPrincipalsResponse['streamerInfo']['accessLevel'],
                       'authorized':'Y',
                       'timestamp':int(tokenTimeStampAsMs),
                       'appid':userPrincipalsResponse['streamerInfo']['appId'],
                       'acl':userPrincipalsResponse['streamerInfo']['acl'],
                     }
        streaming_session = TDStreamerClient(websocket_url=socket_url, user_principal_data=userPrincipalsResponse,credentials=credentials)
        return streaming_session
#WATCHLIST
    def multiple_symbol_watchlist(self, symbols=None):
        #os.chdir('C:\SourceCode\FOREX_TD-AmeritradeAPI\TD-Ameritrade_SQL')
        with open('WatchList.csv', newline='') as watchlist:
            WatchList = csv.reader(watchlist, delimiter=',')
            for Symbol in WatchList:
                symbols = Symbol
                return symbols
    def Historical_Endpoint(self, 
                            symbol:str=None, 
                            period_type:str=None,
                            period:int=None,
                            frequency_type:str=None,
                            frequency:int=None,
                            end_date:str=None,
                            extended_hours:bool=False):
        historicalEndpoint = r'https://api.tdameritrade.com/v1/marketdata/{}/pricehistory'.format(symbol)
        merged_headers = self.headers()
        historicalPayload = {'apikey':client_id,
                             'period': period,
                             'periodType': period_type,
                             'endDate': end_date,
                             'frequency': frequency,
                             'frequencyType': frequency_type,
                             'needExtendedHoursData': extended_hours
                             }
        historicalContent = requests.get(url=historicalEndpoint, headers=merged_headers, params=historicalPayload)
        historicalData = historicalContent.json()
        print(historicalContent)
        print(historicalData)
        '''
        #print(historicalData)
        for ticker in symbol:
            Symbol = historicalData['symbol']
            Open = historicalData['candles'][0]['open']
            High = historicalData['candles'][0]['high']
            Low = historicalData['candles'][0]['low']
            Close = historicalData['candles'][0]['close']
            Volume = historicalData['candles'][0]['volume']
            DateTime = historicalData['candles'][0]['datetime'] / 1000
            Day_time = datetime.fromtimestamp(DateTime).strftime('%Y-%m-%d')
            OHLC = [Symbol, Day_time, Open, High, Low, Close, Volume]
        print(OHLC)
        '''
#Account Info
    def accounts(self, accntNmber=None):
        AccntPayload = {'fields':'positions',
                        'apikey':client_id
                       }
        merged_headers = self.headers()
        getAccntsEndpoint = r'https://api.tdameritrade.com/v1/accounts/{}'.format(accntNmber)
        AccntContent = requests.get(url=getAccntsEndpoint, headers=merged_headers, params=AccntPayload)
        AccntPositions = AccntContent.json()
        return AccntPositions
    def BuyingPower(self,accntNmber=None):
        accntInfo = self.accounts(accntNmber)
        buyingPower = accntInfo['securitiesAccount']['projectedBalances']['availableFunds']
        buyingPower = float(buyingPower)
        return buyingPower
    def accntAssets(self,accntNmber=None,symbol=None):
        accntInfo = self.accounts(accntNmber=accntNmber)
        assets = {}
        lenAssets = len(symbol)
        try:
            for i in range(lenAssets):
                assets[i] = accntInfo['securitiesAccount']['positions'][i]['instrument']['symbol']  
                data = assets.values()
                Positions = list(data)
        except IndexError:
            'N/A'
        return Positions
    def assetQuantity(self,accntNmber=None,symbol=None):
        accntInfo = self.accounts(accntNmber=accntNmber)
        quantity = {}
        lenAssets = len(symbol)
        try:
            for i in range(lenAssets):
                quantity[i] = accntInfo['securitiesAccount']['positions'][i]['longQuantity']  
                data = quantity.values()
                Quantity = list(data)
        except IndexError:
            'N/A'
        return Quantity
    def TDA_Portfolio(self, symbol, accntNmber):
        Assets = self.accntAssets(accntNmber=accntNmber, symbol=symbol)
        Positions = self.assetQuantity(accntNmber=accntNmber, symbol=symbol)
        dfAssets = pd.DataFrame(Assets)
        dfPositions = pd.DataFrame(Positions)
        dfPortfolio = dfAssets.merge(dfPositions, left_index=True, right_index=True)
        dfPortfolio.rename(columns={'0_x':'Ticker','0_y':'Quantity'}, inplace=True)
        return dfPortfolio
    def TDA_Watchlists(self, accntNmber=None):
        WatchlistPayload = {'apikey':client_id}
        merged_headers = self.headers()
        getWatchlistEndpoint = r'https://api.tdameritrade.com/v1/accounts/{}/watchlists/{}'.format(accntNmber,1466022388)
        WatchlistContent = requests.get(url=getWatchlistEndpoint, headers=merged_headers, params=WatchlistPayload)
        Watchlist = WatchlistContent.json()
        return Watchlist
#Orders
    def shareNum_buy(self, positions=None, position=None):
        quotePrice = self.readStream(position=position)      
        quotePrice = [float(value) for value in quotePrice.values()]
        if quotePrice <= [1.00]:
            shares = 300
        elif quotePrice <= [2.00]:
            shares = 200
        elif quotePrice <= [3.00]:
            shares = 100
        elif quotePrice <= [4.00]:
            shares = 50
        elif quotePrice <= [5.00]:
            shares = 20
        elif quotePrice <= [6.00]:
            shares = 10
        else:
            shares = 0
        return shares
    def BuyMarketOrder(self, shares:str, ticker:str):
        Order = {'orderType': 'MARKET',
                 'session': 'NORMAL',
                 'duration': 'DAY',
                 'orderStrategyType': 'SINGLE',
                 'orderLegCollection': [{'instruction': 'Buy',
                                                        'quantity': shares,
                                                        'instrument': {'symbol': ticker,
                                                                       'assetType': 'EQUITY'
                                                                      }
                                        }
                                       ]
                }
        placeOrder = json.dumps(Order)
        return placeOrder
    def SellMarketOrder(self, shares:str, ticker:str):
        Order = {'orderType': 'MARKET',
                 'session': 'NORMAL',
                 'duration': 'DAY',
                 'orderStrategyType': 'SINGLE',
                 'orderLegCollection': [{'instruction': 'Sell',
                                                        'quantity': shares,
                                                        'instrument': {'symbol': ticker,
                                                                       'assetType': 'EQUITY'
                                                                      }
                                        }
                                       ]
                }
        sellPositions = json.dumps(Order, indent=4)
        return sellPositions
    def place_order(self, accntNmber=None, mode=None, shares=None, ticker=None):
        headers = self.headers(mode='json')
        orderData = self.BuyMarketOrder(shares=shares, ticker=ticker)
        print(orderData)
        orderEndpoint = r'https://api.tdameritrade.com/v1/accounts/{}/orders'.format(accntNmber)
        PlaceOrder = requests.post(url=orderEndpoint, headers=headers, data=orderData)
        return PlaceOrder
    def sellPositions(self, accntNmber=None, mode=None, shares=None, ticker=None):
        headers = self.headers(mode='json')
        orderData = self.SellMarketOrder(shares=shares, ticker=ticker)
        print(orderData)
        orderEndpoint = r'https://api.tdameritrade.com/v1/accounts/{}/orders'.format(accntNmber)
        SellOrder = requests.post(url=orderEndpoint, headers=headers, data=orderData)
        return SellOrder
    def getOrders(self, accntNmber=None):
        fromEnteredTime = (datetime.now() - timedelta(hours=120)).strftime('%Y-%m-%d')
        toEnteredTime = time.strftime('%Y-%m-%d', time.localtime())
        OrdersPayload = {
                         'apikey':client_id,
                         'fromEnteredTime':fromEnteredTime,
                         'toEnteredTime':toEnteredTime,
                         'maxResults':10,
                         'status':'FILLED'
                       }
        merged_headers = self.headers()
        getOrdersEndpoint = r'https://api.tdameritrade.com/v1/accounts/{}/orders'.format(accntNmber)
        ordersContent = requests.get(url=getOrdersEndpoint, headers=merged_headers, params=OrdersPayload)
        orders = ordersContent.json()
        return orders


   



        


            



        
            
      

