from datetime import datetime, timezone

class ScoringEngine:
    """Multi-Factor Stock Scoring Engine combining 7 weighted financial pillars."""

    DEFAULT_WEIGHTS = {
        "fundamentals": 0.25,
        "technicals": 0.20,
        "valuation": 0.15,
        "momentum": 0.15,
        "sentiment": 0.10,
        "risk": 0.10,
        "liquidity": 0.05,
    }

    @classmethod
    def evaluate_stock(cls, fundamentals_data, technicals_data, news_sentiment_score=50, weights=None):
        w = weights or cls.DEFAULT_WEIGHTS

        # 1. Fundamental Score (0-100)
        fundamental_score = fundamentals_data.get("fundamental_score", 50) if fundamentals_data.get("available") else 50

        # 2. Technical Score (0-100)
        technical_score = technicals_data.get("technical_score", 50) if technicals_data.get("available") else 50

        # 3. Valuation Score (0-100)
        valuation_score = cls._compute_valuation_score(fundamentals_data)

        # 4. Momentum Score (0-100)
        momentum_score = cls._compute_momentum_score(technicals_data)

        # 5. News Sentiment Score (0-100)
        sentiment_score = max(0, min(100, int(news_sentiment_score)))

        # 6. Risk Score (0-100: Higher score = lower risk/more stable)
        risk_score, risk_label = cls._compute_risk_score(technicals_data, fundamentals_data)

        # 7. Liquidity Score (0-100)
        liquidity_score = cls._compute_liquidity_score(technicals_data)

        # Weighted Composite Score
        composite = (
            (fundamental_score * w["fundamentals"]) +
            (technical_score * w["technicals"]) +
            (valuation_score * w["valuation"]) +
            (momentum_score * w["momentum"]) +
            (sentiment_score * w["sentiment"]) +
            (risk_score * w["risk"]) +
            (liquidity_score * w["liquidity"])
        )
        overall_score = int(round(max(5, min(98, composite))))

        # Signal Classification
        if overall_score >= 85:
            signal = "Strong Buy"
            summary = "Excellent multi-factor profile with robust financial health, positive momentum, and manageable risk."
        elif overall_score >= 70:
            signal = "Buy"
            summary = "Constructive setup with favorable fundamentals and supportive technical structure."
        elif overall_score >= 55:
            signal = "Hold"
            summary = "Neutral risk/reward balance. Key indicators suggest holding existing positions while watching confirmation levels."
        elif overall_score >= 40:
            signal = "Reduce"
            summary = "Weak momentum or elevated valuation metrics suggest caution and risk management."
        else:
            signal = "Avoid"
            summary = "High volatility, adverse technical indicators, or deteriorating fundamental ratios."

        # Confidence rating
        data_completeness = 0
        if fundamentals_data.get("available"):
            data_completeness += 40
        if technicals_data.get("available"):
            data_completeness += 40
        if news_sentiment_score != 50:
            data_completeness += 20
        confidence = min(95, max(45, int(round((data_completeness * 0.5) + (abs(overall_score - 50) * 0.8)))))

        # Identified Strengths & Risks
        strengths, risks = cls._extract_strengths_and_risks(
            fundamentals_data, technicals_data, valuation_score, momentum_score, sentiment_score, risk_label
        )

        return {
            "overall_score": overall_score,
            "signal": signal,
            "confidence": confidence,
            "risk_label": risk_label,
            "summary": summary,
            "factor_scores": {
                "fundamentals": fundamental_score,
                "technicals": technical_score,
                "valuation": valuation_score,
                "momentum": momentum_score,
                "sentiment": sentiment_score,
                "risk": risk_score,
                "liquidity": liquidity_score,
            },
            "weights": w,
            "strengths": strengths,
            "risks": risks,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    @staticmethod
    def _compute_valuation_score(fundamentals):
        if not fundamentals or not fundamentals.get("available"):
            return 50
        raw = fundamentals.get("raw_metrics", {})
        pe = raw.get("pe")
        pb = raw.get("pb")
        div_yield = raw.get("dividend_yield")
        score = 50.0

        if pe is not None:
            if 0 < pe <= 20:
                score += 20
            elif 20 < pe <= 35:
                score += 10
            elif pe > 65:
                score -= 15

        if pb is not None:
            if 0 < pb <= 3.0:
                score += 15
            elif pb > 10.0:
                score -= 12

        if div_yield and div_yield > 0.02:
            score += 10

        return int(round(max(10, min(95, score))))

    @staticmethod
    def _compute_momentum_score(technicals):
        if not technicals or not technicals.get("available"):
            return 50
        score = 50.0
        rsi = technicals.get("rsi_14", 50)
        sma50 = technicals.get("sma_50")
        price = technicals.get("latest_price", 0)

        if 55 <= rsi <= 68:
            score += 20 # Strong sustainable trend
        elif rsi > 75:
            score += 5  # Strong but overbought
        elif rsi < 35:
            score -= 18 # Severe downward drift

        if sma50 and price > sma50:
            score += 15
        elif sma50 and price < sma50:
            score -= 15

        return int(round(max(10, min(95, score))))

    @staticmethod
    def _compute_risk_score(technicals, fundamentals):
        score = 50.0
        if not technicals or not technicals.get("available"):
            return 50, "Moderate Risk"

        high52 = technicals.get("high_52", 0)
        low52 = technicals.get("low_52", 0)
        price = technicals.get("latest_price", 0)
        atr = technicals.get("atr_14", 0)

        # Drawdown from 52W high
        if high52 > 0:
            drawdown = ((high52 - price) / high52) * 100
            if drawdown > 40:
                score -= 18 # Steep drawdown
            elif drawdown < 12:
                score += 12 # Resilient near highs

        # ATR Volatility ratio
        if price > 0:
            volatility_pct = (atr / price) * 100
            if volatility_pct > 4.5:
                score -= 15 # High daily volatility
            elif volatility_pct < 2.0:
                score += 12 # Low steady volatility

        # Solvency risk
        raw = fundamentals.get("raw_metrics", {}) if fundamentals else {}
        debt_to_equity = raw.get("debt_to_equity")
        if debt_to_equity is not None:
            if debt_to_equity > 200:
                score -= 15
            elif debt_to_equity < 50:
                score += 10

        final_score = int(round(max(10, min(95, score))))
        if final_score >= 70:
            risk_label = "Low Risk"
        elif final_score <= 45:
            risk_label = "High Risk"
        else:
            risk_label = "Moderate Risk"

        return final_score, risk_label

    @staticmethod
    def _compute_liquidity_score(technicals):
        if not technicals or not technicals.get("available"):
            return 50
        price = technicals.get("latest_price", 0)
        return 80 if price > 50 else 55

    @staticmethod
    def _extract_strengths_and_risks(fundamentals, technicals, val_score, mom_score, sent_score, risk_label):
        strengths = []
        risks = []

        if fundamentals.get("available"):
            raw = fundamentals.get("raw_metrics", {})
            roe = raw.get("roe")
            if roe and roe > 0.15:
                strengths.append(f"High Return on Equity ({fundamentals.get('roe')})")
            elif roe and roe < 0.08:
                risks.append(f"Subdued Return on Equity ({fundamentals.get('roe')})")

            de = raw.get("debt_to_equity")
            if de is not None and de < 50:
                strengths.append("Conservative leverage & low debt")
            elif de is not None and de > 150:
                risks.append("High debt-to-equity ratio")

        if technicals.get("available"):
            rsi = technicals.get("rsi_14", 50)
            if 55 <= rsi <= 68:
                strengths.append(f"Bullish momentum structure (RSI {rsi})")
            elif rsi > 75:
                risks.append(f"Overbought condition (RSI {rsi})")
            elif rsi < 35:
                risks.append(f"Bearish momentum trend (RSI {rsi})")

            if technicals.get("trend_signal") == "Bullish":
                strengths.append("Trading above key 50 & 200 daily moving averages")
            elif technicals.get("trend_signal") == "Bearish":
                risks.append("Trading below major medium-term moving averages")

        if val_score >= 70:
            strengths.append("Attractive valuation multiples compared to historical baseline")
        elif val_score <= 40:
            risks.append("Premium valuation pricing in aggressive future growth")

        if sent_score >= 70:
            strengths.append("Strong positive market news sentiment")
        elif sent_score <= 35:
            risks.append("Negative market news headlines")

        if not strengths:
            strengths.append("Established market presence and continuous liquidity")
        if not risks:
            risks.append("Broad equity market volatility and sector rotation risk")

        return strengths[:4], risks[:4]
