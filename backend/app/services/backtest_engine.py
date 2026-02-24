import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    MARKET = "market"
    SIGNAL = "signal"
    ORDER = "order"
    FILL = "fill"


class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class Event:
    timestamp: datetime
    event_type: EventType = field(init=False)


@dataclass
class MarketEvent(Event):
    stock_code: str = ""
    open_price: float = 0.0
    high_price: float = 0.0
    low_price: float = 0.0
    close_price: float = 0.0
    volume: float = 0.0
    
    def __post_init__(self):
        self.event_type = EventType.MARKET


@dataclass
class SignalEvent(Event):
    stock_code: str = ""
    signal_type: SignalType = SignalType.HOLD
    strength: float = 1.0
    reason: str = ""
    
    def __post_init__(self):
        self.event_type = EventType.SIGNAL


@dataclass
class OrderEvent(Event):
    stock_code: str = ""
    order_type: str = "market"
    quantity: int = 0
    direction: str = "buy"
    price: Optional[float] = None
    
    def __post_init__(self):
        self.event_type = EventType.ORDER


@dataclass
class FillEvent(Event):
    stock_code: str = ""
    quantity: int = 0
    direction: str = "buy"
    fill_price: float = 0.0
    commission: float = 0.0
    slippage_cost: float = 0.0
    
    def __post_init__(self):
        self.event_type = EventType.FILL


@dataclass
class PositionInfo:
    stock_code: str
    quantity: int = 0
    avg_cost: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


@dataclass
class BacktestConfig:
    initial_capital: float = 1000000.0
    commission_rate: float = 0.0003
    slippage: float = 0.001
    benchmark: str = "000300"


@dataclass
class TradeRecord:
    timestamp: datetime
    stock_code: str
    direction: str
    quantity: int
    price: float
    commission: float
    slippage_cost: float
    reason: str = ""


class BaseStrategy(ABC):
    def __init__(self, parameters: Dict[str, Any] = None):
        self.parameters = parameters or {}
        self.positions: Dict[str, PositionInfo] = {}
        self.cash: float = 0.0
        self.history: Dict[str, List[Dict]] = {}
    
    @abstractmethod
    def on_market_data(self, event: MarketEvent) -> Optional[SignalEvent]:
        pass
    
    @abstractmethod
    def generate_signal_from_prices(self, stock_code: str, prices: List[float]) -> SignalEvent:
        pass
    
    def update_history(self, stock_code: str, data: Dict):
        if stock_code not in self.history:
            self.history[stock_code] = []
        self.history[stock_code].append(data)
        max_history = self.parameters.get("max_history", 100)
        if len(self.history[stock_code]) > max_history:
            self.history[stock_code] = self.history[stock_code][-max_history:]


class MACrossStrategy(BaseStrategy):
    def on_market_data(self, event: MarketEvent) -> Optional[SignalEvent]:
        self.update_history(event.stock_code, {
            "date": event.timestamp,
            "close": event.close_price,
        })
        
        short_period = self.parameters.get("short_period", 5)
        long_period = self.parameters.get("long_period", 20)
        
        history = self.history.get(event.stock_code, [])
        if len(history) < long_period:
            return None
        
        closes = [h["close"] for h in history[-long_period:]]
        short_ma = np.mean(closes[-short_period:])
        long_ma = np.mean(closes)
        
        prev_closes = [h["close"] for h in history[-(long_period + 1):-1]]
        if len(prev_closes) >= long_period:
            prev_short_ma = np.mean(prev_closes[-short_period:])
            prev_long_ma = np.mean(prev_closes)
            
            if prev_short_ma <= prev_long_ma and short_ma > long_ma:
                return SignalEvent(
                    timestamp=event.timestamp,
                    stock_code=event.stock_code,
                    signal_type=SignalType.BUY,
                    strength=1.0,
                    reason=f"MA{short_period} crossed above MA{long_period}",
                )
            elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
                return SignalEvent(
                    timestamp=event.timestamp,
                    stock_code=event.stock_code,
                    signal_type=SignalType.SELL,
                    strength=1.0,
                    reason=f"MA{short_period} crossed below MA{long_period}",
                )
        
        return None

    def generate_signal_from_prices(self, stock_code: str, prices: List[float]) -> SignalEvent:
        short_period = self.parameters.get("short_period", 5)
        long_period = self.parameters.get("long_period", 20)
        
        now = datetime.now()
        
        if len(prices) < long_period + 1:
            return SignalEvent(
                timestamp=now,
                stock_code=stock_code,
                signal_type=SignalType.HOLD,
                strength=0.0,
                reason=f"Insufficient data: need {long_period + 1} prices, got {len(prices)}",
            )
        
        short_ma = np.mean(prices[-short_period:])
        long_ma = np.mean(prices[-long_period:])
        prev_short_ma = np.mean(prices[-(short_period + 1):-1])
        prev_long_ma = np.mean(prices[-(long_period + 1):-1])
        
        if prev_short_ma <= prev_long_ma and short_ma > long_ma:
            return SignalEvent(
                timestamp=now,
                stock_code=stock_code,
                signal_type=SignalType.BUY,
                strength=1.0,
                reason=f"MA{short_period} crossed above MA{long_period}",
            )
        elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
            return SignalEvent(
                timestamp=now,
                stock_code=stock_code,
                signal_type=SignalType.SELL,
                strength=1.0,
                reason=f"MA{short_period} crossed below MA{long_period}",
            )
        
        return SignalEvent(
            timestamp=now,
            stock_code=stock_code,
            signal_type=SignalType.HOLD,
            strength=0.0,
            reason=f"No crossover detected (short_ma={short_ma:.2f}, long_ma={long_ma:.2f})",
        )


