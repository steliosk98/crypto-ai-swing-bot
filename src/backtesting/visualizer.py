from typing import Iterable, Optional

import matplotlib.pyplot as plt


def _series_or_index(values: Iterable[float], timestamps: Optional[Iterable] = None):
    values_list = list(values)
    if timestamps:
        ts_list = list(timestamps)
        if len(ts_list) == len(values_list):
            return ts_list, values_list
    return list(range(len(values_list))), values_list


def plot_equity_curve(session, save_path: Optional[str] = None, show: bool = True) -> None:
    """
    Plot the equity curve for a backtest session.
    """
    equity = session.equity_curve
    timestamps = session.timestamps

    if not equity:
        return

    x, y = _series_or_index(equity, timestamps if timestamps else None)
    plt.figure(figsize=(10, 4))
    plt.plot(x, y, label="Equity")
    plt.title("Equity Curve")
    plt.xlabel("Time" if timestamps else "Trade #")
    plt.ylabel("Equity")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150)
    if show:
        plt.show()
    plt.close()


def plot_drawdowns(session) -> None:
    """
    Plot drawdowns over time for a backtest session.
    """
    if not session.equity_curve:
        return

    drawdowns = []
    peak = session.equity_curve[0]
    for equity in session.equity_curve:
        peak = max(peak, equity)
        drawdowns.append((equity - peak) / peak)

    x, y = _series_or_index(drawdowns, session.timestamps if session.timestamps else None)
    plt.figure(figsize=(10, 3))
    plt.plot(x, y, color="red", label="Drawdown")
    plt.title("Drawdowns")
    plt.xlabel("Time" if session.timestamps else "Trade #")
    plt.ylabel("Drawdown")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()
