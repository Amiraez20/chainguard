from collections import Counter
from pyevmasm import disassemble_all


def _to_bytes(bytecode) -> bytes:
    if isinstance(bytecode, str):
        return bytes.fromhex(bytecode.removeprefix("0x"))
    return bytes(bytecode)  # bytes ou HexBytes (web3)


def opcode_counts(bytecode) -> Counter:
    """Nombre d'occurrences de chaque opcode. PUSH1..PUSH32 fusionnés en PUSH (Chen)."""
    counts = Counter()
    for ins in disassemble_all(_to_bytes(bytecode)):
        name = ins.name
        if name.startswith("PUSH") and name[4:].isdigit():
            name = "PUSH"
        counts[name] += 1
    return counts


def opcode_features(bytecode, vocab: list[str]) -> dict:
    """Fréquences relatives (op_*) + taille du code (n_instr), sur un vocabulaire fixe."""
    c = opcode_counts(bytecode)
    total = sum(c.values()) or 1
    feats = {f"op_{op}": c[op] / total for op in vocab}
    feats["n_instr"] = total
    return feats
