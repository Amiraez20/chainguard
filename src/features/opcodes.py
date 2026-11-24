import re
from collections import Counter
from pyevmasm import disassemble_all


def _to_bytes(bytecode) -> bytes:
    if isinstance(bytecode, str):
        return bytes.fromhex(bytecode.removeprefix("0x"))
    return bytes(bytecode)  # bytes ou HexBytes (web3)


def opcode_counts(bytecode) -> Counter:
    """Nombre d'occurrences de chaque opcode.

    PUSH1..32, DUP1..16, SWAP1..16 et LOG0..4 sont fusionnés en PUSH, DUP, SWAP, LOG :
    c'est la convention du dataset X-SPIDE (sinon décalage entre entraînement et inférence).
    """
    counts = Counter()
    for ins in disassemble_all(_to_bytes(bytecode)):
        name = re.sub(r"^(PUSH|DUP|SWAP|LOG)\d+$", r"\1", ins.name)
        counts[name] += 1
    return counts


def opcode_features(bytecode, vocab: list[str]) -> dict:
    """Fréquences relatives (op_*) + taille du code (n_instr), sur un vocabulaire fixe."""
    c = opcode_counts(bytecode)
    # Comme à l'entraînement : seuls les opcodes du vocabulaire comptent (INVALID, PUSH0
    # récent ou données de métadonnées en fin de bytecode sont ignorés dans le total).
    total = sum(c[op] for op in vocab) or 1
    feats = {f"op_{op}": c[op] / total for op in vocab}
    feats["n_instr"] = total
    return feats
