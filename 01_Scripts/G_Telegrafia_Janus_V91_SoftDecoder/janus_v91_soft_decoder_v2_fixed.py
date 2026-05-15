#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROJETO JANUS V9.1 — Decoder RAW vetorial + soft-decision Hamming(9,5)

Objetivo:
  - Reanalisar CSVs V9/V9.1 sem nova extração.
  - Tentar recuperar payload em RAW sem usar q1_futuro/q0_passado como feature.
  - Usar header maior para calibrar assinaturas vetoriais 0/1 dos espiões.
  - Decodificar cada caractere por soft-decision: testa todos os codewords válidos do
    alfabeto Baudot Janus e escolhe o menor custo vetorial ponderado.

Regras de auditoria:
  - q1_futuro só é usado para formar modo POST_Q1_1; nunca como feature.
  - q0_passado nunca é usado como feature.
  - RAW não usa pós-seleção.
  - Features principais usam somente espiao_1, espiao_2, espiao_3.

Instalação:
  pip install pandas numpy

Exemplo:
  python janus_v91_soft_decoder.py --input "janus_v91_run/JANUS_V9_RAW_*.csv" \
    --message JANUS --header 0101010101010101 --outdir janus_v91_analysis
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

ALFABETO = " ABCDEFGHIJKLMNOPQRSTUVWXYZ"
SPY_COLUMNS = ["espiao_1", "espiao_2", "espiao_3"]
DEFAULT_HEADER = "0101010101010101"


# -----------------------------------------------------------------------------
# Codificação Janus V8/V9: Baudot 5-bit + Hamming(9,5) + interleaving
# -----------------------------------------------------------------------------

def normalize_message(message: str) -> str:
    msg = "".join(ch for ch in str(message).upper() if ch in ALFABETO)
    if not msg:
        raise ValueError("Mensagem vazia ou fora do alfabeto Janus permitido.")
    return msg


def char_para_5bit(char: str) -> str:
    idx = ALFABETO.find(char.upper())
    if idx < 0:
        idx = 0
    return format(idx, "05b")


def codificar_hamming_9_5(bits_5: str) -> str:
    if len(bits_5) != 5 or any(b not in "01" for b in bits_5):
        raise ValueError(f"bits_5 inválido: {bits_5!r}")
    d = [int(x) for x in bits_5]
    p1 = d[0] ^ d[1] ^ d[3] ^ d[4]
    p2 = d[0] ^ d[2] ^ d[3]
    p4 = d[1] ^ d[2] ^ d[3]
    p8 = d[4]
    return f"{p1}{p2}{d[0]}{p4}{d[1]}{d[2]}{d[3]}{p8}{d[4]}"


def aplicar_interleaving(blocos_9bits: Sequence[str]) -> str:
    out = ""
    for bit_idx in range(9):
        for bloco in blocos_9bits:
            out += bloco[bit_idx]
    return out


def reverter_interleaving(bits_interleaved: str, num_chars: int) -> List[str]:
    blocos = ["" for _ in range(num_chars)]
    idx = 0
    for bit_idx in range(9):
        for char_idx in range(num_chars):
            if idx < len(bits_interleaved):
                blocos[char_idx] += bits_interleaved[idx]
            idx += 1
    return blocos


def decodificar_hamming_9_5_hard(bloco_9: str) -> Tuple[str, int, bool, str]:
    """Decoder hard clássico. Retorna (bits5, síndrome, corrigiu, bloco_corrigido)."""
    if len(bloco_9) != 9 or any(b not in "01" for b in bloco_9):
        return "00000", -1, False, bloco_9
    b = [int(x) for x in bloco_9]
    s1 = b[0] ^ b[2] ^ b[4] ^ b[6] ^ b[8]
    s2 = b[1] ^ b[2] ^ b[5] ^ b[6]
    s4 = b[3] ^ b[4] ^ b[5] ^ b[6]
    s8 = b[7] ^ b[8]
    syndrome = s1 * 1 + s2 * 2 + s4 * 4 + s8 * 8
    corrected = False
    if 0 < syndrome <= 9:
        b[syndrome - 1] ^= 1
        corrected = True
    bits5 = f"{b[2]}{b[4]}{b[5]}{b[6]}{b[8]}"
    return bits5, syndrome, corrected, "".join(str(x) for x in b)


