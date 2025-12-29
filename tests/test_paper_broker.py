from execution.paper_broker import PaperBroker

def test_paper_broker_long_tp():
    broker = PaperBroker()
    broker.open_position("BTC/USDT", "LONG", entry=100, stop_loss=95, take_profit=110)
    
    # simulate a candle that hits TP
    pnl = broker.check_and_close(high=111, low=99, close=105)
    assert pnl > 0