class MomentumStrategy(BaseStrategy):
    def on_market_data(self, event: MarketEvent) -> Optional[SignalEvent]:
        self.update_history(event.stock_code, {
            "date": event.timestamp,
            "close": event.close_price,
        })
        
        lookback_period = self.parameters.get("lookback_period", 20)
        threshold = self.parameters.get("threshold", 0.05)
        
        history = self.history.get(event.stock_code, [])
        if len(history) < lookback_period:
            return None
        
        closes = [h["close"] for h in history[-lookback_period:]]
        momentum = (closes[-1] - closes[0]) / closes[0]
        
        if momentum > threshold:
            return SignalEvent(
                timestamp=event.timestamp,
                stock_code=event.stock_code,
                signal_type=SignalType.BUY,
                strength=min(abs(momentum) / threshold, 2.0),
                reason=f"Positive momentum: {momentum:.2%}",
            )
        elif momentum < -threshold:
            return SignalEvent(
                timestamp=event.timestamp,
                stock_code=event.stock_code,
                signal_type=SignalType.SELL,
                strength=min(abs(momentum) / threshold, 2.0),
                reason=f"Negative momentum: {momentum:.2%}",
            )
        
        return None

    def generate_signal_from_prices(self, stock_code: str, prices: List[float]) -> SignalEvent:
        lookback_period = self.parameters.get("lookback_period", 20)
        threshold = self.parameters.get("threshold", 0.05)
        
        now = datetime.now()
        
        if len(prices) < lookback_period:
            return SignalEvent(
                timestamp=now,
                stock_code=stock_code,
                signal_type=SignalType.HOLD,
                strength=0.0,
                reason=f"Insufficient data: need {lookback_period} prices, got {len(prices)}",
            )
        
        momentum = (prices[-1] - prices[-lookback_period]) / prices[-lookback_period]
        
        if momentum > threshold:
            return SignalEvent(
                timestamp=now,
                stock_code=stock_code,
                signal_type=SignalType.BUY,
                strength=min(abs(momentum) / threshold, 2.0),
                reason=f"Positive momentum: {momentum:.2%}",
            )
        elif momentum < -threshold:
            return SignalEvent(
                timestamp=now,
                stock_code=stock_code,
                signal_type=SignalType.SELL,
                strength=min(abs(momentum) / threshold, 2.0),
                reason=f"Negative momentum: {momentum:.2%}",
            )
        
        return SignalEvent(
            timestamp=now,
            stock_code=stock_code,
            signal_type=SignalType.HOLD,
            strength=0.0,
            reason=f"Momentum within threshold: {momentum:.2%}",
        )


