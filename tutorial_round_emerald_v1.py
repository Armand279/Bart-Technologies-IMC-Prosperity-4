from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import *
import jsonpickle
import numpy as np
import json
from typing import List, Dict, Tuple,Any
import string
import math
from typing import Dict, List, Tuple, Any
from json import JSONEncoder
import statistics

class Product:
    EMERALD = "EMERALDS"
    TOMATOES = "TOMATOES"

PARAMS = {
    Product.EMERALD: {
        "fair_value": 10000,
        "volume_limit": 80
    },
    Product.TOMATOES: {
        "volume_limit": 80,
        "fast_ema_window": 20,       # For the main fair value and Bollinger Bands
        "slow_ema_window": 50,       # For trend detection
        "std_dev_multiplier": 2.0,   # Bollinger Band width (k)
        "inventory_threshold": 15    # Position size to start skewing quotes
    },
}

class Trader:
    def __init__(self, params=None):
        if params is None:
            params = PARAMS
        self.params = params
        self.LIMIT = {
            Product.EMERALD: 80,
            Product.TOMATOES: 80,
        }

    def run(self, state: TradingState):
        traderObject = {}
        if state.traderData != None and state.traderData != "":
            traderObject = jsonpickle.decode(state.traderData)

        result = {}
        
        if Product.EMERALD in self.params and Product.EMERALD in state.order_depths:
            order_depth = state.order_depths[Product.EMERALD]
            position = state.position.get(Product.EMERALD, 0)
            
            fair_value = self.params[Product.EMERALD]["fair_value"]
            limit = self.LIMIT[Product.EMERALD]
            
            orders = []
            if len(order_depth.buy_orders) != 0:
                best_bid = max(order_depth.buy_orders.keys())
            else:
                best_bid = fair_value - 2 
            if len(order_depth.sell_orders) != 0:
                best_ask = min(order_depth.sell_orders.keys())
            else:
                best_ask = fair_value + 2 
            my_bid_price = best_bid + 1
            my_ask_price = best_ask - 1
            my_bid_price = min(my_bid_price, fair_value - 1)
            my_ask_price = max(my_ask_price, fair_value + 1)

            buy_quantity = limit - position
            sell_quantity = -limit - position 
            if buy_quantity > 0 :
                orders.append(Order(Product.EMERALD, my_bid_price, buy_quantity))
                
            if sell_quantity < 0:
                orders.append(Order(Product.EMERALD, my_ask_price, sell_quantity))

            result[Product.EMERALD] = orders

        if Product.TOMATOES in self.params and Product.TOMATOES in state.order_depths:
            order_depth = state.order_depths[Product.TOMATOES]
            position = state.position.get(Product.TOMATOES, 0)

            params = self.params[Product.TOMATOES]
            limit = params["volume_limit"]
            fast_window = params["fast_ema_window"]
            slow_window = params["slow_ema_window"]
            std_multiplier = params["std_dev_multiplier"]
            inventory_threshold = params["inventory_threshold"]
            
            orders = []
            
            if len(order_depth.buy_orders) > 0 and len(order_depth.sell_orders) > 0:
                best_bid = max(order_depth.buy_orders.keys())
                best_ask = min(order_depth.sell_orders.keys())

                past_prices = traderObject.get("tomato_mid_prices", [])

                mid_price = (best_bid + best_ask) / 2
                prev_mid = past_prices[-1] if past_prices else mid_price
                momentum = mid_price - prev_mid

                
                past_prices.append(mid_price)

                if len(past_prices) > fast_window:
                    past_prices.pop(0)
                traderObject["tomato_mid_prices"] = past_prices

                fast_ema = traderObject.get("tomato_fast_ema", mid_price)
                slow_ema = traderObject.get("tomato_slow_ema", mid_price)
                
                fast_alpha = 2 / (fast_window + 1)
                slow_alpha = 2 / (slow_window + 1)
                
                fast_ema = (mid_price * fast_alpha) + (fast_ema * (1 - fast_alpha))
                slow_ema = (mid_price * slow_alpha) + (slow_ema * (1 - slow_alpha))
                
                traderObject["tomato_fast_ema"] = fast_ema
                traderObject["tomato_slow_ema"] = slow_ema
                
                std_dev = 0
                if len(past_prices) >= 2: 
                    std_dev = statistics.stdev(past_prices)
                
                std_dev *= (1 + 0.3 * (std_dev / (statistics.mean(past_prices) + 1e-9)))

                upper_band = fast_ema + (std_multiplier * std_dev)
                lower_band = fast_ema - (std_multiplier * std_dev)

                buy_quantity = limit - position
                sell_quantity = -limit - position
                
                market_regime = 'SIDEWAYS'
                if fast_ema > slow_ema + 0.5: 
                    market_regime = 'UPTREND'
                elif fast_ema < slow_ema - 0.5:
                    market_regime = 'DOWNTREND'
                    
                if best_ask < lower_band and market_regime != 'DOWNTREND' and momentum < 0:
                    take_volume = min(buy_quantity, -order_depth.sell_orders[best_ask])
                    if take_volume > 0:
                        orders.append(Order(Product.TOMATOES, best_ask, take_volume))
                        buy_quantity -= take_volume
                
                if best_bid > upper_band and market_regime != 'UPTREND' and momentum > 0 :
                    take_volume = max(sell_quantity, -order_depth.buy_orders[best_bid])
                    if take_volume < 0:
                        orders.append(Order(Product.TOMATOES, best_bid, take_volume))
                        sell_quantity -= take_volume
                if buy_quantity > 0:
                    my_bid_price = min(best_bid + 1, math.floor(lower_band))
                    if position > inventory_threshold:
                        my_bid_price -= 1
                    orders.append(Order(Product.TOMATOES, my_bid_price, buy_quantity))

                if sell_quantity < 0:
                    my_ask_price = max(best_ask - 1, math.ceil(upper_band))
                    if position < -inventory_threshold:
                        my_ask_price += 1
                    orders.append(Order(Product.TOMATOES, my_ask_price, sell_quantity))

            result[Product.TOMATOES] = orders

        traderData = jsonpickle.encode(traderObject)
        conversions = 1
        
        return result, conversions, traderData