portfolio = {
    "balance": 10000,
    "positions": {},
    "history": [],
    "equity": []
}

def buy(symbol, price, qty):
    portfolio["balance"] -= price * qty
    portfolio["positions"][symbol] = {"entry": price, "qty": qty}

def sell(symbol, price):
    if symbol in portfolio["positions"]:
        pos = portfolio["positions"][symbol]
        pnl = (price - pos["entry"]) * pos["qty"]

        portfolio["balance"] += price * pos["qty"]
        portfolio["history"].append({"pnl": pnl})

        del portfolio["positions"][symbol]

def update_equity(prices):
    total = portfolio["balance"]

    for sym in portfolio["positions"]:
        pos = portfolio["positions"][sym]
        total += prices.get(sym, pos["entry"]) * pos["qty"]

    portfolio["equity"].append(total)

def get_portfolio():
    return portfolio