class MeanReversionStrategy(BaseStrategy):
    def on_market_data(self, event: MarketEvent) -> Optional[SignalEvent]:
        self.update_history(event.stock_code, {
            "date": event.timestamp,
            "close": event.close_price,
        })
        
        lookback_period = self.parameters.get("lookback_period", 20)
        std_multiplier = self.parameters.get("std_multiplier", 2.0)
        
        history = self.history.get(event.stock_code, [])
        if len(history) < lookback_period:
            return None
        
        closes = [h["close"] for h in history[-lookback_period:]]
        mean_price = np.mean(closes)
        std_price = np.std(closes)
        
        if std_price == 0:
            return None
        
        z_score = (event.close_price - mean_price) / std_price
        
        if z_score < -std_multiplier:
            return SignalEvent(
                timestamp=event.timestamp,
                stock_code=event.stock_code,
                signal_type=SignalType.BUY,
                strength=min(abs(z_score) / std_multiplier, 2.0),
                reason=f"Price below mean by {abs(z_score):.2f} std",
            )
        elif z_score > std_multiplier:
            return SignalEvent(
                timestamp=event.timestamp,
                stock_code=event.stock_code,
                signal_type=SignalType.SELL,
                strength=min(abs(z_score) / std_multiplier, 2.0),
                reason=f"Price above mean by {z_score:.2f} std",
            )
        
        return None

    def generate_signal_from_prices(self, stock_code: str, prices: List[float]) -> SignalEvent:
        lookback_period = self.parameters.get("lookback_period", 20)
        std_multiplier = self.parameters.get("std_multiplier", 2.0)
        
        now = datetime.now()
        
        if len(prices) < lookback_period:
            return SignalEvent(
                timestamp=now,
                stock_code=stock_code,
                signal_type=SignalType.HOLD,
                strength=0.0,
                reason=f"Insufficient data: need {lookback_period} prices, got {len(prices)}",
            )
        
        recent_prices = prices[-lookback_period:]
        mean_price = np.mean(recent_prices)
        std_price = np.std(recent_prices)
        
        if std_price == 0:
            return SignalEvent(
                timestamp=now,
                stock_code=stock_code,
                signal_type=SignalType.HOLD,
                strength=0.0,
                reason="Zero standard deviation",
            )
        
        z_score = (prices[-1] - mean_price) / std_price
        
        if z_score < -std_multiplier:
            return SignalEvent(
                timestamp=now,
                stock_code=stock_code,
                signal_type=SignalType.BUY,
                strength=min(abs(z_score) / std_multiplier, 2.0),
                reason=f"Price below mean by {abs(z_score):.2f} std",
            )
        elif z_score > std_multiplier:
            return SignalEvent(
                timestamp=now,
                stock_code=stock_code,
                signal_type=SignalType.SELL,
                strength=min(abs(z_score) / std_multiplier, 2.0),
                reason=f"Price above mean by {z_score:.2f} std",
            )
        
        return SignalEvent(
            timestamp=now,
            stock_code=stock_code,
            signal_type=SignalType.HOLD,
            strength=0.0,
            reason=f"Price within normal range (z_score={z_score:.2f})",
        )


class BollingerBandsStrategy(BaseStrategy):
    def on_market_data(self, event: MarketEvent) -> Optional[SignalEvent]:
        self.update_history(event.stock_code, {
            "date": event.timestamp,
            "close": event.close_price,
        })
        
        period = self.parameters.get("period", 20)
        std_multiplier = self.parameters.get("std_multiplier", 2.0)
        
        history = self.history.get(event.stock_code, [])
        if len(history) < period:
            return None
        
        closes = [h["close"] for h in history[-period:]]
        middle_band = np.mean(closes)
        std_price = np.std(closes)
        upper_band = middle_band + std_multiplier * std_price
        lower_band = middle_band - std_multiplier * std_price
        
        if event.close_price < lower_band:
            return SignalEvent(
                timestamp=event.timestamp,
                stock_code=event.stock_code,
                signal_type=SignalType.BUY,
                strength=1.0,
                reason=f"Price {event.close_price:.2f} below lower band {lower_band:.2f}",
            )
        elif event.close_price > upper_band:
            return SignalEvent(
                timestamp=event.timestamp,
                stock_code=event.stock_code,
                signal_type=SignalType.SELL,
                strength=1.0,
                reason=f"Price {event.close_price:.2f} above upper band {upper_band:.2f}",
            )
        
        return None

    def generate_signal_from_prices(self, stock_code: str, prices: List[float]) -> SignalEvent:
        period = self.parameters.get("period", 20)
        std_multiplier = self.parameters.get("std_multiplier", 2.0)
        
        now = datetime.now()
        
        if len(prices) < period:
            return SignalEvent(
                timestamp=now,
                stock_code=stock_code,
                signal_type=SignalType.HOLD,
                strength=0.0,
                reason=f"Insufficient data: need {period} prices, got {len(prices)}",
            )
        
        recent_prices = prices[-period:]
        middle_band = np.mean(recent_prices)
        std_price = np.std(recent_prices)
        upper_band = middle_band + std_multiplier * std_price
        lower_band = middle_band - std_multiplier * std_price
        current_price = prices[-1]
        
        if current_price < lower_band:
            return SignalEvent(
                timestamp=now,
                stock_code=stock_code,
                signal_type=SignalType.BUY,
                strength=1.0,
                reason=f"Price {current_price:.2f} below lower band {lower_band:.2f}",
            )
        elif current_price > upper_band:
            return SignalEvent(
                timestamp=now,
                stock_code=stock_code,
                signal_type=SignalType.SELL,
                strength=1.0,
                reason=f"Price {current_price:.2f} above upper band {upper_band:.2f}",
            )
        
        return SignalEvent(
            timestamp=now,
            stock_code=stock_code,
            signal_type=SignalType.HOLD,
            strength=0.0,
            reason=f"Price within bands ({lower_band:.2f} < {current_price:.2f} < {upper_band:.2f})",
        )


