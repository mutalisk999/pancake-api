import time

from web3 import Web3
from g import *
from utils import *


class BscApi:
    def __init__(self, url="https://bsc-dataseed.binance.org/"):
        self.url = url
        self.web3 = Web3(Web3.HTTPProvider(url))
        self.make_sure_api_connected()

    def is_connected(self):
        return self.web3.isConnected()

    def make_sure_api_connected(self):
        while True:
            if self.is_connected():
                break
            else:
                print("sleep 1 second and try to re-connect.......")
                time.sleep(1)
                self.web3 = Web3(Web3.HTTPProvider(self.url))

    def get_acct_balance(self, query_addr):
        self.make_sure_api_connected()
        balance = self.web3.eth.get_balance(query_addr)
        return balance

    def get_acct_erc20_token_balance(self, token_addr, query_addr):
        self.make_sure_api_connected()
        tokenContract = self.web3.eth.contract(token_addr, abi=Erc20TokenAbi)
        tokenBalance = tokenContract.functions \
            .balanceOf(query_addr).call()
        return tokenBalance

    def send_raw_transaction(self, signed_tx):
        self.make_sure_api_connected()
        tx_id = self.web3.eth.send_raw_transaction(signed_tx)
        return tx_id

    def sign_tx(self, unsigned_tx, priv_key):
        return self.web3.eth.account.sign_transaction(unsigned_tx, priv_key)

    # 需要将 approved contract 设定为 panRouter contract
    def approve(self, token_addr, approved_addr, approved_amount, gas_price, priv_key):
        self.make_sure_api_connected()
        tokenContract = self.web3.eth.contract(token_addr, abi=Erc20TokenAbi)
        sender_addr = calc_addr_from_key(priv_key)
        unsigned_tx = tokenContract.functions \
            .approve(approved_addr, approved_amount) \
            .buildTransaction({
            'from': sender_addr,
            'gasPrice': gas_price,
            'nonce': self.web3.eth.get_transaction_count(sender_addr),
        })

        signed_tx = self.sign_tx(unsigned_tx)
        tx_id = self.send_raw_transaction(signed_tx)
        return tx_id

    def get_reserves(self):
        self.make_sure_api_connected()
        lpContract = self.web3.eth.contract(LiquidityPairContract, abi=LiquidityPairAbi)
        reserve1, reserve2, block_timestamp_last = lpContract.functions \
            .getReserves().call()
        return reserve1, reserve2, block_timestamp_last

    # 用以估算可以兑换数量
    def get_amount_out(self, amount_in, reserve_in, reserve_out):
        self.make_sure_api_connected()
        routerContract = self.web3.eth.contract(PanCakeRouterContract, abi=PanCakeRouterAbi)
        amount_out = routerContract.functions \
            .getAmountOut(amount_in, reserve_in, reserve_out).call()
        return amount_out

    # 兑换
    # 用精确数量的token 甲 兑换出不少于多少数量的token 乙
    # 如果 买乙, 设置正向path (甲->乙)
    # 如果 卖乙, 设置逆向path (乙->甲), 相当于用乙买甲
    def swap_exact_token_for_tokens(self, amount_in, amount_out_min, path, gas_price, priv_key):
        self.make_sure_api_connected()
        routerContract = self.web3.eth.contract(PanCakeRouterContract, abi=PanCakeRouterAbi)
        sender_addr = calc_addr_from_key(priv_key)
        unsigned_tx = routerContract.functions \
            .swapExactTokensForTokens(amount_in, amount_out_min, path, sender_addr, (int(time.time()) + 1000000)) \
            .buildTransaction({
            'from': sender_addr,
            'gasPrice': gas_price,
            'nonce': self.web3.eth.get_transaction_count(sender_addr),
        })

        signed_tx = self.sign_tx(unsigned_tx)
        tx_id = self.send_raw_transaction(signed_tx)
        return tx_id
