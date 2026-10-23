# Out-of-sample validation, bootstrap and overfitting (Phase 25 OOS Validation)
## Strict Statistical Validation, Bootstrap Uncertainty & Walk-Forward Audit

> **Repository:** [`wallex`](..)  
> **Research branch:** `research/phase25-validation`  
> **Frozen base commit:** [`b494d60e211497f47ef3b79d6ae79a0726471172`](..)  
> **Classification of statistical status:** ⚠️ **INCONCLUSIVE**

---

## 1. Data Snooping Disclosure

> [!IMPORTANT]
> ### The scientific truth about the 29 investigated windows:
> 29 72-hour windows of competition during phases 20 to 24 have been repeatedly analyzed, analyzed and revised.  
> Therefore, from the perspective of international quantitative research standards, these 29 windows are considered **Research Data**, not a blind and untouched sample (Pristine Holdout).  
> Any improvement in this dataset should not be interpreted as definitive proof of future success.

---

## 2. Bootstrap Uncertainty - 10,000 Iterations

To evaluate the stability of the 72-hour mean efficiency of the combined H1+H3 model, the efficiency distribution of 29 windows was simulated with 10,000 random resampling times (Bootstrap with Replacement):

| Bootstrap statistical index Computational value | Statistical interpretation and financial risk
|---|:---:|---|
| **Average observed yield** | **0.0441%+** | The mean of the original sample |
| **95% bootstrap confidence interval** | **[-0.0811%, +0.1798%]** | **Crossing the confidence interval of zero!** |
| **Probability of positive average yield** | **73.74%** | Profitability beyond zero
| **one-sided empirical p-value** | **26.26%** | **Not rejecting the null hypothesis at the 5% level!** |

### Scientific interpretation:
The 95% confidence interval includes negative values (up to 0.08%-loss in each window) and the p-value is **26.3%**.  
In statistics, when the p-value is greater than 5% ($p > 0.05$), the hypothesis of random chance is not rejected. Therefore, the average profitability of this system is statistically **proven not definitive**.

---

## 3. Extreme sensitivity to remove outliers (Outlier Sensitivity)

| Outlier data removal scenario Total Net Profit (TMN) | Profit change delta | Account profitability status
|---|:---:|:---:|:---:|
| **Total 29 match windows** | **63,954.7+** | Basis | Profitable
| **Remove only top rank window 1 (W09)** | **3,440.8-** | 67,395.5- | ❌ **It was negative!** |
| **Remove the top 2 windows (W09, W20)** | **8,692.7-** | 72,647.4- | ❌ **Negative** |
| **Remove the top 3 windows (W09, W20, W21)** | **21,969.4-** | 85,924.1- | ❌ **deep negative** |

> [!CAUTION]
> **Critical Fragility Point:** The entire profitability of the system depends on **an exceptional window (W09)**. By removing W09, the whole system loses (-3,441 Tomans).

---

## 4. Chronological Walk-Forward three-part time evaluation

Dividing the 90-day period into 3 consecutive and continuous 30-day periods:

| Time evaluation period Range of windows Total Net Profit (TMN) | Average efficiency of 72 hours Windows win rate The behavior of the market regime
|---|:---:|:---:|:---:|:---:|---|
| **Part 1 (days 1 to 30)** | W01 to W10 | 25,312.7+ | 0.051%+ | 2 out of 10 (20%) | Average upward trend
| **Part 2 (days 31 to 60)** | W11 to W20 | 62,635.1+ | 0.125%+ | 4 out of 10 (40%) | Historical explosive upward wave
| **Part 3 (days 61 to 90)** | W21 to W29 | **23,993.1-** | **0.053%-** | 2 out of 9 (22%) | **Correction of erosion and small fluctuations** |

### Fundamental discovery:
In the last 30 days (W21 to W29), the combined H1+H3 model has recorded a loss of nearly **24,000 Tomans**.  
If the match is held in the same conditions as the third month of the market, the system will face losses.
This finding proves that the strategy lacks stability in all market regimes and in the absence of an uptrend, holding 100% liquidity will be superior.