# Risk & Stress Testing Engine

Risque d'un portefeuille actions en Python : VaR et CVaR à 99 % par trois méthodes (historique, paramétrique, Monte Carlo), stress tests sur les crises de 2008, 2020 et 2022, volatilité glissante et corrélations.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Data](https://img.shields.io/badge/data-Yahoo%20Finance-purple) ![License](https://img.shields.io/badge/License-MIT-green)

## Ce que fait le projet

Portefeuille de **10 M$** équipondéré sur 10 actions US (AAPL, MSFT, JPM, XOM, JNJ, PG, V, NVDA, KO, UNH), historique quotidien 2007 → 2026.

- **VaR / CVaR 1 jour à 99 %** : simulation historique, paramétrique gaussienne (variance-covariance), Monte Carlo (20 000 tirages).
- **Stress tests** : rejeu des fenêtres de crise réelles et choc de taux synthétique.
- **Diagnostics** : volatilité glissante, distribution des rendements, heatmap de corrélation.

## Quickstart

```bash
pip install -r requirements.txt
python risk_stress_testing.py
```

## Résultats

### VaR et CVaR (1 jour, 99 %, portefeuille de 10 M$)

| Méthode | VaR | CVaR |
|---|---:|---:|
| Historique | **343 310 $** | **519 299 $** |
| Paramétrique (normale) | 279 282 $ | 321 126 $ |
| Monte Carlo | 280 708 $ | 323 038 $ |

La VaR historique dépasse la VaR gaussienne de 23 % et la CVaR historique de 62 % : les queues de distribution réelles sont bien plus épaisses que ne le suppose l'hypothèse normale.

![Distribution des rendements](output/return_distribution.png)

### Stress tests

| Scénario | Rendement | P&L |
|---|---:|---:|
| Crise financière 2008 (sept.–nov. 2008) | −22,2 % | −2,22 M$ |
| Krach COVID (19 fév.–23 mars 2020) | **−32,8 %** | **−3,28 M$** |
| Hausse des taux 2022 (S1 2022) | −8,4 % | −0,84 M$ |
| Choc de taux synthétique +200 bp | −4,0 % | −0,40 M$ |

### Volatilité et corrélations

![Volatilité glissante](output/rolling_volatility.png)
![Corrélations](output/correlation_heatmap.png)

## Stack

`Python` · `NumPy` · `pandas` · `SciPy` · `Matplotlib` · `yfinance`

## Licence

MIT — voir [LICENSE](LICENSE).
