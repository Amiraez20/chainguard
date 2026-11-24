import pandas as pd

WEI = 1e18


def features_from_txlist(txs: list[dict], address: str) -> dict:
    """Recalcule, à partir de l'API Etherscan, les features du dataset Kaggle
    disponibles dans les transactions normales."""
    if not txs:
        return {}
    a = address.lower()
    df = pd.DataFrame(txs)
    df = df[df["isError"] == "0"].copy()
    if df.empty:
        return {}
    df["to"] = df["to"].fillna("").str.lower()
    df["from"] = df["from"].str.lower()
    df["t"] = df["timeStamp"].astype(int) / 60        # minutes
    df["v"] = df["value"].astype(float) / WEI         # ETH
    sent, recv = df[df["from"] == a], df[df["to"] == a]

    def gap(s):
        return s["t"].sort_values().diff().mean() if len(s) > 1 else 0.0

    def stat(s, f):
        return getattr(s["v"], f)() if len(s) else 0.0

    return {
        "Avg min between sent tnx": gap(sent),
        "Avg min between received tnx": gap(recv),
        "Time Diff between first and last (Mins)": df["t"].max() - df["t"].min(),
        "Sent tnx": len(sent), "Received Tnx": len(recv),
        "Unique Received From Addresses": recv["from"].nunique(),
        "Unique Sent To Addresses": sent["to"].nunique(),
        "min value received": stat(recv, "min"), "max value received": stat(recv, "max"),
        "avg val received": stat(recv, "mean"),
        "min val sent": stat(sent, "min"), "max val sent": stat(sent, "max"),
        "avg val sent": stat(sent, "mean"),
        "total Ether sent": sent["v"].sum(), "total ether received": recv["v"].sum(),
        "total ether balance": recv["v"].sum() - sent["v"].sum(),
    }