def build_manifest(message: str, header: str) -> Dict[str, object]:
    message = normalize_message(message)
    if any(b not in "01" for b in header) or len(header) < 4:
        raise ValueError("Header precisa ser uma string binária com pelo menos 4 bits.")
    bits5 = [char_para_5bit(c) for c in message]
    hamming_blocks = [codificar_hamming_9_5(b) for b in bits5]
    payload_interleaved = aplicar_interleaving(hamming_blocks)
    return {
        "message": message,
        "alphabet": ALFABETO,
        "header": header,
        "bits_5": bits5,
        "hamming_9_5_blocks": hamming_blocks,
        "payload_interleaved": payload_interleaved,
        "sequence_bits": header + payload_interleaved,
        "num_header_bits": len(header),
        "num_payload_bits": len(payload_interleaved),
        "num_sequence_bits": len(header) + len(payload_interleaved),
    }


def valid_codebook() -> Dict[str, Dict[str, str]]:
    """char -> {bits5, code9}. Inclui espaço e A-Z."""
    book: Dict[str, Dict[str, str]] = {}
    for ch in ALFABETO:
        bits5 = char_para_5bit(ch)
        book[ch] = {"bits5": bits5, "code9": codificar_hamming_9_5(bits5)}
    return book


# -----------------------------------------------------------------------------
# Features vetoriais dos espiões
# -----------------------------------------------------------------------------

def _flicker(v: np.ndarray) -> float:
    if len(v) <= 1:
        return 0.0
    return float(np.mean(np.abs(np.diff(v))))


def _safe_ratio(a: float, b: float, eps: float = 1e-6) -> float:
    return float(a / (b + eps))


def spy_feature_vector(df: pd.DataFrame, mode: str = "v91") -> Dict[str, float]:
    """Features por bloco usando SOMENTE espiao_1/2/3."""
    if len(df) == 0:
        return {}
    spies = df[SPY_COLUMNS].astype(float)
    e1 = spies["espiao_1"].to_numpy(dtype=float)
    e2 = spies["espiao_2"].to_numpy(dtype=float)
    e3 = spies["espiao_3"].to_numpy(dtype=float)
    cons = e1 + e2 + e3
    m1, m2, m3 = float(np.mean(e1)), float(np.mean(e2)), float(np.mean(e3))
    c = float(np.mean(cons))

    base = {
        "e1_mean": m1,
        "e2_mean": m2,
        "e3_mean": m3,
        "cons_mean": c,
        "e1_minus_e2": m1 - m2,
        "e1_minus_e3": m1 - m3,
        "e2_minus_e3": m2 - m3,
        "e1_ratio_e2": _safe_ratio(m1, m2),
        "e2_ratio_e1": _safe_ratio(m2, m1),
        "e1_share": _safe_ratio(m1, c),
        "e2_share": _safe_ratio(m2, c),
        "e3_share": _safe_ratio(m3, c),
    }

    if mode == "minimal":
        return {k: base[k] for k in ["e1_mean", "e2_mean", "e3_mean", "e1_minus_e2", "e2_minus_e3", "cons_mean"]}

    # Full V9.1: inclui variância/flicker, mas ainda só dos espiões.
    base.update({
        "e1_var": float(np.var(e1)),
        "e2_var": float(np.var(e2)),
        "e3_var": float(np.var(e3)),
        "cons_var": float(np.var(cons)),
        "e1_flicker": _flicker(e1),
        "e2_flicker": _flicker(e2),
        "e3_flicker": _flicker(e3),
        "cons_flicker": _flicker(cons),
    })
    return base


def feature_columns(mode: str) -> List[str]:
    dummy = spy_feature_vector(pd.DataFrame({
        "espiao_1": [0, 1, 0, 1],
        "espiao_2": [1, 0, 1, 0],
        "espiao_3": [0, 0, 1, 1],
    }), mode=mode)
    return list(dummy.keys())


# -----------------------------------------------------------------------------
# Leitura e agregação
# -----------------------------------------------------------------------------

