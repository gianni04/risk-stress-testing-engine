"""
Risk & Stress-Testing Dashboard
--------------------------------
Student project: measure and stress-test the risk of an equity portfolio.

1) Value-at-Risk (VaR) and Conditional VaR (CVaR / Expected Shortfall)
   computed 3 ways: historical, parametric (variance-covariance), Monte Carlo.
2) Stress testing against historical crisis scenarios (2008 GFC, 2020 COVID crash,
   a simple rate-shock scenario).
3) Rolling volatility and correlation heatmap.

Data source: Yahoo Finance (real prices, daily).
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from scipy.stats import norm

# ----------------------------------------------------------------------
# 1. CONFIG
# ----------------------------------------------------------------------

TICKERS = ["AAPL", "MSFT", "JPM", "XOM", "JNJ", "PG", "V", "NVDA", "KO", "UNH"]
WEIGHTS = np.repeat(1.0 / len(TICKERS), len(TICKERS))  # equal-weight book for this study

START_DATE = "2007-01-01"  # needs to reach back to 2008 for the GFC stress scenario
END_DATE = "2026-08-01"
TRADING_DAYS = 252

PORTFOLIO_VALUE = 10_000_000  # $10m book, typical size for a demo mandate
CONFIDENCE = 0.99             # 99% VaR, standard risk-desk convention
N_MC_SIMULATIONS = 20_000

OUTPUT_DIR = "output"


# ----------------------------------------------------------------------
# 2. DATA
# ----------------------------------------------------------------------

def load_data():
    prices = yf.download(TICKERS, start=START_DATE, end=END_DATE, progress=False)["Close"]
    prices = prices.dropna()
    daily_returns = prices.pct_change().dropna()
    portfolio_returns = daily_returns @ WEIGHTS
    return prices, daily_returns, portfolio_returns


# ----------------------------------------------------------------------
# 3. VALUE-AT-RISK / EXPECTED SHORTFALL
# ----------------------------------------------------------------------

def historical_var_cvar(portfolio_returns, confidence, portfolio_value):
    """Historical simulation: use the empirical distribution of past returns."""
    sorted_returns = np.sort(portfolio_returns)
    cutoff_index = int((1 - confidence) * len(sorted_returns))
    var_return = sorted_returns[cutoff_index]
    cvar_return = sorted_returns[:cutoff_index].mean()

    var_dollar = -var_return * portfolio_value
    cvar_dollar = -cvar_return * portfolio_value
    return var_dollar, cvar_dollar


def parametric_var_cvar(portfolio_returns, confidence, portfolio_value):
    """Variance-covariance method: assume returns are normally distributed."""
    mu = portfolio_returns.mean()
    sigma = portfolio_returns.std()
    z = norm.ppf(1 - confidence)

    var_return = mu + z * sigma
    # analytical expected shortfall for a normal distribution
    cvar_return = mu - sigma * norm.pdf(z) / (1 - confidence)

    var_dollar = -var_return * portfolio_value
    cvar_dollar = -cvar_return * portfolio_value
    return var_dollar, cvar_dollar


def monte_carlo_var_cvar(portfolio_returns, confidence, portfolio_value, n_sims):
    """Simulate n_sims daily returns drawn from a normal fit and re-measure VaR/CVaR."""
    mu = portfolio_returns.mean()
    sigma = portfolio_returns.std()

    rng = np.random.default_rng(seed=42)
    simulated_returns = rng.normal(mu, sigma, n_sims)

    sorted_sim = np.sort(simulated_returns)
    cutoff_index = int((1 - confidence) * n_sims)
    var_return = sorted_sim[cutoff_index]
    cvar_return = sorted_sim[:cutoff_index].mean()

    var_dollar = -var_return * portfolio_value
    cvar_dollar = -cvar_return * portfolio_value
    return var_dollar, cvar_dollar


# ----------------------------------------------------------------------
# 4. STRESS TESTING
# ----------------------------------------------------------------------

def run_stress_scenarios(prices, daily_returns, portfolio_value):
    """
    Apply historical crisis windows to the CURRENT book (same weights, same tickers)
    to see 'what would happen if that crisis repeated today'.
    """
    scenarios = {
        "2008 Global Financial Crisis": ("2008-09-01", "2008-11-30"),
        "2020 COVID Crash": ("2020-02-19", "2020-03-23"),
        "2022 Rate-Hike Selloff": ("2022-01-01", "2022-06-30"),
    }

    results = []
    for name, (start, end) in scenarios.items():
        window = daily_returns.loc[start:end]
        if window.empty:
            continue
        # cumulative return of each stock over the crisis window, applied to current weights
        cumulative_stock_returns = (1 + window).prod() - 1
        shocked_portfolio_return = float(np.dot(WEIGHTS, cumulative_stock_returns))
        dollar_impact = shocked_portfolio_return * portfolio_value
        results.append([name, shocked_portfolio_return, dollar_impact])

    # a simple synthetic rate-shock: +200bps parallel shock, proxied as a flat
    # -8% hit to rate-sensitive names (banks) and -3% to the rest (illustrative, not a real model)
    rate_shock_returns = pd.Series(
        [-0.03 if t not in ("JPM", "V") else -0.08 for t in TICKERS], index=TICKERS
    )
    rate_shock_return = float(np.dot(WEIGHTS, rate_shock_returns))
    results.append(["Synthetic +200bps Rate Shock", rate_shock_return, rate_shock_return * portfolio_value])

    return pd.DataFrame(results, columns=["Scenario", "Portfolio Return", "P&L Impact ($)"])


# ----------------------------------------------------------------------
# 5. MAIN
# ----------------------------------------------------------------------

def main():
    print("Downloading price history for:", TICKERS)
    prices, daily_returns, portfolio_returns = load_data()

    # --- VaR / CVaR, 3 methods ---
    hist_var, hist_cvar = historical_var_cvar(portfolio_returns, CONFIDENCE, PORTFOLIO_VALUE)
    param_var, param_cvar = parametric_var_cvar(portfolio_returns, CONFIDENCE, PORTFOLIO_VALUE)
    mc_var, mc_cvar = monte_carlo_var_cvar(portfolio_returns, CONFIDENCE, PORTFOLIO_VALUE, N_MC_SIMULATIONS)

    var_table = pd.DataFrame({
        "Method": ["Historical", "Parametric (Normal)", "Monte Carlo"],
        "1-day VaR 99% ($)": [hist_var, param_var, mc_var],
        "1-day CVaR 99% ($)": [hist_cvar, param_cvar, mc_cvar],
    })
    print("\nVaR / CVaR summary (portfolio value = ${:,.0f}):\n".format(PORTFOLIO_VALUE), var_table.round(0))
    var_table.to_csv(f"{OUTPUT_DIR}/var_cvar_summary.csv", index=False)

    # --- stress scenarios ---
    stress_table = run_stress_scenarios(prices, daily_returns, PORTFOLIO_VALUE)
    print("\nStress test results:\n", stress_table.round(4))
    stress_table.to_csv(f"{OUTPUT_DIR}/stress_test_results.csv", index=False)

    # --- rolling 21-day annualized volatility ---
    rolling_vol = portfolio_returns.rolling(21).std() * np.sqrt(TRADING_DAYS)
    plt.figure(figsize=(10, 5))
    rolling_vol.plot()
    plt.title("Rolling 21-Day Annualized Portfolio Volatility")
    plt.ylabel("Annualized Volatility")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/rolling_volatility.png", dpi=150)

    # --- correlation heatmap (plain matplotlib, no seaborn dependency) ---
    corr = daily_returns.corr()
    fig, ax = plt.subplots(figsize=(9, 7))
    im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticklabels(corr.columns)
    for i in range(len(corr.columns)):
        for j in range(len(corr.columns)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=ax)
    ax.set_title("Return Correlation Matrix")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/correlation_heatmap.png", dpi=150)

    # --- return distribution with VaR/CVaR markers ---
    plt.figure(figsize=(9, 5))
    plt.hist(portfolio_returns, bins=80, color="steelblue", alpha=0.7)
    plt.axvline(-hist_var / PORTFOLIO_VALUE, color="red", linestyle="--", label="Historical VaR 99%")
    plt.axvline(-hist_cvar / PORTFOLIO_VALUE, color="darkred", linestyle="--", label="Historical CVaR 99%")
    plt.title("Daily Portfolio Return Distribution")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/return_distribution.png", dpi=150)

    print(f"\nSaved charts and CSVs to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
