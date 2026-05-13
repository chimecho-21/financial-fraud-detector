"""
机器学习预测模块
基于规则引擎提取的特征，使用 Random Forest 进行财务造假概率预测。
支持：
  1. 冷启动：使用基于规则合成的标签训练基础模型
  2. 在线训练：用户上传标注数据后重新训练
"""

import pickle
import os
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from ..models.schemas import FinancialData, MLResult

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "fraud_model.pkl")


class MLPredictor:
    def __init__(self):
        self.model: RandomForestClassifier = None
        self.feature_names: list[str] = []
        self.is_trained = False
        self._load_or_init()

    def _load_or_init(self):
        """加载已有模型或初始化默认模型"""
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    data = pickle.load(f)
                self.model = data["model"]
                self.feature_names = data["feature_names"]
                self.is_trained = True
            except Exception:
                self._train_default()

        if not self.is_trained:
            self._train_default()

    def _train_default(self):
        """使用基于规则的合成数据训练默认模型"""
        np.random.seed(42)
        n_samples = 500

        features = []
        labels = []

        for i in range(n_samples):
            is_fraud = np.random.random() < 0.15
            f = self._generate_features(is_fraud)
            features.append(f)
            labels.append(1 if is_fraud else 0)

        X = np.array(features)
        y = np.array(labels)

        self.feature_names = [
            "dsri", "gmi", "aqi", "sgi", "depi", "sgai", "lvgi", "tata",
            "ocf_to_ni", "ar_to_revenue", "debt_ratio", "gm_change",
            "revenue_growth", "inventory_ratio",
        ]

        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            min_samples_leaf=5,
            random_state=42,
            class_weight="balanced",
        )
        self.model.fit(X, y)
        self.is_trained = True

        # 保存模型
        try:
            with open(MODEL_PATH, "wb") as f:
                pickle.dump({"model": self.model, "feature_names": self.feature_names}, f)
        except Exception:
            pass

    def _generate_features(self, is_fraud: bool) -> list[float]:
        """根据是否为造假生成特征向量"""
        if is_fraud:
            return [
                np.random.uniform(1.0, 3.0),   # dsri
                np.random.uniform(1.0, 2.0),   # gmi
                np.random.uniform(1.0, 2.5),   # aqi
                np.random.uniform(1.2, 2.5),   # sgi
                np.random.uniform(0.5, 1.5),   # depi
                np.random.uniform(1.0, 2.0),   # sgai
                np.random.uniform(1.0, 2.0),   # lvgi
                np.random.uniform(0.05, 0.3),  # tata
                np.random.uniform(0.0, 0.8),   # ocf_to_ni
                np.random.uniform(0.2, 0.5),   # ar_to_revenue
                np.random.uniform(0.5, 0.9),   # debt_ratio
                np.random.uniform(0.05, 0.3),  # gm_change
                np.random.uniform(0.2, 1.0),   # revenue_growth
                np.random.uniform(0.15, 0.4),  # inventory_ratio
            ]
        else:
            return [
                np.random.uniform(0.5, 1.5),   # dsri
                np.random.uniform(0.8, 1.2),   # gmi
                np.random.uniform(0.5, 1.2),   # aqi
                np.random.uniform(0.8, 1.3),   # sgi
                np.random.uniform(0.8, 1.2),   # depi
                np.random.uniform(0.8, 1.2),   # sgai
                np.random.uniform(0.8, 1.2),   # lvgi
                np.random.uniform(-0.05, 0.05), # tata
                np.random.uniform(0.8, 1.5),   # ocf_to_ni
                np.random.uniform(0.05, 0.2),  # ar_to_revenue
                np.random.uniform(0.2, 0.6),   # debt_ratio
                np.random.uniform(0.0, 0.08),  # gm_change
                np.random.uniform(-0.1, 0.3),  # revenue_growth
                np.random.uniform(0.05, 0.18), # inventory_ratio
            ]

    def _extract_features(self, statements: list[FinancialData]) -> np.ndarray:
        """从财务数据中提取特征向量"""
        if len(statements) < 2:
            return np.zeros((1, len(self.feature_names)))

        curr = statements[-1]
        prev = statements[-2]

        def sdiv(a, b, d=0.0):
            return a / b if abs(b) > 1e-10 else d

        features = [
            sdiv(sdiv(curr.accounts_receivable, curr.revenue),
                 sdiv(prev.accounts_receivable, prev.revenue, 1), 1),  # dsri
            sdiv(sdiv(prev.gross_profit or prev.revenue - prev.cost_of_revenue, prev.revenue),
                 sdiv(curr.gross_profit or curr.revenue - curr.cost_of_revenue, curr.revenue), 1),  # gmi
            sdiv(1 - sdiv(curr.current_assets + curr.fixed_assets, curr.total_assets),
                 1 - sdiv(prev.current_assets + prev.fixed_assets, prev.total_assets), 1),  # aqi
            sdiv(curr.revenue, prev.revenue, 1),  # sgi
            sdiv(sdiv(prev.depreciation, prev.fixed_assets),
                 sdiv(curr.depreciation, curr.fixed_assets), 1),  # depi
            sdiv(sdiv(curr.sg_and_a, curr.revenue),
                 sdiv(prev.sg_and_a, prev.revenue), 1),  # sgai
            sdiv(sdiv(curr.total_liabilities, curr.total_assets),
                 sdiv(prev.total_liabilities, prev.total_assets), 1),  # lvgi
            sdiv(curr.net_income - curr.operating_cash_flow, curr.total_assets),  # tata
            sdiv(curr.operating_cash_flow, curr.net_income, 1),  # ocf_to_ni
            sdiv(curr.accounts_receivable, curr.revenue),  # ar_to_revenue
            sdiv(curr.total_liabilities, curr.total_assets),  # debt_ratio
            sdiv((curr.gross_profit or curr.revenue - curr.cost_of_revenue) -
                 (prev.gross_profit or prev.revenue - prev.cost_of_revenue),
                 prev.gross_profit or prev.revenue - prev.cost_of_revenue, 0),  # gm_change
            sdiv(curr.revenue - prev.revenue, prev.revenue, 0),  # revenue_growth
            sdiv(curr.inventory, curr.revenue),  # inventory_ratio
        ]

        return np.array([features])

    def predict(self, statements: list[FinancialData]) -> MLResult:
        """对财务数据进行造假概率预测"""
        result = MLResult()

        if not self.is_trained or self.model is None:
            result.description = "模型未就绪"
            return result

        if len(statements) < 2:
            result.description = "需要至少两年数据"
            return result

        X = self._extract_features(statements)
        proba = self.model.predict_proba(X)[0]

        fraud_idx = list(self.model.classes_).index(1) if 1 in self.model.classes_ else 1
        fraud_prob = float(proba[fraud_idx])

        result.fraud_probability = round(fraud_prob, 4)
        result.model_available = True

        if fraud_prob < 0.3:
            result.prediction = "正常"
        elif fraud_prob < 0.6:
            result.prediction = "存在风险"
        else:
            result.prediction = "高风险"

        # 特征重要性
        if hasattr(self.model, "feature_importances_") and self.feature_names:
            importances = {}
            for name, imp in zip(self.feature_names, self.model.feature_importances_):
                importances[name] = round(float(imp), 4)
            # 按重要性排序
            sorted_imp = dict(sorted(importances.items(), key=lambda x: x[1], reverse=True))
            result.feature_importance = sorted_imp

        result.description = (
            f"ML 模型预测造假概率为 {fraud_prob:.1%}，"
            f"判定为「{result.prediction}」。"
        )

        return result

    def train(self, X: np.ndarray, y: np.ndarray, feature_names: list[str]) -> dict:
        """使用用户提供的数据训练模型"""
        if len(X) != len(y):
            return {"error": "特征和标签长度不一致"}

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            random_state=42,
            class_weight="balanced",
        )
        self.model.fit(X_train, y_train)
        self.feature_names = feature_names or [f"f{i}" for i in range(X.shape[1])]
        self.is_trained = True

        # 评估
        y_pred = self.model.predict(X_test)
        metrics = {
            "accuracy": round(accuracy_score(y_test, y_pred), 4),
            "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
            "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
            "f1": round(f1_score(y_test, y_pred, zero_division=0), 4),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        }

        # 保存
        try:
            with open(MODEL_PATH, "wb") as f:
                pickle.dump({"model": self.model, "feature_names": self.feature_names}, f)
        except Exception as e:
            metrics["save_error"] = str(e)

        return metrics