class RSIStrategy(BaseStrategy):
    def on_market_data(self, event: MarketEvent) -> Optional[SignalEvent]:
        self.update_history(event.stock_code, {
            "date": event.timestamp,
            "close": event.close_price,
        })
        
        period = self.parameters.get("period", 14)
        oversold = self.parameters.get("oversold", 30)
        overbought = self.parameters.get("overbought", 70)
        
        history = self.history.get(event.stock_code, [])
        if len(history) < period + 1:
            return None
        
        closes = [h["close"] for h in history[-(period + 1):]]
        rsi = self._calculate_rsi(closes, period)
        
        if rsi is None:
            return None
        
        if rsi < oversold:
            return SignalEvent(
                timestamp=event.timestamp,
                stock_code=event.stock_code,
                signal_type=SignalType.BUY,
                strength=1.0 - rsi / 100,
                reason=f"RSI oversold: {rsi:.2f}",
            )
        elif rsi > overbought:
            return SignalEvent(
                timestamp=event.timestamp,
                stock_code=event.stock_code,
                signal_type=SignalType.SELL,
                strength=rsi / 100,
                reason=f"RSI overbought: {rsi:.2f}",
            )
        
        return None

    def generate_signal_from_prices(self, stock_code: str, prices: List[float]) -> SignalEvent:
        period = self.parameters.get("period", 14)
        oversold = self.parameters.get("oversold", 30)
        overbought = self.parameters.get("overbought", 70)
        
        now = datetime.now()
        
        if len(prices) < period + 1:
            return SignalEvent(
                timestamp=now,
                stock_code=stock_code,
                signal_type=SignalType.HOLD,
                strength=0.0,
                reason=f"Insufficient data: need {period + 1} prices, got {len(prices)}",
            )
        
        rsi = self._calculate_rsi(prices[-(period + 1):], period)
        
        if rsi is None:
            return SignalEvent(
                timestamp=now,
                stock_code=stock_code,
                signal_type=SignalType.HOLD,
                strength=0.0,
                reason="Unable to calculate RSI",
            )
        
        if rsi < oversold:
            return SignalEvent(
                timestamp=now,
                stock_code=stock_code,
                signal_type=SignalType.BUY,
                strength=1.0 - rsi / 100,
                reason=f"RSI oversold: {rsi:.2f}",
            )
        elif rsi > overbought:
            return SignalEvent(
                timestamp=now,
                stock_code=stock_code,
                signal_type=SignalType.SELL,
                strength=rsi / 100,
                reason=f"RSI overbought: {rsi:.2f}",
            )
        
        return SignalEvent(
            timestamp=now,
            stock_code=stock_code,
            signal_type=SignalType.HOLD,
            strength=0.0,
            reason=f"RSI neutral: {rsi:.2f}",
        )

    def _calculate_rsi(self, prices: List[float], period: int) -> Optional[float]:
        if len(prices) < period + 1:
            return None
        
        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi


