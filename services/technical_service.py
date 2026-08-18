import pandas as pd
import numpy as np

class TechnicalService:
    """Calculates deterministic technical indicators from historical OHLCV data."""

    @staticmethod
    def calculate_indicators(history_df):
        """
        history_df: pandas DataFrame with Open, High, Low, Close, Volume columns
        """
        if history_df is None or history_df.empty:
            return {
                "available": False,
                "reason": "Historical price data is unavailable"
            }

        try:
            df = history_df.copy()
            if isinstance(df.columns, pd.MultiIndex):
                # Flatten multi-index columns if yfinance returns multi-tier dataframe
                df.columns = [col[0] for col in df.columns]

            for col in ["Close", "High", "Low", "Open", "Volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            df = df.dropna(subset=["Close"]).sort_index()

            if len(df) < 5:
                return {
                    "available": False,
                    "reason": "Insufficient historical data points"
                }

            close = df["Close"]
            high = df["High"] if "High" in df.columns else close
            low = df["Low"] if "Low" in df.columns else close
            volume = df["Volume"] if "Volume" in df.columns else pd.Series(0, index=df.index)

            latest_price = float(close.iloc[-1])
            prev_price = float(close.iloc[-2]) if len(close) >= 2 else latest_price
            price_change_pct = ((latest_price - prev_price) / prev_price) * 100 if prev_price else 0.0

            # 1. Simple Moving Averages
            sma_20 = float(close.tail(20).mean()) if len(close) >= 20 else float(close.mean())
            sma_50 = float(close.tail(50).mean()) if len(close) >= 50 else float(close.mean())
            sma_100 = float(close.tail(100).mean()) if len(close) >= 100 else float(close.mean())
            sma_200 = float(close.tail(200).mean()) if len(close) >= 200 else float(close.mean())

            # 2. Exponential Moving Averages
            ema_12 = float(close.ewm(span=12, adjust=False).mean().iloc[-1]) if len(close) >= 12 else latest_price
            ema_26 = float(close.ewm(span=26, adjust=False).mean().iloc[-1]) if len(close) >= 26 else latest_price

            # 3. RSI (14 periods)
            delta = close.diff()
            gain = delta.where(delta > 0, 0.0)
            loss = (-delta.where(delta < 0, 0.0))
            avg_gain = gain.rolling(window=14, min_periods=5).mean()
            avg_loss = loss.rolling(window=14, min_periods=5).mean()

            rs = avg_gain / (avg_loss + 1e-10)
            rsi_series = 100 - (100 / (1 + rs))
            rsi_14 = float(rsi_series.dropna().iloc[-1]) if not rsi_series.dropna().empty else 50.0
            rsi_14 = max(0.0, min(100.0, rsi_14))

            # 4. MACD (12, 26, 9)
            macd_line = ema_12 - ema_26
            macd_series = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
            signal_series = macd_series.ewm(span=9, adjust=False).mean()
            macd_signal = float(signal_series.iloc[-1]) if not signal_series.empty else 0.0
            macd_hist = macd_line - macd_signal

            # 5. Bollinger Bands (20, 2)
            rolling_mean = close.rolling(window=20, min_periods=5).mean()
            rolling_std = close.rolling(window=20, min_periods=5).std()
            bb_middle = float(rolling_mean.iloc[-1]) if not rolling_mean.empty else latest_price
            bb_std = float(rolling_std.iloc[-1]) if not rolling_std.empty and not pd.isna(rolling_std.iloc[-1]) else 0.0
            bb_upper = bb_middle + (2 * bb_std)
            bb_lower = max(0.0, bb_middle - (2 * bb_std))

            # 6. Average True Range (ATR 14)
            tr1 = high - low
            tr2 = (high - close.shift()).abs()
            tr3 = (low - close.shift()).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr_series = tr.rolling(window=14, min_periods=5).mean()
            atr_14 = float(atr_series.dropna().iloc[-1]) if not atr_series.dropna().empty else max(1.0, latest_price * 0.02)

            # 7. Support & Resistance Levels (Pivot Points / Recent Swings)
            recent_lows = low.tail(60).nsmallest(5)
            recent_highs = high.tail(60).nlargest(5)
            support_1 = float(recent_lows.iloc[0]) if not recent_lows.empty else round(latest_price * 0.95, 2)
            support_2 = float(recent_lows.iloc[1]) if len(recent_lows) > 1 else round(latest_price * 0.90, 2)
            resistance_1 = float(recent_highs.iloc[0]) if not recent_highs.empty else round(latest_price * 1.05, 2)
            resistance_2 = float(recent_highs.iloc[1]) if len(recent_highs) > 1 else round(latest_price * 1.10, 2)

            # 8. 52-Week High/Low
            high_52 = float(high.tail(252).max()) if len(high) > 0 else latest_price
            low_52 = float(low.tail(252).min()) if len(low) > 0 else latest_price

            # 9. Deterministic Technical Score (0-100)
            score = 50.0

            # Trend vs Moving Averages (+/- 25 pts)
            if latest_price > sma_20:
                score += 8
            else:
                score -= 6

            if latest_price > sma_50:
                score += 10
            else:
                score -= 8

            if latest_price > sma_200:
                score += 7
            else:
                score -= 6

            # RSI Signals (+/- 15 pts)
            if 40 <= rsi_14 <= 60:
                score += 5  # Healthy neutral momentum
            elif 60 < rsi_14 <= 70:
                score += 12 # Strong bullish momentum
            elif rsi_14 > 70:
                score -= 5  # Overbought warning
            elif 30 <= rsi_14 < 40:
                score -= 6  # Weak momentum
            elif rsi_14 < 30:
                score += 8  # Oversold rebound potential

            # MACD Signals (+/- 10 pts)
            if macd_line > macd_signal:
                score += 8
            else:
                score -= 8

            # Price momentum over 1 month / 3 months (+/- 15 pts)
            if len(close) >= 22:
                month_return = ((latest_price - float(close.iloc[-22])) / float(close.iloc[-22])) * 100
                if month_return > 10:
                    score += 8
                elif month_return > 2:
                    score += 4
                elif month_return < -10:
                    score -= 8
                elif month_return < -2:
                    score -= 4

            technical_score = int(round(max(10, min(95, score))))

            # Interpretation
            if technical_score >= 75:
                trend_signal = "Bullish"
            elif technical_score <= 40:
                trend_signal = "Bearish"
            else:
                trend_signal = "Neutral"

            return {
                "available": True,
                "latest_price": round(latest_price, 2),
                "price_change_pct": round(price_change_pct, 2),
                "sma_20": round(sma_20, 2),
                "sma_50": round(sma_50, 2),
                "sma_100": round(sma_100, 2),
                "sma_200": round(sma_200, 2),
                "ema_12": round(ema_12, 2),
                "ema_26": round(ema_26, 2),
                "rsi_14": round(rsi_14, 1),
                "macd_line": round(macd_line, 2),
                "macd_signal": round(macd_signal, 2),
                "macd_histogram": round(macd_hist, 2),
                "bb_upper": round(bb_upper, 2),
                "bb_middle": round(bb_middle, 2),
                "bb_lower": round(bb_lower, 2),
                "atr_14": round(atr_14, 2),
                "support_1": round(support_1, 2),
                "support_2": round(support_2, 2),
                "resistance_1": round(resistance_1, 2),
                "resistance_2": round(resistance_2, 2),
                "high_52": round(high_52, 2),
                "low_52": round(low_52, 2),
                "technical_score": technical_score,
                "trend_signal": trend_signal,
            }

        except Exception as e:
            return {
                "available": False,
                "reason": f"Calculation error: {str(e)}"
            }
