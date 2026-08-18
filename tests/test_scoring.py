import unittest
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.scoring_service import ScoringEngine
from services.technical_service import TechnicalService
from services.target_service import TargetService


class TestScoringAndTechnicals(unittest.TestCase):

    def test_scoring_engine_composite(self):
        fundamentals = {
            "available": True,
            "fundamental_score": 85,
            "raw_metrics": {
                "pe": 18.5,
                "pb": 2.2,
                "roe": 0.22,
                "debt_to_equity": 25.0,
                "revenue_growth": 0.18,
                "dividend_yield": 0.025,
                "market_cap": 1500000000000,
            },
        }

        technicals = {
            "available": True,
            "technical_score": 80,
            "latest_price": 2500.0,
            "sma_50": 2350.0,
            "rsi_14": 62.5,
            "high_52": 2600.0,
            "low_52": 2000.0,
            "atr_14": 45.0,
            "trend_signal": "Bullish",
        }

        eval_result = ScoringEngine.evaluate_stock(
            fundamentals_data=fundamentals,
            technicals_data=technicals,
            news_sentiment_score=75,
        )

        self.assertTrue(0 <= eval_result["overall_score"] <= 100)
        self.assertIn(eval_result["signal"], ["Strong Buy", "Buy"])
        self.assertGreaterEqual(eval_result["confidence"], 50)
        self.assertGreater(len(eval_result["strengths"]), 0)
        self.assertIn("factor_scores", eval_result)
        self.assertEqual(eval_result["factor_scores"]["fundamentals"], 85)
        self.assertEqual(eval_result["factor_scores"]["technicals"], 80)

    def test_technical_service_synthetic_data(self):
        dates = pd.date_range(end="2026-08-18", periods=60, freq="B")
        prices = [100.0 + (i * 1.5) + (i % 3) for i in range(60)]

        df = pd.DataFrame(
            {
                "Open": [p - 1.0 for p in prices],
                "High": [p + 2.0 for p in prices],
                "Low": [p - 2.0 for p in prices],
                "Close": prices,
                "Volume": [1000000 + (i * 5000) for i in range(60)],
            },
            index=dates,
        )

        indicators = TechnicalService.calculate_indicators(df)

        self.assertTrue(indicators["available"])
        self.assertEqual(indicators["latest_price"], prices[-1])
        self.assertGreater(indicators["sma_20"], 0)
        self.assertGreater(indicators["sma_50"], 0)
        self.assertTrue(0 <= indicators["rsi_14"] <= 100)
        self.assertGreaterEqual(indicators["bb_upper"], indicators["bb_middle"])
        self.assertGreaterEqual(indicators["bb_middle"], indicators["bb_lower"])
        self.assertGreater(indicators["atr_14"], 0)
        self.assertGreaterEqual(indicators["technical_score"], 10)

    def test_target_service_atr(self):
        technicals = {
            "available": True,
            "latest_price": 1000.0,
            "atr_14": 25.0,
            "support_1": 960.0,
            "resistance_1": 1060.0,
            "trend_signal": "Bullish",
        }

        targets = TargetService.calculate_targets(1000.0, technicals)

        self.assertTrue(targets["available"])
        self.assertGreater(targets["target_price"], 1000.0)
        self.assertLess(targets["stop_loss"], 1000.0)
        self.assertIn("1:", targets["risk_reward_ratio"])


if __name__ == "__main__":
    unittest.main()
