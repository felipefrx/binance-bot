import logging
from datetime import datetime

# Configurar o logger
logging.basicConfig(
    filename='logs/trading_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Printa e cria um log de ordem de compra ou venda.
# A partir do objeto retornado pela API da Binance
def createLogOrder(order):
    # Extraindo as informações necessárias
    side = order['side']
    type = order['type']
    quantity = order['executedQty']
    asset = order['symbol']
    price_per_unit = order['fills'][0]['price']
    currency = order['fills'][0]['commissionAsset']
    total_value = order['cummulativeQuoteQty']
    timestamp = order['transactTime']

    # Convertendo timestamp para data/hora legível
    datetime_transact = datetime.utcfromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')

    # Criando as mensagens para log
    log_message = (
        f"\n- ORDEM EXECUTADA: \n"
        f"Side: {side}\n"
        f"Ativo: {asset}\n"
        f"Quantidade: {quantity}\n"
        f"Preço por unidade: {price_per_unit}\n"
        f"Moeda da comissão: {currency}\n"
        f"Valor total: {total_value}\n"
        f"Timestamp: {datetime_transact}\n"
    )

    print_message = (
        f"\n- ORDEM EXECUTADA: \n"
        f"Side: {side}\n"
        f"Ativo: {asset}\n"
        f"Quantidade: {quantity}\n"
        f"Valor no momento: {price_per_unit}\n"
        f"Moeda: {currency}\n"
        f"Valor em {currency}: {total_value}\n"
        f"Type: {type}\n"
    )

    # Exibindo no console
    print(print_message)

    # Registrando no log
    logging.info(log_message)