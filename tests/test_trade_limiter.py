from filters.trade_limiter import TradeLimiter

def test_daily_trade_limit_and_reset():
    limiter = TradeLimiter(max_trades_per_day=1)
    
    assert limiter.can_trade()
    limiter.record_trade_opened()
    assert not limiter.can_trade()

    # force-reset for test
    limiter.trades_today = 0  
    assert limiter.can_trade()