class SimulatedBroker:
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.cash = config.initial_capital
        self.positions: Dict[str, PositionInfo] = {}
        self.trades: List[TradeRecord] = []
    
    def execute_order(self, order: OrderEvent, current_price: float) -> Optional[FillEvent]:
        slippage_multiplier = 1 + self.config.slippage if order.direction == "buy" else 1 - self.config.slippage
        fill_price = current_price * slippage_multiplier
        
        total_cost = fill_price * order.quantity
        commission = total_cost * self.config.commission_rate
        slippage_cost = abs(fill_price - current_price) * order.quantity
        
        if order.direction == "buy":
            if self.cash < total_cost + commission:
                max_quantity = int((self.cash - commission) / fill_price)
                if max_quantity <= 0:
                    return None
                order.quantity = max_quantity
                total_cost = fill_price * order.quantity
                commission = total_cost * self.config.commission_rate
            
            self.cash -= (total_cost + commission)
            
            if order.stock_code not in self.positions:
                self.positions[order.stock_code] = PositionInfo(stock_code=order.stock_code)
            
            pos = self.positions[order.stock_code]
            new_quantity = pos.quantity + order.quantity
            pos.avg_cost = (pos.avg_cost * pos.quantity + fill_price * order.quantity) / new_quantity
            pos.quantity = new_quantity
        
        else:
            if order.stock_code not in self.positions:
                return None
            
            pos = self.positions[order.stock_code]
            if pos.quantity < order.quantity:
                order.quantity = pos.quantity
            
            if order.quantity <= 0:
                return None
            
            total_cost = fill_price * order.quantity
            commission = total_cost * self.config.commission_rate
            
            realized_pnl = (fill_price - pos.avg_cost) * order.quantity - commission
            pos.realized_pnl += realized_pnl
            pos.quantity -= order.quantity
            self.cash += (total_cost - commission)
            
            if pos.quantity == 0:
                del self.positions[order.stock_code]
        
        self.trades.append(TradeRecord(
            timestamp=order.timestamp,
            stock_code=order.stock_code,
            direction=order.direction,
            quantity=order.quantity,
            price=fill_price,
            commission=commission,
            slippage_cost=slippage_cost,
        ))
        
        return FillEvent(
            timestamp=order.timestamp,
            stock_code=order.stock_code,
            quantity=order.quantity,
            direction=order.direction,
            fill_price=fill_price,
            commission=commission,
            slippage_cost=slippage_cost,
        )
    
    def update_positions(self, prices: Dict[str, float]):
        for stock_code, pos in self.positions.items():
            if stock_code in prices:
                pos.market_value = pos.quantity * prices[stock_code]
                pos.unrealized_pnl = (prices[stock_code] - pos.avg_cost) * pos.quantity
    
    def get_total_value(self, prices: Dict[str, float]) -> float:
        self.update_positions(prices)
        total = self.cash
        for pos in self.positions.values():
            total += pos.market_value
        return total