def load_inputs(pattern: str) -> pd.DataFrame:
    files = sorted(glob.glob(pattern))
    if not files:
        p = Path(pattern)
        if p.exists():
            files = [str(p)]
    if not files:
        raise FileNotFoundError(f"Nenhum arquivo encontrado para: {pattern}")
    dfs = []
    for f in files:
        print(f"    - {f}")
        dfs.append(pd.read_csv(f, low_memory=False))
    df = pd.concat(dfs, ignore_index=True)
    for c in ["cycle", "sequence_index", "payload_index", "char_index", "bit_in_char", "bit_sent", "q1_futuro", "q0_passado", *SPY_COLUMNS]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(-1).astype(int)
    missing = [c for c in SPY_COLUMNS + ["dataset", "sequence_index", "bit_sent"] if c not in df.columns]
    if missing:
        raise ValueError(f"CSV sem colunas obrigatórias: {missing}")
    if "cycle" not in df.columns:
        df["cycle"] = 0
    return df


def apply_mode_filter(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    if mode == "RAW":
        return df
    if mode == "POST_Q1_1":
        return df[df["q1_futuro"].astype(int) == 1]
    if mode == "POST_Q1_0":
        return df[df["q1_futuro"].astype(int) == 0]
    raise ValueError(f"Modo desconhecido: {mode}")


def add_sequence_metadata_if_needed(df: pd.DataFrame, message: str, header: str) -> pd.DataFrame:
    """Garante sequence_kind/payload_index/char_index/bit_in_char mesmo se vierem ausentes."""
    out = df.copy()
    msg = normalize_message(message)
    header_len = len(header)
    num_chars = len(msg)

    # Pandas 3.x não aceita ndarray diretamente em fillna(value=...).
    # Por isso criamos Series alinhadas ao índice antes de preencher valores ausentes.
    seq_idx = pd.to_numeric(out["sequence_index"], errors="coerce").fillna(-1).astype(int)

    inferred_kind = pd.Series(
        np.where(seq_idx < header_len, "HEADER", "PAYLOAD"),
        index=out.index,
        dtype="object",
    )
    if "sequence_kind" not in out.columns:
        out["sequence_kind"] = inferred_kind
    else:
        out["sequence_kind"] = out["sequence_kind"].astype("object")
        out.loc[out["sequence_kind"].isna(), "sequence_kind"] = inferred_kind.loc[out["sequence_kind"].isna()]

    payload_index = seq_idx - header_len
    inferred_payload_index = pd.Series(np.where(payload_index >= 0, payload_index, -1), index=out.index).astype(int)
    inferred_char_index = pd.Series(np.where(payload_index >= 0, payload_index % num_chars, -1), index=out.index).astype(int)
    inferred_bit_in_char = pd.Series(np.where(payload_index >= 0, payload_index // num_chars, -1), index=out.index).astype(int)

    if "payload_index" not in out.columns:
        out["payload_index"] = inferred_payload_index
    else:
        out["payload_index"] = pd.to_numeric(out["payload_index"], errors="coerce")
        out.loc[out["payload_index"].isna(), "payload_index"] = inferred_payload_index.loc[out["payload_index"].isna()]
        out["payload_index"] = out["payload_index"].astype(int)

    if "char_index" not in out.columns:
        out["char_index"] = inferred_char_index
    else:
        out["char_index"] = pd.to_numeric(out["char_index"], errors="coerce")
        out.loc[out["char_index"].isna(), "char_index"] = inferred_char_index.loc[out["char_index"].isna()]
        out["char_index"] = out["char_index"].astype(int)

    if "bit_in_char" not in out.columns:
        out["bit_in_char"] = inferred_bit_in_char
    else:
        out["bit_in_char"] = pd.to_numeric(out["bit_in_char"], errors="coerce")
        out.loc[out["bit_in_char"].isna(), "bit_in_char"] = inferred_bit_in_char.loc[out["bit_in_char"].isna()]
        out["bit_in_char"] = out["bit_in_char"].astype(int)

    inferred_char_sent = out["char_index"].map(lambda i: msg[int(i)] if 0 <= int(i) < num_chars else "")
    if "char_sent" not in out.columns:
        out["char_sent"] = inferred_char_sent
    else:
        out["char_sent"] = out["char_sent"].astype("object")
        missing_char = out["char_sent"].isna() | (out["char_sent"].astype(str) == "")
        out.loc[missing_char, "char_sent"] = inferred_char_sent.loc[missing_char]

    return out


def aggregate_blocks(df: pd.DataFrame, mode: str, feature_mode: str, by_cycle: bool = False) -> pd.DataFrame:
    d = apply_mode_filter(df, mode).copy()
    if len(d) == 0:
        return pd.DataFrame()
    group_cols = ["dataset", "sequence_index"]
    if by_cycle:
        group_cols = ["dataset", "cycle", "sequence_index"]
    rows = []
    for key, g in d.groupby(group_cols, sort=True):
        g = g.sort_values(["shot_index"] if "shot_index" in g.columns else ["sequence_index"])
        feat = spy_feature_vector(g, mode=feature_mode)
        if not feat:
            continue
        first = g.iloc[0]
        row = {
            "dataset": str(first["dataset"]),
            "mode": mode,
            "sequence_index": int(first["sequence_index"]),
            "sequence_kind": str(first.get("sequence_kind", "")),
            "payload_index": int(first.get("payload_index", -1)),
            "char_index": int(first.get("char_index", -1)),
            "bit_in_char": int(first.get("bit_in_char", -1)),
            "bit_sent": int(first.get("bit_sent", -1)),
        }
        if by_cycle:
            row["cycle"] = int(first.get("cycle", 0))
        row.update(feat)
        rows.append(row)
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# Decoder hard e soft
# -----------------------------------------------------------------------------

@dataclass
class Calibration:
    fcols: List[str]
    mu: np.ndarray
    sd: np.ndarray
    sig0: np.ndarray
    sig1: np.ndarray
    ok: bool
    reason: str = "ok"


def calibrate_from_header(blocks: pd.DataFrame, header: str, feature_mode: str) -> Calibration:
    fcols = [c for c in feature_columns(feature_mode) if c in blocks.columns]
    if not fcols:
        return Calibration([], np.array([]), np.array([]), np.array([]), np.array([]), False, "sem features")

    header_blocks = blocks[blocks["sequence_index"] < len(header)].copy()
    if len(header_blocks) < 4:
        return Calibration(fcols, np.array([]), np.array([]), np.array([]), np.array([]), False, "header insuficiente")

    # Usa bit_sent do CSV quando presente; se não, usa string header por sequence_index.
    header_blocks["header_bit"] = header_blocks["sequence_index"].map(lambda i: int(header[int(i)]))
    h0 = header_blocks[header_blocks["header_bit"] == 0]
    h1 = header_blocks[header_blocks["header_bit"] == 1]
    if len(h0) < 2 or len(h1) < 2:
        return Calibration(fcols, np.array([]), np.array([]), np.array([]), np.array([]), False, "header sem 0/1 suficientes")

    all_cal = pd.concat([h0, h1], ignore_index=True)
    X = all_cal[fcols].astype(float).replace([np.inf, -np.inf], np.nan).fillna(0).to_numpy()
    mu = np.mean(X, axis=0)
    sd = np.std(X, axis=0)
    sd[sd == 0] = 1.0
    sig0 = (h0[fcols].astype(float).replace([np.inf, -np.inf], np.nan).fillna(0).to_numpy().mean(axis=0) - mu) / sd
    sig1 = (h1[fcols].astype(float).replace([np.inf, -np.inf], np.nan).fillna(0).to_numpy().mean(axis=0) - mu) / sd
    return Calibration(fcols, mu, sd, sig0, sig1, True)


def normalized_vector(row: pd.Series, cal: Calibration) -> np.ndarray:
    x = row[cal.fcols].astype(float).replace([np.inf, -np.inf], np.nan).fillna(0).to_numpy()
    return (x - cal.mu) / cal.sd


def bit_costs_for_row(row: pd.Series, cal: Calibration, distance_power: float = 2.0) -> Tuple[float, float, int, float]:
    """Retorna (cost0, cost1, hard_bit, confidence_margin). Menor custo vence."""
    x = normalized_vector(row, cal)
    d0 = float(np.linalg.norm(x - cal.sig0))
    d1 = float(np.linalg.norm(x - cal.sig1))
    cost0 = d0 ** distance_power
    cost1 = d1 ** distance_power
    hard = 0 if cost0 <= cost1 else 1
    margin = abs(cost1 - cost0)
    return cost0, cost1, hard, margin


def hard_decode(blocks: pd.DataFrame, message: str, header: str, feature_mode: str) -> Dict[str, object]:
    msg = normalize_message(message)
    manifest = build_manifest(msg, header)
    cal = calibrate_from_header(blocks, header, feature_mode)
    if not cal.ok:
        return {"ok": False, "reason": cal.reason, "decoded_message": ""}

    payload = blocks[blocks["sequence_index"] >= len(header)].sort_values("sequence_index")
    bits = ""
    bit_rows = []
    for _, row in payload.iterrows():
        c0, c1, hard, margin = bit_costs_for_row(row, cal)
        bits += str(hard)
        bit_rows.append({
            "sequence_index": int(row["sequence_index"]),
            "bit_true": int(row.get("bit_sent", -1)),
            "bit_pred_hard": hard,
            "cost0": c0,
            "cost1": c1,
            "margin": margin,
        })

    raw_blocks = reverter_interleaving(bits, len(msg))
    chars = []
    corrected_count = 0
    corrected_blocks = []
    syndromes = []
    for b9 in raw_blocks:
        bits5, syndrome, corrected, fixed = decodificar_hamming_9_5_hard(b9)
        idx = int(bits5, 2) if len(bits5) == 5 else 999
        chars.append(ALFABETO[idx] if 0 <= idx < len(ALFABETO) else "?")
        corrected_count += int(corrected)
        corrected_blocks.append(fixed)
        syndromes.append(syndrome)
    decoded = "".join(chars)
    expected_bits = manifest["payload_interleaved"]
    bit_acc = float(np.mean([a == b for a, b in zip(bits, expected_bits)])) if expected_bits else float("nan")
    char_acc = float(np.mean([a == b for a, b in zip(decoded, msg)])) if msg else float("nan")

    return {
        "ok": True,
        "decoder": "hard_vector",
        "decoded_message": decoded,
        "expected_message": msg,
        "bits_received": bits,
        "bits_expected": expected_bits,
        "payload_bit_accuracy": bit_acc,
        "char_accuracy": char_acc,
        "hamming_blocks_raw": raw_blocks,
        "hamming_blocks_corrected": corrected_blocks,
        "hamming_syndromes": syndromes,
        "hamming_corrected_count": corrected_count,
        "bit_rows": bit_rows,
        "reason": "ok",
    }


def soft_decode(blocks: pd.DataFrame, message: str, header: str, feature_mode: str, distance_power: float = 2.0) -> Dict[str, object]:
    """Soft-decision Hamming:
    - calcula custo de cada bit observado ser 0/1 via distância vetorial;
    - para cada caractere, testa todos os codewords válidos do alfabeto Janus;
    - escolhe o caractere com menor custo total.
    """
    msg = normalize_message(message)
    manifest = build_manifest(msg, header)
    cal = calibrate_from_header(blocks, header, feature_mode)
    if not cal.ok:
        return {"ok": False, "reason": cal.reason, "decoded_message": ""}

    payload = blocks[blocks["sequence_index"] >= len(header)].copy().sort_values("sequence_index")
    if len(payload) < len(msg) * 9:
        return {"ok": False, "reason": f"payload insuficiente: {len(payload)} blocos", "decoded_message": ""}

    # Custo por payload_index: (cost0, cost1, hard, margin)
    cost_map: Dict[Tuple[int, int], Dict[str, float]] = {}
    hard_bits_interleaved = ""
    bit_rows = []
    for _, row in payload.iterrows():
        seq = int(row["sequence_index"])
        payload_index = seq - len(header)
        char_idx = payload_index % len(msg)
        bit_idx = payload_index // len(msg)
        c0, c1, hard, margin = bit_costs_for_row(row, cal, distance_power=distance_power)
        cost_map[(char_idx, bit_idx)] = {"cost0": c0, "cost1": c1, "hard": hard, "margin": margin}
        hard_bits_interleaved += str(hard)
        bit_rows.append({
            "sequence_index": seq,
            "payload_index": payload_index,
            "char_index": char_idx,
            "bit_in_char": bit_idx,
            "bit_true": int(row.get("bit_sent", -1)),
            "bit_pred_hard": hard,
            "cost0": c0,
            "cost1": c1,
            "margin": margin,
        })

    book = valid_codebook()
    decoded_chars: List[str] = []
    selected_codes: List[str] = []
    char_rows = []
    for char_idx in range(len(msg)):
        candidates = []
        for ch, meta in book.items():
            code9 = meta["code9"]
            cost = 0.0
            missing = 0
            for bit_idx, expected_bit in enumerate(code9):
                item = cost_map.get((char_idx, bit_idx))
                if item is None:
                    missing += 1
                    cost += 999.0
                    continue
                cost += item["cost1" if expected_bit == "1" else "cost0"]
            candidates.append((cost, missing, ch, code9, meta["bits5"]))
        candidates.sort(key=lambda x: (x[0], x[1]))
        best = candidates[0]
        second = candidates[1] if len(candidates) > 1 else (float("nan"), 0, "", "", "")
        decoded_chars.append(best[2])
        selected_codes.append(best[3])
        char_rows.append({
            "char_index": char_idx,
            "expected_char": msg[char_idx],
            "decoded_char": best[2],
            "selected_code9": best[3],
            "selected_bits5": best[4],
            "best_cost": float(best[0]),
            "second_char": second[2],
            "second_code9": second[3],
            "second_cost": float(second[0]),
            "soft_margin": float(second[0] - best[0]),
            "ok_char": best[2] == msg[char_idx],
        })

    decoded = "".join(decoded_chars)
    # Reinterleava os codewords escolhidos para comparar com payload esperado.
    selected_interleaved = aplicar_interleaving(selected_codes)
    expected_bits = manifest["payload_interleaved"]
    bit_acc = float(np.mean([a == b for a, b in zip(selected_interleaved, expected_bits)])) if expected_bits else float("nan")
    char_acc = float(np.mean([a == b for a, b in zip(decoded, msg)])) if msg else float("nan")

    return {
        "ok": True,
        "decoder": "soft_vector_codebook",
        "decoded_message": decoded,
        "expected_message": msg,
        "bits_received": selected_interleaved,
        "hard_bits_interleaved": hard_bits_interleaved,
        "bits_expected": expected_bits,
        "payload_bit_accuracy": bit_acc,
        "char_accuracy": char_acc,
        "selected_codewords": selected_codes,
        "hamming_corrected_count": np.nan,
        "char_rows": char_rows,
        "bit_rows": bit_rows,
        "reason": "ok",
    }


# -----------------------------------------------------------------------------
# Métricas e relatório
# -----------------------------------------------------------------------------

def markdown_table(df: pd.DataFrame, index: bool = False) -> str:
    if df is None or df.empty:
        return "Sem dados."
    try:
        return df.to_markdown(index=index)
    except Exception:
        return "``\n" + df.to_csv(index=index) + "\n```"


def summarize_shots(df: pd.DataFrame, modes: Sequence[str]) -> pd.DataFrame:
    rows = []
    for dataset in sorted(df["dataset"].astype(str).unique()):
        dd = df[df["dataset"].astype(str) == dataset]
        for mode in modes:
            d = apply_mode_filter(dd, mode)
            if len(d) == 0:
                continue
            for bit in [0, 1]:
                b = d[d["bit_sent"].astype(int) == bit]
                if len(b) == 0:
                    continue
                spies = b[SPY_COLUMNS].astype(float)
                rows.append({
                    "dataset": dataset,
                    "mode": mode,
                    "bit_sent": bit,
                    "n": len(b),
                    "consenso_mean": float(spies.sum(axis=1).mean()),
                    "espiao_1_mean": float(spies["espiao_1"].mean()),
                    "espiao_2_mean": float(spies["espiao_2"].mean()),
                    "espiao_3_mean": float(spies["espiao_3"].mean()),
                    "e1_minus_e2": float(spies["espiao_1"].mean() - spies["espiao_2"].mean()),
                    "e2_minus_e3": float(spies["espiao_2"].mean() - spies["espiao_3"].mean()),
                    "q1_rate": float(b["q1_futuro"].mean()) if "q1_futuro" in b.columns else np.nan,
                    "q0_rate": float(b["q0_passado"].mean()) if "q0_passado" in b.columns else np.nan,
                })
    return pd.DataFrame(rows)


def run_decode_suite(df: pd.DataFrame, message: str, header: str, feature_mode: str, modes: Sequence[str], distance_power: float, by_cycle: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    decode_rows = []
    char_detail_rows = []
    bit_detail_rows = []
    block_rows = []
    datasets = sorted(df["dataset"].astype(str).unique())

    for dataset in datasets:
        dd = df[df["dataset"].astype(str) == dataset]
        for mode in modes:
            if by_cycle:
                blocks_all = aggregate_blocks(dd, mode, feature_mode, by_cycle=True)
                if blocks_all.empty:
                    continue
                for cycle, blocks in blocks_all.groupby("cycle", sort=True):
                    _append_decode_results(decode_rows, char_detail_rows, bit_detail_rows, block_rows, blocks, dataset, mode, message, header, feature_mode, distance_power, cycle=int(cycle))
            else:
                blocks = aggregate_blocks(dd, mode, feature_mode, by_cycle=False)
                if blocks.empty:
                    continue
                _append_decode_results(decode_rows, char_detail_rows, bit_detail_rows, block_rows, blocks, dataset, mode, message, header, feature_mode, distance_power, cycle=None)

    return pd.DataFrame(decode_rows), pd.DataFrame(char_detail_rows), pd.DataFrame(bit_detail_rows), pd.DataFrame(block_rows)


def _append_decode_results(decode_rows, char_detail_rows, bit_detail_rows, block_rows, blocks, dataset, mode, message, header, feature_mode, distance_power, cycle: Optional[int]) -> None:
    for _, r in blocks.iterrows():
        row = r.to_dict()
        row["cycle_scope"] = "aggregate" if cycle is None else "cycle"
        block_rows.append(row)

    for decoder_name, func in [("hard_vector", hard_decode), ("soft_vector_codebook", soft_decode)]:
        if decoder_name == "soft_vector_codebook":
            dec = func(blocks, message, header, feature_mode, distance_power=distance_power)
        else:
            dec = func(blocks, message, header, feature_mode)
        row = {
            "dataset": dataset,
            "mode": mode,
            "cycle": "aggregate" if cycle is None else int(cycle),
            "decoder": decoder_name,
            "decoded_message": dec.get("decoded_message", ""),
            "expected_message": normalize_message(message),
            "payload_bit_accuracy": dec.get("payload_bit_accuracy", np.nan),
            "char_accuracy": dec.get("char_accuracy", np.nan),
            "bits_received": dec.get("bits_received", ""),
            "hamming_corrected_count": dec.get("hamming_corrected_count", np.nan),
            "status": dec.get("reason", ""),
        }
        decode_rows.append(row)
        for cr in dec.get("char_rows", []) if dec.get("ok") else []:
            char_detail_rows.append({"dataset": dataset, "mode": mode, "cycle": row["cycle"], "decoder": decoder_name, **cr})
        for br in dec.get("bit_rows", []) if dec.get("ok") else []:
            bit_detail_rows.append({"dataset": dataset, "mode": mode, "cycle": row["cycle"], "decoder": decoder_name, **br})


def sham_test(decode_results: pd.DataFrame, message: str) -> pd.DataFrame:
    """Controle simples de pareidolia baseado nos decodes produzidos.
    Não substitui randomização estatística; apenas resume hit exato por dataset/mode/decoder.
    """
    msg = normalize_message(message)
    rows = []
    for (dataset, mode, decoder), g in decode_results.groupby(["dataset", "mode", "decoder"], sort=True):
        exact_hits = int((g["decoded_message"] == msg).sum())
        best_idx = g["char_accuracy"].astype(float).idxmax()
        best = g.loc[best_idx]
        rows.append({
            "dataset": dataset,
            "mode": mode,
            "decoder": decoder,
            "n_decodes": len(g),
            "exact_message_hits": exact_hits,
            "best_char_accuracy": float(best["char_accuracy"]),
            "best_decoded_message": best["decoded_message"],
        })
    return pd.DataFrame(rows)


def cmd_analyze(args) -> int:
    message = normalize_message(args.message)
    manifest = build_manifest(message, args.header)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print("\n==========================================================")
    print(" 🧠 PROJETO JANUS V9.1: RAW SOFT DECODER")
    print("==========================================================")
    print("[*] Arquivos:")
    df = load_inputs(args.input)
    df = add_sequence_metadata_if_needed(df, message, args.header)
    print(f"[*] Linhas totais : {len(df):,}".replace(",", "."))
    print(f"[*] Datasets      : {', '.join(sorted(df['dataset'].astype(str).unique()))}")
    print(f"[*] Mensagem      : {message}")
    print(f"[*] Header        : {args.header} ({len(args.header)} bits)")
    print(f"[*] Feature mode  : {args.feature_mode}")

    modes = ["RAW", "POST_Q1_1"]
    if args.include_q1_zero_diagnostic:
        modes.append("POST_Q1_0")

    shot_summary = summarize_shots(df, modes)
    shot_summary.to_csv(outdir / "v91_shot_level_summary.csv", index=False)

    agg_decodes, agg_char, agg_bit, agg_blocks = run_decode_suite(
        df, message, args.header, args.feature_mode, modes, args.distance_power, by_cycle=False
    )
    cyc_decodes, cyc_char, cyc_bit, cyc_blocks = run_decode_suite(
        df, message, args.header, args.feature_mode, modes, args.distance_power, by_cycle=True
    )

    agg_decodes.to_csv(outdir / "v91_decode_results_aggregate.csv", index=False)
    cyc_decodes.to_csv(outdir / "v91_decode_results_by_cycle.csv", index=False)
    agg_char.to_csv(outdir / "v91_char_details_aggregate.csv", index=False)
    cyc_char.to_csv(outdir / "v91_char_details_by_cycle.csv", index=False)
    agg_bit.to_csv(outdir / "v91_bit_details_aggregate.csv", index=False)
    cyc_bit.to_csv(outdir / "v91_bit_details_by_cycle.csv", index=False)
    agg_blocks.to_csv(outdir / "v91_block_features_aggregate.csv", index=False)
    cyc_blocks.to_csv(outdir / "v91_block_features_by_cycle.csv", index=False)

    sham = sham_test(pd.concat([agg_decodes, cyc_decodes], ignore_index=True), message)
    sham.to_csv(outdir / "v91_decode_hit_summary.csv", index=False)

    report = []
    report.append("# JANUS V9.1 — RAW Soft Decoder")
    report.append("")
    report.append(f"Mensagem esperada: **{message}**")
    report.append(f"Linhas analisadas: **{len(df)}**")
    report.append(f"Header: `{args.header}`")
    report.append(f"Feature mode: `{args.feature_mode}`")
    report.append(f"Distance power: `{args.distance_power}`")
    report.append("")
    report.append("## Sequência codificada")
    report.append("```json")
    report.append(json.dumps(manifest, ensure_ascii=False, indent=2))
    report.append("```")
    report.append("")
    report.append("## Resumo shot-level")
    report.append(markdown_table(shot_summary, index=False))
    report.append("")
    report.append("## Decodificação agregada")
    cols = ["dataset", "mode", "cycle", "decoder", "decoded_message", "expected_message", "payload_bit_accuracy", "char_accuracy", "hamming_corrected_count", "status"]
    report.append(markdown_table(agg_decodes[cols] if not agg_decodes.empty else agg_decodes, index=False))
    report.append("")
    report.append("## Decodificação por ciclo")
    report.append(markdown_table(cyc_decodes[cols] if not cyc_decodes.empty else cyc_decodes, index=False))
    report.append("")
    report.append("## Hit summary")
    report.append(markdown_table(sham, index=False))
    report.append("")
    report.append("## Observação metodológica")
    report.append("- `RAW` não usa `q1_futuro`, `q0_passado` nem pós-seleção.")
    report.append("- `POST_Q1_1` usa `q1_futuro == 1` apenas como filtro, nunca como feature.")
    report.append("- O decoder `soft_vector_codebook` testa todos os codewords Hamming(9,5) válidos do alfabeto Janus e escolhe o menor custo vetorial.")
    report.append("- Para alegação forte, o sucesso deve aparecer no REAL e falhar em NULO/PHAN_STRICT.")

    report_path = outdir / "JANUS_V91_SOFT_DECODER_REPORT.md"
    report_path.write_text("\n".join(report), encoding="utf-8")

    print("\n" + "\n".join(report))
    print("\n==========================================================")
    print(" V9.1 concluído")
    print("==========================================================")
    print(f"Relatório: {report_path}")
    print(f"Decode agregado: {outdir / 'v91_decode_results_aggregate.csv'}")
    print(f"Decode ciclos  : {outdir / 'v91_decode_results_by_cycle.csv'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Janus V9.1 — decoder RAW vetorial + soft-decision Hamming")
    p.add_argument("--input", required=True, help="CSV ou glob. Ex: janus_run/JANUS_V9_RAW_*.csv")
    p.add_argument("--message", default="JANUS")
    p.add_argument("--header", default=DEFAULT_HEADER)
    p.add_argument("--outdir", default="janus_v91_soft_analysis")
    p.add_argument("--feature-mode", choices=["minimal", "v91"], default="v91")
    p.add_argument("--distance-power", type=float, default=2.0, help="2.0 = distância quadrática; 1.0 = distância linear")
    p.add_argument("--include-q1-zero-diagnostic", action="store_true")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return cmd_analyze(args)


if __name__ == "__main__":
    raise SystemExit(main())
