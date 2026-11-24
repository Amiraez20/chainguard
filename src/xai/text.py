def _fr(s: str) -> str:
    """Format français : espace pour les milliers, virgule pour les décimales."""
    return s.replace(",", "\u202f").replace(".", ",")


def _duree(v: float) -> str:
    if v >= 1440:
        return _fr(f"{v / 1440:,.0f} jours")
    if v >= 60:
        return _fr(f"{v / 60:,.1f} h")
    return _fr(f"{v:,.1f} min")


LABELS = {
    "Time Diff between first and last (Mins)": ("durée d'activité", _duree),
    "Avg min between received tnx": ("écart moyen entre réceptions", _duree),
    "Avg min between sent tnx": ("écart moyen entre envois", _duree),
    "Unique Received From Addresses": ("expéditeurs distincts", "{:,.0f}"),
    "Unique Sent To Addresses": ("destinataires distincts", "{:,.0f}"),
    "Received Tnx": ("transactions reçues", "{:,.0f}"),
    "Sent tnx": ("transactions envoyées", "{:,.0f}"),
    "total ether received": ("ETH reçus au total", "{:,.3f} ETH"),
    "total Ether sent": ("ETH envoyés au total", "{:,.3f} ETH"),
    "total ether balance": ("solde", "{:,.3f} ETH"),
    "min value received": ("plus petite réception", "{:,.4f} ETH"),
    "max value received": ("plus grosse réception", "{:,.3f} ETH"),
    "avg val received": ("réception moyenne", "{:,.3f} ETH"),
    "min val sent": ("plus petit envoi", "{:,.4f} ETH"),
    "max val sent": ("plus gros envoi", "{:,.3f} ETH"),
    "avg val sent": ("envoi moyen", "{:,.3f} ETH"),
}


def to_text(contribs, k=3) -> str:
    """Phrase lisible par un analyste SOC : raisons de l'alerte, puis facteurs atténuants."""
    top = sorted(contribs, key=lambda c: -abs(c.shap))[:k]

    def one(c):
        label, fmt = LABELS.get(c.name, (c.name, "{:,.2f}"))
        val = fmt(c.value) if callable(fmt) else _fr(fmt.format(c.value))
        return f"{label} : {val}"

    up = [one(c) for c in top if c.shap > 0]
    down = [one(c) for c in top if c.shap <= 0]
    txt = ("Signalée principalement pour : " + " ; ".join(up)) if up \
        else "Signalée sans facteur de risque dominant"
    if down:
        txt += ". Facteurs atténuants : " + " ; ".join(down)
    return txt + "."