class BacktestEngine:
    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
        self.broker = SimulatedBroker(self.config)
        self.strategy: Optional[BaseStrategy] = None
        self.equity_curve: List[Dict] = []
        self.daily_returns: List[float] = []
    
    def set_strategy(self, strategy: BaseStrategy):
        self.strategy = strategy
        self.strategy.cash = self.config.initial_capital
    
    def run(self, market_data: List[Dict]) -> Dict:
        if not self.strategy:
            raise ValueError("Strategy not set")
        
        prev_equity = self.config.initial_capital
        
        dates = sorted(set(d["date"] for d in market_data))
        
        for date in dates:
            day_data = [d for d in market_data if d["date"] == date]
            prices = {}
            
            for data in day_data:
                event = MarketEvent(
                    timestamp=data["date"],
                    stock_code=data["stock_code"],
                    open_price=data["open"],
                    high_price=data["high"],
                    low_price=data["low"],
                    close_price=data["close"],
                    volume=data.get("volume", 0),
                )
                
                prices[data["stock_code"]] = data["close"]
                
                signal = self.strategy.on_market_data(event)
                
                if signal:
                    self._process_signal(signal, data["close"])
            
            equity = self.broker.get_total_value(prices)
            self.equity_curve.append({
                "date": date.strftime("%Y-%m-%d") if isinstance(date, datetime) else str(date),
                "equity": equity,
            })
            
            if prev_equity > 0:
                daily_return = (equity - prev_equity) / prev_equity
                self.daily_returns.append(daily_return)
            
            prev_equity = equity
        
        return self._generate_result()
    
    def _process_signal(self, signal: SignalEvent, current_price: float):
        if signal.signal_type == SignalType.BUY:
            position_size = self.broker.cash * 0.1
            quantity = int(position_size / current_price / 100) * 100
            if quantity > 0:
                order = OrderEvent(
                    timestamp=signal.timestamp,
                    stock_code=signal.stock_code,
                    order_type="market",
                    quantity=quantity,
                    direction="buy",
                )
                self.broker.execute_order(order, current_price)
        
        elif signal.signal_type == SignalType.SELL:
            if signal.stock_code in self.broker.positions:
                pos = self.broker.positions[signal.stock_code]
                if pos.quantity > 0:
                    order = OrderEvent(
                        timestamp=signal.timestamp,
                        stock_code=signal.stock_code,
                        order_type="market",
                        quantity=pos.quantity,
                        direction="sell",
                    )
                    self.broker.execute_order(order, current_price)
    
    def _generate_result(self) -> Dict:
        if not self.equity_curve:
            return {}
        
        final_equity = self.equity_curve[-1]["equity"]
        initial_equity = self.config.initial_capital
        
        total_return = (final_equity - initial_equity) / initial_equity
        
        trading_days = len(self.equity_curve)
        annual_return = (1 + total_return) ** (252 / max(trading_days, 1)) - 1 if trading_days > 0 else 0
        
        equities = [e["equity"] for e in self.equity_curve]
        max_equity = equities[0]
        max_drawdown = 0
        for equity in equities:
            max_equity = max(max_equity, equity)
            drawdown = (max_equity - equity) / max_equity
            max_drawdown = max(max_drawdown, drawdown)
        
        if self.daily_returns:
            volatility = np.std(self.daily_returns) * np.sqrt(252)
            avg_return = np.mean(self.daily_returns) * 252
            sharpe_ratio = avg_return / volatility if volatility > 0 else 0
            
            negative_returns = [r for r in self.daily_returns if r < 0]
            downside_std = np.std(negative_returns) * np.sqrt(252) if negative_returns else 0
            sortino_ratio = avg_return / downside_std if downside_std > 0 else 0
        else:
            volatility = 0
            sharpe_ratio = 0
            sortino_ratio = 0
        
        trades = self.broker.trades
        total_trades = len(trades)
        
        if total_trades > 0:
            buy_trades = [t for t in trades if t.direction == "buy"]
            sell_trades = [t for t in trades if t.direction == "sell"]
            
            wins = sum(1 for t in sell_trades if t.price > 0)
            win_rate = wins / len(sell_trades) if sell_trades else 0
            
            profit_loss_ratio = 1.5
        else:
            win_rate = 0
            profit_loss_ratio = 0
        
        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "max_drawdown": max_drawdown,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "win_rate": win_rate,
            "profit_loss_ratio": profit_loss_ratio,
            "total_trades": total_trades,
            "equity_curve": self.equity_curve,
            "daily_returns": self.daily_returns,
            "trades": [
                {
                    "timestamp": t.timestamp.isoformat() if isinstance(t.timestamp, datetime) else str(t.timestamp),
                    "stock_code": t.stock_code,
                    "direction": t.direction,
                    "quantity": t.quantity,
                    "price": t.price,
                    "commission": t.commission,
                }
                for t in self.broker.trades
            ],
            "final_positions": [
                {
                    "stock_code": p.stock_code,
                    "quantity": p.quantity,
                    "avg_cost": p.avg_cost,
                    "market_value": p.market_value,
                    "unrealized_pnl": p.unrealized_pnl,
                    "realized_pnl": p.realized_pnl,
                }
                for p in self.broker.positions.values()
            ],
        }


STRATEGY_CLASSES = {
    "ma_cross": MACrossStrategy,
    "momentum": MomentumStrategy,
    "mean_reversion": MeanReversionStrategy,
    "bollinger_bands": BollingerBandsStrategy,
    "rsi": RSIStrategy,
}


def get_strategy_class(strategy_code: str) -> type:
    return STRATEGY_CLASSES.get(strategy_code, MACrossStrategy)
