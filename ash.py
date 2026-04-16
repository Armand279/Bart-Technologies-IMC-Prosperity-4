from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string



class Product:
    ASH= "ASH"
    

PARAMS = {
    Product.ASH:{
        "fair_value":10000,
        "std_dev":5.35,
        "volume_limit":80,
        z_score_limit:2}
    }


class Trader:
    __init__(self, params=None){
        if params==None:
            params=PARAMS
        self.params=PARAMS

    }

    def run(self, state: TradingState):
        result = {}
        if Product.ASH in self.params and Product.ASH in state.order_depths:
            order_depth = state.order_depths[Product.ASH]
            position = state.position.get(Product.ASH, 0)
            params = self.params[Product.ASH]
            fair_value= params["fair_value"]
            limit = params["volume_limit"]
            std_dev = params["std_dev"]
            z_score_limit=params["z_score_limit"]
            orders = []
            if len(order_depth.buy_orders) > 0 and len(order_depth.sell_orders) > 0:

                buy_quantity = limit - position
                sell_quantity = -limit - position

                best_bid = max(order_depth.buy_orders.keys())
                best_ask = min(order_depth.sell_orders.keys())

                z_best_bid= (best_bid-fair_value)/std_dev

                z_best_ask=(best_ask-fair_value)/std_dev

                while (buy_quantity>0 and z_best_ask<=-2 ):
                    orders.append(Order(ASH,best_bid, buy_quantity ))
                    del order_depth.buy_orders[best_bid]
                     best_bid = max(order_depth.buy_orders.keys())
                
                    z_best_bid= (best_bid-fair_value)/std_dev
                    


                while(sell_quantity and z_best_bid>=2):
                    orders.append(Order(ASH,best_ask, -sell_quantity))
                    del order_depth.buy_orders[best_ask]
                    best_ask = min(order_depth.sell_orders.keys())
                    z_best_ask=(best_ask-fair_value)/std_dev
                
                result[ASH]=orders
        
        return result