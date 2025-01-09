import os
import time
from datetime import datetime
import logging
import pandas as pd
from binance.client import Client
from binance.enums import *

from Logger import *

api_key = ''
secret_key = ''

# CONFIGURAÇÕES
STOCK_CODE = "SOL"
OPERATION_CODE = "SOLBRL"
CANDLE_PERIOD = Client.KLINE_INTERVAL_15MINUTE
TRADED_QUANTITY = 1

# Define o logger
logging.basicConfig(
    filename='logs/trading_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class BinanceTraderBot():
    def __init__(self, stock_code, operation_code, traded_quantity, traded_percentage, candle_period):
        self.stock_code = stock_code
        self.operation_code = operation_code
        self.traded_quantity = traded_quantity
        self.traded_percentage = traded_percentage
        self.candle_period = candle_period
        self.client_binance = Client(api_key, secret_key)
        self.updateAllData()
        print('Robo Trader iniciado...')

    def updateAllData(self):
        self.account_data = self.getUpdatedAccountData()
        self.last_stock_account_balance = self.getLastStockAccountBalance()
        self.actual_trade_position = self.getActualTradePosition()
        self.stock_data = self.getStockData_ClosePrice_OpenTime()

    def getUpdatedAccountData(self):
        return self.client_binance.get_account()  # Busca infos da conta

    def getLastStockAccountBalance(self):
        for stock in self.account_data['balances']:
            if stock['asset'] == self.stock_code:
                in_wallet_amount = stock['free']
        return float(in_wallet_amount)

    def getActualTradePosition(self):
        """Checa se a posição atual é comprada ou vendida"""
        if self.last_stock_account_balance > 0.001:
            return True  # Comprado
        else:
            return False  # Vendido

    def getStockData_ClosePrice_OpenTime(self):
        """Busca os dados do ativo no período"""
        # Busca dados na Binance dos últimos 1000 períodos
        candles = self.client_binance.get_klines(
            symbol=self.operation_code,
            interval=self.candle_period,
            limit=500
        )

        # Transforma em um DataFrame Pandas
        prices = pd.DataFrame(candles)

        # Renomeia as colunas baseada na Documentação da Binance
        prices.columns = ["open_time", "open_price", "high_price", "low_price", "close_price",
                          "volume", "close_time", "quote_asset_volume", "number_of_trades",
                          "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume"]

        # Pode-se apenas os indicadores que queremos para esse modelo
        return prices

    def getStockData_ClosePrice_OpenTime(self):
        """Busca os dados do ativo no período"""
        # Busca dados na Binance dos últimos 1000 períodos
        candles = self.client_binance.get_klines(
            symbol=self.operation_code,
            interval=self.candle_period,
            limit=1000
        )

        # Transforma em um DataFrame Pandas
        prices = pd.DataFrame(candles)

        # Renomeia as colunas baseada na Documentação da Binance
        prices.columns = ["open_time", "open_price", "high_price", "low_price", "close_price",
                          "volume", "close_time", "quote_asset_volume", "number_of_trades",
                          "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume"]

        # Pega apenas os indicadores que queremos para esse modelo
        prices = prices[["close_price", "open_time"]]

        # Corrige o tempo de fechamento
        prices['open_time'] = pd.to_datetime(prices['open_time'], unit='ms').dt.tz_localize('UTC')
        # Converte para o fuso horário UTC -3
        prices['open_time'] = prices['open_time'].dt.tz_convert('America/Sao_Paulo')

        return prices

    def getMovingAverageTradeStrategy(self, fast_window=7, slow_window=40):
        """Executa a estratégia de média móvel"""
        # Calcula as Médias Móveis Rápida e Lenta
        self.stock_data['ma_fast'] = self.stock_data['close_price'].rolling(window=fast_window).mean()  # Média Rápida
        self.stock_data['ma_slow'] = self.stock_data['close_price'].rolling(window=slow_window).mean()  # Média Lenta

        # Pega as últimas Moving Average
        last_ma_fast = self.stock_data['ma_fast'].iloc[-1]  # iloc[-1] pega o último dado do array.
        last_ma_slow = self.stock_data['ma_slow'].iloc[-1]

        if last_ma_fast > last_ma_slow:
            ma_trade_decision = True  # Compra
        else:
            ma_trade_decision = False  # Vende

        # Imprime informações sobre a execução da estratégia
        print('Estratégia executada: Moving Average')
        print(f'({self.operation_code})\n | Última Média Rápida: {last_ma_fast:.3f}\n | Última Média Lenta: {last_ma_slow:.3f}')
        print(f'Decisão de posição: {"Comprar" if ma_trade_decision else "Vender"}')

        return ma_trade_decision

    def printWallet(self):
        """Imprime toda a carteira"""
        for stock in self.account_data["balances"]:
            if float(stock["free"]) > 0:
                print(stock)

    def printStock(self):
        """Imprime o ativo definido na classe"""
        for stock in self.account_data["balances"]:
            if stock['asset'] == self.stock_code:
                print(stock)

    def printBrl(self):
        """Imprime os ativos em BRL"""
        for stock in self.account_data["balances"]:
            if stock["asset"] == "BRL":
                print(stock)

    def getWallet(self):
        """Retorna toda a carteira"""
        for stock in self.account_data["balances"]:
            if float(stock["free"]) > 0:
                return stock

    def getStock(self):
        """Retorna o ativo definido na classe"""
        for stock in self.account_data["balances"]:
            if stock['asset'] == self.stock_code:
                return stock

    def buyStock(self):
        """Compra a ação"""
        if self.actual_trade_position == False:  # Se a posição for vendida
            order_buy = self.client_binance.create_order(
                symbol=self.operation_code,
               side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=self.traded_quantity
            )
            self.actual_trade_position = True  # Define posição como comprada
            createLogOrder(order_buy)  # Cria um log
            return order_buy  # Retorna a ordem
        else:
            logging.warning('Erro ao comprar')
            print('Erro ao comprar')
            return False

    def sellStock(self):
        """Vende a ação"""
        if self.actual_trade_position == True:  # Se a posição for comprada
            order_sell = self.client_binance.create_order(
                symbol=self.operation_code,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=self.traded_quantity
            )
            self.actual_trade_position = False  # Define posição como vendida
            createLogOrder(order_sell)  # Cria um log
            return order_sell  # Retorna a ordem
        else:
            logging.warning('Erro ao vender')
            print('Erro ao vender')
            return False

    def execute(self):
        # Atualiza todos os dados
        self.updateAllData()

        print(f'Executado ({datetime.now().strftime("%Y-%m-%d %H:%M:%S")})')
        print(f'Posição atual: {"Comprado" if self.actual_trade_position else "Vendido"}')
        print(f'Balanço atual: {self.last_stock_account_balance} ({self.stock_code})')

        # Executa a estratégia de média móvel
        ma_trade_decision = self.getMovingAverageTradeStrategy()

        # Neste caso, a decisão final será a mesma da estratégia móvel.
        self.last_trade_decision = ma_trade_decision

        # Se a posição for vendida (false) e a decisão for de compra (true), compra o ativo
        if self.actual_trade_position == False and self.last_trade_decision == True:
            self.printStock()
            self.printBrl()
            self.buyStock()
            time.sleep(2)
            self.updateAllData()
            self.printStock()
            self.printBrl()
        # Se a posição for comprada (true) e a decisão for de venda (false), vende o ativo
        elif self.actual_trade_position == True and self.last_trade_decision == False:
            # Vende o ativo
            self.printStock()
            self.printBrl()
            self.sellStock()
            time.sleep(2)  # Espera 2 segundos
            self.updateAllData()
            self.printStock()
            self.printBrl()
        else:
            # Nenhuma ação necessária
            pass

MaTrader = BinanceTraderBot(STOCK_CODE, OPERATION_CODE, TRADED_QUANTITY, 100, CANDLE_PERIOD)
while(1):
    MaTrader.execute()
    time.sleep(60)

