from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string

class Product:
    ASH = "ASH_COATED_OSMIUM"

PARAMS = {
    Product.ASH: {
        "fair_value": 10000,
        "std_dev": 5.35,
        "volume_limit": 80,
        "z_score_limit": 1,
        "mm_edge": 7,
    }
}

class Trader:
    def __init__(self, params=None):
        if params == None:
            params = PARAMS
        self.params = params

    def run(self, state: TradingState):
        result = {}
        if Product.ASH in self.params and Product.ASH in state.order_depths:
            order_depth = state.order_depths[Product.ASH]
            position = state.position.get(Product.ASH, 0)
            params = self.params[Product.ASH]
            fair_value = params["fair_value"]
            limit = params["volume_limit"]
            std_dev = params["std_dev"]
            z_score_limit = params["z_score_limit"]
            mm_edge = params["mm_edge"]
            orders = []
            buy_quantity = limit - position
            sell_quantity = -limit - position

            
            if len(order_depth.sell_orders) > 0:
                best_ask = min(order_depth.sell_orders.keys())
                z_best_ask = (best_ask - fair_value) / std_dev
                while (buy_quantity > 0 and z_best_ask <= -z_score_limit):
                    amount_buy = min(buy_quantity, -order_depth.sell_orders[best_ask])
                    orders.append(Order(Product.ASH, best_ask, amount_buy))
                    buy_quantity -= amount_buy
                    del order_depth.sell_orders[best_ask]
                    if not order_depth.sell_orders:
                        break
                    best_ask = min(order_depth.sell_orders.keys())
                    z_best_ask = (best_ask - fair_value) / std_dev

            if len(order_depth.buy_orders) > 0:
                best_bid = max(order_depth.buy_orders.keys())
                z_best_bid = (best_bid - fair_value) / std_dev
                while (sell_quantity < 0 and z_best_bid >= z_score_limit):
                    amount_sell = max(sell_quantity, -order_depth.buy_orders[best_bid])
                    orders.append(Order(Product.ASH, best_bid, amount_sell))
                    sell_quantity -= amount_sell
                    del order_depth.buy_orders[best_bid]
                    if not order_depth.buy_orders:
                        break
                    best_bid = max(order_depth.buy_orders.keys())
                    z_best_bid = (best_bid - fair_value) / std_dev
            
            # ── MAKER: passive quotes with remaining capacity ──────────────
            best_ask = min(order_depth.sell_orders) if order_depth.sell_orders else fair_value + mm_edge
            best_bid = max(order_depth.buy_orders)  if order_depth.buy_orders  else fair_value - mm_edge
            mm_ask = best_ask - 1
            mm_bid = best_bid + 1

            if buy_quantity > 0 and mm_bid < fair_value:
                orders.append(Order(Product.ASH, mm_bid, buy_quantity))


            if sell_quantity < 0 and mm_ask > fair_value:
                orders.append(Order(Product.ASH, mm_ask, sell_quantity))

            result[Product.ASH] = orders
        return result, 1, ""