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
    PEPPER = "INTARIAN_PEPPER_ROOT"

PARAMS = {
    Product.PEPPER: {
        # Linear fair-value model:  fair_value(t) = day_intercept + SLOPE * timestamp
        # Slope fitted from 3-day history: Pepper drifts ~1000 pts over 999_900 ticks
        "slope": 1000 / 999900,   # ≈ 0.001001 pts per timestamp unit
        # Day intercepts (starting price at timestamp=0 for each day).
        # Day -2: ~10000, Day -1: ~11000, Day 0: ~12000
        # At runtime we don't know the day, so we track it via traderData.
        "day_intercepts": {-2: 10000, -1: 11000, 0: 12000},
        "volume_limit": 80,
    },
}

class Trader:
    def __init__(self, params=None):
        if params is None:
            params = PARAMS
        self.params = params
        self.LIMIT = {
            Product.PEPPER: 80,
        }

    def _pepper_fair_value(self, timestamp: int, order_depth, traderObject: dict) -> float:
        p = self.params[Product.PEPPER]
        slope = p["slope"]

        prev_ts = traderObject.get("prev_timestamp", -1)
        day_idx = traderObject.get("day_idx", None)

        if timestamp < prev_ts:
            day_idx += 1
            traderObject["day_idx"] = day_idx

        # Bootstrap: on first tick, infer intercept from mid-price
        if day_idx is None:
            if order_depth.buy_orders and order_depth.sell_orders:
                mid = (max(order_depth.buy_orders) + min(order_depth.sell_orders)) / 2
                inferred_intercept = mid - slope * timestamp
                # snap to nearest known intercept
                known = p["day_intercepts"]
                day_idx = min(known.keys(), key=lambda d: abs(known[d] - inferred_intercept))
                day_idx = [-2, -1, 0].index(day_idx)
            else:
                day_idx = 0  # fallback
            traderObject["day_idx"] = day_idx

        traderObject["prev_timestamp"] = timestamp
        day = [-2, -1, 0][min(day_idx, 2)]
        return p["day_intercepts"][day] + slope * timestamp

    def run(self, state: TradingState):
        traderObject = {}
        if state.traderData != None and state.traderData != "":
            traderObject = jsonpickle.decode(state.traderData)

        result = {}

        if Product.PEPPER in self.params and Product.PEPPER in state.order_depths:

            order_depth = state.order_depths[Product.PEPPER]
            position = state.position.get(Product.PEPPER, 0)

            fair_value = self._pepper_fair_value(state.timestamp, order_depth, traderObject)
            limit = self.LIMIT[Product.PEPPER]
            
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
            my_bid_price = int(round(min(best_bid + 1, fair_value - 1)))
            my_ask_price = int(round(max(best_ask - 1, fair_value + 1)))
            buy_quantity = limit - position
            sell_quantity = -limit - position 
            if buy_quantity > 0 :
                orders.append(Order(Product.PEPPER, my_bid_price, buy_quantity))
                
            if sell_quantity < 0:
                orders.append(Order(Product.PEPPER, my_ask_price, sell_quantity))

            result[Product.PEPPER] = orders
        traderData = jsonpickle.encode(traderObject)
        conversions = 0
        
        return result, conversions, traderData
    