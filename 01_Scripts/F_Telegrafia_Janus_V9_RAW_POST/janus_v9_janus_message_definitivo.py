#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROJETO JANUS V9 — Mensagem curta JANUS: extração + análise RAW/POST

Objetivo:
  - Enviar uma mensagem curta usando o alfabeto Baudot customizado do protocolo Janus.
  - Gerar dados em três regimes: REAL, NULO e PHAN_STRICT_POSTHOC.
  - Analisar a recuperação com pós-seleção q1_futuro == 1.
  - Analisar a recuperação em massa bruta, SEM pós-seleção, usando apenas os qubits espiões.

Regras de auditoria embutidas:
  - Features principais usam SOMENTE espiao_1, espiao_2, espiao_3 e consenso.
  - q1_futuro só é permitido como filtro no modo postselected, nunca como feature.
  - q0_passado nunca é usado como feature por padrão.
  - Ordem dos circuitos pode ser randomizada para reduzir drift temporal.
  - PHAN_STRICT_POSTHOC roda circuito sem marreta, mas conserva os rótulos de mensagem por índice,
    servindo como controle contra pareidolia, sequência e drift.

Instalação:
  pip install qiskit qiskit-ibm-runtime pandas numpy scipy scikit-learn python-dotenv

Exemplo de extração:
  python janus_v9_janus_message_definitivo.py extract --backend ibm_fez --message JANUS \
    --shots 8192 --cycles 2 --outdir janus_v9_fez --run-tag FEZ_JANUS_V9 \
    --include-nulo --include-phan-strict --randomize-order

Exemplo de análise:
  python janus_v9_janus_message_definitivo.py analyze --input "janus_v9_fez/JANUS_V9_RAW_ibm_fez_FEZ_JANUS_V9.csv" \
    --message JANUS --window 16 --n-perm 1000 --outdir janus_v9_analysis_fez
"""

from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import math
import os
import random
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

# sklearn/scipy são usados apenas na análise.

ALFABETO = " ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_HEADER = "0101"
SPY_COLUMNS = ["espiao_1", "espiao_2", "espiao_3"]
RAW_COLUMNS = [
    "run_tag",
    "backend",
    "job_id",
    "dataset",
    "cycle",
    "pub_order",
    "sequence_index",
    "sequence_kind",
    "payload_index",
    "char_index",
    "char_sent",
    "bit_in_char",
    "bit_sent",
    "shot_index",
    "q1_futuro",
    "q0_passado",
    "espiao_1",
    "espiao_2",
    "espiao_3",
    "circuit_hash",
    "transpile_hash",
    "created_utc",
]


@dataclass
class SequenceEntry:
    sequence_index: int
    sequence_kind: str  # HEADER ou PAYLOAD
    payload_index: int
    char_index: int
    char_sent: str
    bit_in_char: int
    bit_sent: int


def now_utc_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def safe_mkdir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def circuit_hash(qc) -> str:
    try:
        return hash_text(qc.qasm())
    except Exception:
        return hash_text(str(qc))


def normalize_message(message: str) -> str:
    msg = "".join(ch for ch in message.upper() if ch in ALFABETO)
    if not msg:
        raise ValueError("Mensagem vazia ou fora do alfabeto permitido.")
    return msg


def char_para_5bit(char: str) -> str:
    idx = ALFABETO.find(char.upper())
    if idx == -1:
        idx = 0
    return format(idx, "05b")


def codificar_hamming_9_5(bits_5: str) -> str:
    """Hamming (9,5), compatível com o transmissor/receptor V8."""
    if len(bits_5) != 5 or any(b not in "01" for b in bits_5):
        raise ValueError(f"bits_5 inválido: {bits_5!r}")
    d = [int(x) for x in bits_5]
    p1 = d[0] ^ d[1] ^ d[3] ^ d[4]
    p2 = d[0] ^ d[2] ^ d[3]
    p4 = d[1] ^ d[2] ^ d[3]
    p8 = d[4]
    return f"{p1}{p2}{d[0]}{p4}{d[1]}{d[2]}{d[3]}{p8}{d[4]}"


def decodificar_hamming_9_5(bloco_9: str) -> Tuple[str, int, bool, str]:
    """Retorna (bits_5, syndrome, corrected, bloco_corrigido)."""
    if len(bloco_9) != 9 or any(b not in "01" for b in bloco_9):
        return "00000", -1, False, bloco_9
    b = [int(x) for x in bloco_9]
    s1 = b[0] ^ b[2] ^ b[4] ^ b[6] ^ b[8]
    s2 = b[1] ^ b[2] ^ b[5] ^ b[6]
    s4 = b[3] ^ b[4] ^ b[5] ^ b[6]
    s8 = b[7] ^ b[8]
    syndrome = s1 * 1 + s2 * 2 + s4 * 4 + s8 * 8
    corrected = False
    if syndrome != 0 and syndrome <= 9:
        b[syndrome - 1] ^= 1
        corrected = True
    dados_5_bits = f"{b[2]}{b[4]}{b[5]}{b[6]}{b[8]}"
    return dados_5_bits, syndrome, corrected, "".join(str(x) for x in b)


def aplicar_interleaving(blocos_9bits: Sequence[str]) -> str:
    resultado = ""
    for bit_idx in range(9):
        for bloco in blocos_9bits:
            resultado += bloco[bit_idx]
    return resultado


def reverter_interleaving(bits_recebidos: str, num_caracteres: int) -> List[str]:
    blocos = ["" for _ in range(num_caracteres)]
    idx = 0
    for bit_idx in range(9):
        for char_idx in range(num_caracteres):
            if idx < len(bits_recebidos):
                blocos[char_idx] += bits_recebidos[idx]
            idx += 1
    return blocos


def build_sequence(message: str, header: str = DEFAULT_HEADER) -> Tuple[List[SequenceEntry], Dict[str, object]]:
    message = normalize_message(message)
    bits_base = [char_para_5bit(c) for c in message]
    blocos_hamming = [codificar_hamming_9_5(b) for b in bits_base]
    payload_interleaved = aplicar_interleaving(blocos_hamming)
    sequence_bits = header + payload_interleaved

    entries: List[SequenceEntry] = []
    for i, b in enumerate(sequence_bits):
        if i < len(header):
            entries.append(
                SequenceEntry(
                    sequence_index=i,
                    sequence_kind="HEADER",
                    payload_index=-1,
                    char_index=-1,
                    char_sent="",
                    bit_in_char=-1,
                    bit_sent=int(b),
                )
            )
        else:
            payload_index = i - len(header)
            # A ordem do interleaving é bit_idx externo, char_idx interno.
            num_chars = len(message)
            bit_idx_hamming = payload_index // num_chars
            char_index = payload_index % num_chars
            entries.append(
                SequenceEntry(
                    sequence_index=i,
                    sequence_kind="PAYLOAD",
                    payload_index=payload_index,
                    char_index=char_index,
                    char_sent=message[char_index],
                    bit_in_char=bit_idx_hamming,
                    bit_sent=int(b),
                )
            )
    manifest = {
        "message": message,
        "alphabet": ALFABETO,
        "header": header,
        "bits_5": bits_base,
        "hamming_9_5_blocks": blocos_hamming,
        "payload_interleaved": payload_interleaved,
        "sequence_bits": sequence_bits,
        "num_sequence_bits": len(sequence_bits),
        "num_payload_bits": len(payload_interleaved),
    }
    return entries, manifest


def construir_circuito_bit(valor_bit: int, dataset: str, theta: float, total_qubits: int):
    """Constrói circuito de 5 qubits compatível com o V8.

    REAL: H(q0), CX(q0,q1), espiões, RX(pi/2) se bit=1, mede q1/q0.
    NULO: H(q0), H(q1), sem CX, espiões, RX(pi/2) se bit=1, mede q1/q0.
    PHAN_STRICT_POSTHOC: H(q0), CX(q0,q1), espiões, SEM RX em todos os bits.
    """
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(total_qubits, total_qubits)
    qc.h(0)

    if dataset == "REAL":
        qc.cx(0, 1)
    elif dataset == "NULO":
        qc.h(1)
    elif dataset == "PHAN_STRICT_POSTHOC":
        qc.cx(0, 1)
    else:
        raise ValueError(f"dataset desconhecido: {dataset}")

    qc.barrier()
    qc.cry(theta, 0, 2)
    qc.measure(2, 2)
    qc.cry(theta, 0, 3)
    qc.measure(3, 3)
    qc.cry(theta, 0, 4)
    qc.measure(4, 4)
    qc.barrier()

    if dataset in ("REAL", "NULO") and int(valor_bit) == 1:
        qc.rx(np.pi / 2, 1)

    qc.measure(1, 1)
    qc.measure(0, 0)
    return qc


def bitstring_to_row_bits(string_bin: str) -> Tuple[int, int, int, int, int]:
    # Compatível com seu código V8: string_bits[::-1] para obter c0,c1,c2,c3,c4.
    s = string_bin[::-1]
    return int(s[1]), int(s[0]), int(s[2]), int(s[3]), int(s[4])


def cmd_extract(args) -> int:
    if load_dotenv is not None:
        load_dotenv()

    try:
        from qiskit import transpile
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
    except Exception as e:
        print("[X] Falha ao importar Qiskit/Qiskit IBM Runtime.")
        print("    Instale com: pip install qiskit qiskit-ibm-runtime python-dotenv")
        print(f"    Erro: {e}")
        return 2

    token = args.ibm_token or os.getenv("IBM_QUANTUM_TOKEN")
    if not token:
        print("[X] IBM_QUANTUM_TOKEN não encontrado. Defina no .env ou no ambiente.")
        return 2

    message = normalize_message(args.message)
    entries, manifest = build_sequence(message, args.header)
    outdir = safe_mkdir(args.outdir)
    run_tag = args.run_tag or f"JANUS_V9_{args.backend}_{now_utc_compact()}"
    created_utc = datetime.now(timezone.utc).isoformat()

    datasets = ["REAL"]
    if args.include_nulo:
        datasets.append("NULO")
    if args.include_phan_strict:
        datasets.append("PHAN_STRICT_POSTHOC")

    theta = float(eval(args.theta, {"np": np, "pi": np.pi, "math": math})) if isinstance(args.theta, str) else float(args.theta)

    print("\n==========================================================")
    print(" 📡 PROJETO JANUS V9: EXTRAÇÃO MENSAGEM JANUS")
    print("==========================================================")
    print(f"[*] Backend        : {args.backend}")
    print(f"[*] Mensagem       : {message}")
    print(f"[*] Header         : {args.header}")
    print(f"[*] Bits sequência : {manifest['sequence_bits']}")
    print(f"[*] Circuitos base : {len(entries)} por ciclo/dataset")
    print(f"[*] Cycles         : {args.cycles}")
    print(f"[*] Shots/circuito : {args.shots}")
    print(f"[*] Datasets       : {', '.join(datasets)}")
    print(f"[*] Random order   : {args.randomize_order}")
    print(f"[*] Run tag        : {run_tag}")

    service = QiskitRuntimeService(channel=args.channel, token=token)
    backend = service.backend(args.backend)
    sampler = Sampler(backend)

    tasks = []
    for cycle in range(args.cycles):
        for dataset in datasets:
            for entry in entries:
                tasks.append({
                    "cycle": cycle,
                    "dataset": dataset,
                    "entry": entry,
                })

    rng = random.Random(args.random_seed)
    if args.randomize_order:
        rng.shuffle(tasks)

    circuits = []
    meta_rows = []
    for pub_order, task in enumerate(tasks):
        e = task["entry"]
        qc = construir_circuito_bit(e.bit_sent, task["dataset"], theta, args.total_qubits)
        chash = circuit_hash(qc)
        circuits.append(qc)
        meta_rows.append({
            "pub_order": pub_order,
            "cycle": task["cycle"],
            "dataset": task["dataset"],
            **asdict(e),
            "circuit_hash": chash,
        })

    print(f"[*] Transpilando {len(circuits)} circuitos...")
    transpile_kwargs = {
        "backend": backend,
        "optimization_level": args.optimization_level,
        "seed_transpiler": args.seed_transpiler,
    }
    if args.initial_layout:
        transpile_kwargs["initial_layout"] = [int(x.strip()) for x in args.initial_layout.split(",") if x.strip()]
    circuits_isa = transpile(circuits, **transpile_kwargs)

    for i, cisa in enumerate(circuits_isa):
        meta_rows[i]["transpile_hash"] = circuit_hash(cisa)

    raw_path = outdir / f"JANUS_V9_RAW_{args.backend}_{run_tag}.csv"
    manifest_path = outdir / f"JANUS_V9_MANIFEST_{args.backend}_{run_tag}.json"
    meta_path = outdir / f"JANUS_V9_CIRCUIT_META_{args.backend}_{run_tag}.csv"

    print(f"[*] Salvando metadados: {meta_path}")
    pd.DataFrame(meta_rows).to_csv(meta_path, index=False)

    manifest.update({
        "run_tag": run_tag,
        "created_utc": created_utc,
        "backend": args.backend,
        "channel": args.channel,
        "theta": theta,
        "total_qubits": args.total_qubits,
        "shots": args.shots,
        "cycles": args.cycles,
        "datasets": datasets,
        "randomize_order": args.randomize_order,
        "random_seed": args.random_seed,
        "optimization_level": args.optimization_level,
        "seed_transpiler": args.seed_transpiler,
        "initial_layout": args.initial_layout,
        "raw_csv": str(raw_path),
        "meta_csv": str(meta_path),
    })
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[*] Rodando SamplerV2: {len(circuits_isa)} circuitos × {args.shots} shots...")
    t0 = time.time()
    job = sampler.run(circuits_isa, shots=args.shots)
    job_id = getattr(job, "job_id", lambda: "UNKNOWN")()
    print(f"[*] Job ID: {job_id}")
    result = job.result()
    print(f"[*] Resultado recebido em {(time.time() - t0):.1f}s")

    with raw_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RAW_COLUMNS)
        writer.writeheader()
        for i, circ_res in enumerate(result):
            m = meta_rows[i]
            try:
                bitstrings = circ_res.data.c.get_bitstrings()
            except Exception as e:
                raise RuntimeError(f"Não consegui ler bitstrings do resultado {i}: {e}")
            for shot_index, string_bin in enumerate(bitstrings):
                q1, q0, e1, e2, e3 = bitstring_to_row_bits(string_bin)
                writer.writerow({
                    "run_tag": run_tag,
                    "backend": args.backend,
                    "job_id": job_id,
                    "dataset": m["dataset"],
                    "cycle": m["cycle"],
                    "pub_order": m["pub_order"],
                    "sequence_index": m["sequence_index"],
                    "sequence_kind": m["sequence_kind"],
                    "payload_index": m["payload_index"],
                    "char_index": m["char_index"],
                    "char_sent": m["char_sent"],
                    "bit_in_char": m["bit_in_char"],
                    "bit_sent": m["bit_sent"],
                    "shot_index": shot_index,
                    "q1_futuro": q1,
                    "q0_passado": q0,
                    "espiao_1": e1,
                    "espiao_2": e2,
                    "espiao_3": e3,
                    "circuit_hash": m["circuit_hash"],
                    "transpile_hash": m["transpile_hash"],
                    "created_utc": created_utc,
                })
            if (i + 1) % max(1, len(result) // 10) == 0 or (i + 1) == len(result):
                print(f"    -> escrito {i + 1}/{len(result)} circuitos")

    print("\n==========================================================")
    print(" Extração concluída")
    print("==========================================================")
    print(f"Raw CSV  : {raw_path}")
    print(f"Manifest : {manifest_path}")
    print(f"Meta CSV : {meta_path}")
    return 0


def safe_skew(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    if len(x) < 3:
        return 0.0
    std = float(np.std(x))
    if std == 0.0:
        return 0.0
    z = (x - float(np.mean(x))) / std
    return float(np.mean(z ** 3))


def safe_kurtosis(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    if len(x) < 4:
        return 0.0
    std = float(np.std(x))
    if std == 0.0:
        return 0.0
    z = (x - float(np.mean(x))) / std
    return float(np.mean(z ** 4) - 3.0)


def feature_vector_from_df(df: pd.DataFrame, feature_mode: str = "full") -> Dict[str, float]:
    if len(df) == 0:
        return {}
    spies = df[SPY_COLUMNS].astype(float)
    cons = spies.sum(axis=1).to_numpy(dtype=float)
    e1 = spies["espiao_1"].to_numpy(dtype=float)
    e2 = spies["espiao_2"].to_numpy(dtype=float)
    e3 = spies["espiao_3"].to_numpy(dtype=float)

    def flicker(v: np.ndarray) -> float:
        return float(np.mean(np.abs(np.diff(v)))) if len(v) > 1 else 0.0

    out = {
        "n": float(len(df)),
        "cons_mean": float(np.mean(cons)),
        "cons_var": float(np.var(cons)),
        "cons_std": float(np.std(cons)),
        "cons_skew": safe_skew(cons),
        "cons_kurt": safe_kurtosis(cons),
        "cons_flicker": flicker(cons),
        "e1_mean": float(np.mean(e1)),
        "e2_mean": float(np.mean(e2)),
        "e3_mean": float(np.mean(e3)),
        "e1_var": float(np.var(e1)),
        "e2_var": float(np.var(e2)),
        "e3_var": float(np.var(e3)),
        "e1_flicker": flicker(e1),
        "e2_flicker": flicker(e2),
        "e3_flicker": flicker(e3),
    }
    if feature_mode == "basic":
        keys = ["n", "cons_mean", "cons_var", "cons_flicker", "e1_mean", "e2_mean", "e3_mean"]
        return {k: out[k] for k in keys}
    return out


def feature_columns(feature_mode: str = "full") -> List[str]:
    if feature_mode == "basic":
        return ["cons_mean", "cons_var", "cons_flicker", "e1_mean", "e2_mean", "e3_mean"]
    return [
        "cons_mean", "cons_var", "cons_std", "cons_skew", "cons_kurt", "cons_flicker",
        "e1_mean", "e2_mean", "e3_mean", "e1_var", "e2_var", "e3_var",
        "e1_flicker", "e2_flicker", "e3_flicker",
    ]


def apply_mode_filter(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    if mode == "RAW":
        return df
    if mode == "POST_Q1_1":
        return df[df["q1_futuro"].astype(int) == 1]
    if mode == "POST_Q1_0":
        return df[df["q1_futuro"].astype(int) == 0]
    raise ValueError(f"modo desconhecido: {mode}")


def aggregate_block_features(df: pd.DataFrame, mode: str, feature_mode: str) -> pd.DataFrame:
    d = apply_mode_filter(df, mode).copy()
    if len(d) == 0:
        return pd.DataFrame()
    d[SPY_COLUMNS] = d[SPY_COLUMNS].astype(int)
    rows = []
    group_cols = ["dataset", "sequence_index"]
    for (dataset, seq), g in d.groupby(group_cols, sort=True):
        g = g.sort_values(["cycle", "shot_index"])
        feat = feature_vector_from_df(g, feature_mode)
        if not feat:
            continue
        first = g.iloc[0]
        rows.append({
            "dataset": dataset,
            "mode": mode,
            "sequence_index": int(seq),
            "sequence_kind": first.get("sequence_kind", ""),
            "payload_index": int(first.get("payload_index", -1)),
            "char_index": int(first.get("char_index", -1)),
            "char_sent": first.get("char_sent", ""),
            "bit_in_char": int(first.get("bit_in_char", -1)),
            "bit_sent": int(first.get("bit_sent", 0)),
            **feat,
        })
    return pd.DataFrame(rows)


def aggregate_cycle_block_features(df: pd.DataFrame, mode: str, feature_mode: str) -> pd.DataFrame:
    d = apply_mode_filter(df, mode).copy()
    if len(d) == 0:
        return pd.DataFrame()
    d[SPY_COLUMNS] = d[SPY_COLUMNS].astype(int)
    rows = []
    group_cols = ["dataset", "cycle", "sequence_index"]
    for (dataset, cycle, seq), g in d.groupby(group_cols, sort=True):
        g = g.sort_values(["shot_index"])
        feat = feature_vector_from_df(g, feature_mode)
        if not feat:
            continue
        first = g.iloc[0]
        rows.append({
            "dataset": dataset,
            "cycle": int(cycle),
            "mode": mode,
            "sequence_index": int(seq),
            "sequence_kind": first.get("sequence_kind", ""),
            "payload_index": int(first.get("payload_index", -1)),
            "char_index": int(first.get("char_index", -1)),
            "char_sent": first.get("char_sent", ""),
            "bit_in_char": int(first.get("bit_in_char", -1)),
            "bit_sent": int(first.get("bit_sent", 0)),
            **feat,
        })
    return pd.DataFrame(rows)


def standardize_for_distance(X: np.ndarray) -> np.ndarray:
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X.reshape(1, -1)
    mu = np.nanmean(X, axis=0)
    sd = np.nanstd(X, axis=0)
    sd[sd == 0] = 1.0
    return (X - mu) / sd


def decode_from_block_features(blocks: pd.DataFrame, message: str, header: str, feature_mode: str) -> Dict[str, object]:
    message = normalize_message(message)
    if blocks.empty:
        return {"decoded_message": "", "ok": False, "reason": "sem blocos"}
    fcols = feature_columns(feature_mode)
    available = [c for c in fcols if c in blocks.columns]
    if not available:
        return {"decoded_message": "", "ok": False, "reason": "sem features"}

    # Handshake esperado: 0101. Usa seq 0/2 para assinatura 0 e 1/3 para assinatura 1.
    h0 = blocks[blocks["sequence_index"].isin([0, 2])]
    h1 = blocks[blocks["sequence_index"].isin([1, 3])]
    if len(h0) == 0 or len(h1) == 0:
        return {"decoded_message": "", "ok": False, "reason": "handshake insuficiente"}

    all_cal = pd.concat([h0, h1], ignore_index=True)
    mu = all_cal[available].astype(float).mean(axis=0).to_numpy()
    sd = all_cal[available].astype(float).std(axis=0).replace(0, 1).fillna(1).to_numpy()

    sig0 = ((h0[available].astype(float).mean(axis=0).to_numpy() - mu) / sd)
    sig1 = ((h1[available].astype(float).mean(axis=0).to_numpy() - mu) / sd)

    payload = blocks[blocks["sequence_kind"] == "PAYLOAD"].sort_values("sequence_index")
    bits = ""
    distances = []
    for _, row in payload.iterrows():
        x = ((row[available].astype(float).to_numpy() - mu) / sd)
        d0 = float(np.linalg.norm(x - sig0))
        d1 = float(np.linalg.norm(x - sig1))
        pred = "0" if d0 < d1 else "1"
        bits += pred
        distances.append({
            "sequence_index": int(row["sequence_index"]),
            "bit_true": int(row["bit_sent"]),
            "bit_pred": int(pred),
            "d0": d0,
            "d1": d1,
            "margin_d0_minus_d1": d0 - d1,
        })

    blocos = reverter_interleaving(bits, len(message))
    decoded_chars = []
    corrected_count = 0
    syndromes = []
    corrected_blocks = []
    for bloco in blocos:
        bits5, syndrome, corrected, corrected_block = decodificar_hamming_9_5(bloco)
        idx = int(bits5, 2) if len(bits5) == 5 else 999
        decoded_chars.append(ALFABETO[idx] if idx < len(ALFABETO) else "?")
        corrected_count += int(corrected)
        syndromes.append(syndrome)
        corrected_blocks.append(corrected_block)
    decoded = "".join(decoded_chars)

    expected_entries, expected_manifest = build_sequence(message, header)
    true_payload_bits = expected_manifest["payload_interleaved"]
    bit_acc = np.mean([a == b for a, b in zip(bits, true_payload_bits)]) if true_payload_bits else np.nan
    char_acc = np.mean([a == b for a, b in zip(decoded, message)]) if message else np.nan

    return {
        "ok": True,
        "decoded_message": decoded,
        "expected_message": message,
        "bits_received": bits,
        "bits_expected": true_payload_bits,
        "payload_bit_accuracy": float(bit_acc),
        "char_accuracy": float(char_acc),
        "hamming_blocks_raw": blocos,
        "hamming_blocks_corrected": corrected_blocks,
        "hamming_syndromes": syndromes,
        "hamming_corrected_count": int(corrected_count),
        "distance_rows": distances,
        "reason": "ok",
    }


def build_window_features(df: pd.DataFrame, mode: str, feature_mode: str, window: int, exclude_header: bool = True) -> pd.DataFrame:
    d = apply_mode_filter(df, mode).copy()
    if exclude_header:
        d = d[d["sequence_kind"] == "PAYLOAD"]
    if len(d) == 0:
        return pd.DataFrame()
    d[SPY_COLUMNS] = d[SPY_COLUMNS].astype(int)
    rows = []
    group_cols = ["dataset", "cycle", "sequence_index"]
    for (dataset, cycle, seq), g in d.groupby(group_cols, sort=True):
        g = g.sort_values("shot_index").reset_index(drop=True)
        n = len(g)
        for start in range(0, n - window + 1, window):
            w = g.iloc[start:start + window]
            if len(w) < window:
                continue
            feat = feature_vector_from_df(w, feature_mode)
            if not feat:
                continue
            first = w.iloc[0]
            rows.append({
                "dataset": dataset,
                "mode": mode,
                "cycle": int(cycle),
                "sequence_index": int(seq),
                "window_start": int(start),
                "bit_sent": int(first["bit_sent"]),
                "char_sent": first.get("char_sent", ""),
                "char_index": int(first.get("char_index", -1)),
                **feat,
            })
    return pd.DataFrame(rows)


def evaluate_binary_model(windows: pd.DataFrame, feature_mode: str, n_perm: int, random_seed: int, model_kind: str = "logreg") -> Dict[str, object]:
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score, confusion_matrix
    from sklearn.model_selection import GroupKFold, StratifiedKFold
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline

    if windows.empty or windows["bit_sent"].nunique() < 2:
        return {"ok": False, "reason": "dados insuficientes"}

    fcols = [c for c in feature_columns(feature_mode) if c in windows.columns]
    X = windows[fcols].astype(float).replace([np.inf, -np.inf], np.nan).fillna(0).to_numpy()
    y = windows["bit_sent"].astype(int).to_numpy()
    groups = windows["sequence_index"].astype(int).to_numpy()

    if model_kind == "logreg":
        model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, solver="liblinear", random_state=random_seed))
    elif model_kind == "rf":
        model = RandomForestClassifier(n_estimators=80, max_depth=8, n_jobs=-1, random_state=random_seed)
    else:
        raise ValueError(model_kind)

    unique_groups = np.unique(groups)
    if len(unique_groups) >= 4:
        splitter = GroupKFold(n_splits=min(5, len(unique_groups)))
        splits = list(splitter.split(X, y, groups))
    else:
        splitter = StratifiedKFold(n_splits=3, shuffle=True, random_state=random_seed)
        splits = list(splitter.split(X, y))

    y_true_all = []
    y_pred_all = []
    y_score_all = []
    for train_idx, test_idx in splits:
        model.fit(X[train_idx], y[train_idx])
        pred = model.predict(X[test_idx])
        if hasattr(model, "predict_proba"):
            score = model.predict_proba(X[test_idx])[:, 1]
        else:
            score = pred
        y_true_all.extend(y[test_idx].tolist())
        y_pred_all.extend(pred.tolist())
        y_score_all.extend(score.tolist())

    acc = float(accuracy_score(y_true_all, y_pred_all))
    bacc = float(balanced_accuracy_score(y_true_all, y_pred_all))
    try:
        auc = float(roc_auc_score(y_true_all, y_score_all))
    except Exception:
        auc = float("nan")
    cm = confusion_matrix(y_true_all, y_pred_all, labels=[0, 1])

    # Permutação agrupada: embaralha rótulos por sequência, preservando janelas internas.
    perm_p = float("nan")
    if n_perm > 0 and model_kind == "logreg":
        rng = np.random.default_rng(random_seed)
        observed = bacc
        seq_to_label = windows.groupby("sequence_index")["bit_sent"].first().to_dict()
        seqs = np.array(list(seq_to_label.keys()))
        labels = np.array([seq_to_label[s] for s in seqs])
        ge = 0
        for p in range(n_perm):
            shuffled = labels.copy()
            rng.shuffle(shuffled)
            map_label = dict(zip(seqs, shuffled))
            y_perm = windows["sequence_index"].map(map_label).astype(int).to_numpy()
            y_true_p = []
            y_pred_p = []
            for train_idx, test_idx in splits:
                model.fit(X[train_idx], y_perm[train_idx])
                pred = model.predict(X[test_idx])
                y_true_p.extend(y_perm[test_idx].tolist())
                y_pred_p.extend(pred.tolist())
            stat = float(balanced_accuracy_score(y_true_p, y_pred_p))
            if stat >= observed:
                ge += 1
            if (p + 1) in {1, 10, 100, n_perm} or ((p + 1) % max(1, n_perm // 10) == 0):
                print(f"      perm {p+1}/{n_perm} — {model_kind}")
        perm_p = float((ge + 1) / (n_perm + 1))

    return {
        "ok": True,
        "model": model_kind,
        "n_windows": int(len(windows)),
        "n_sequences": int(windows["sequence_index"].nunique()),
        "accuracy": acc,
        "balanced_accuracy": bacc,
        "auc": auc,
        "perm_p_grouped": perm_p,
        "cm_tn": int(cm[0, 0]),
        "cm_fp": int(cm[0, 1]),
        "cm_fn": int(cm[1, 0]),
        "cm_tp": int(cm[1, 1]),
        "reason": "ok",
    }


def markdown_table(df: pd.DataFrame, index: bool = False) -> str:
    try:
        return df.to_markdown(index=index)
    except Exception:
        return "```\n" + df.to_string(index=index) + "\n```"


def load_input_csvs(pattern: str) -> pd.DataFrame:
    files = sorted(glob.glob(pattern))
    if not files and Path(pattern).exists():
        files = [pattern]
    if not files:
        raise FileNotFoundError(f"Nenhum CSV encontrado para: {pattern}")
    print("[*] Arquivos de entrada:")
    for f in files:
        print(f"    - {f}")
    frames = [pd.read_csv(f) for f in files]
    df = pd.concat(frames, ignore_index=True)
    return df


def cmd_analyze(args) -> int:
    print("\n==========================================================")
    print(" 🔬 PROJETO JANUS V9: ANÁLISE RAW vs PÓS-SELEÇÃO")
    print("==========================================================")
    outdir = safe_mkdir(args.outdir)
    message = normalize_message(args.message)
    entries, manifest = build_sequence(message, args.header)

    df = load_input_csvs(args.input)
    print(f"[*] Linhas totais: {len(df):,}".replace(",", "."))
    required = {"dataset", "sequence_index", "bit_sent", "q1_futuro", *SPY_COLUMNS}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"CSV sem colunas necessárias: {missing}")

    for c in ["sequence_index", "bit_sent", "q1_futuro", "q0_passado", *SPY_COLUMNS]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    if "cycle" not in df.columns:
        df["cycle"] = 0
    if "sequence_kind" not in df.columns:
        df["sequence_kind"] = np.where(df["sequence_index"] < len(args.header), "HEADER", "PAYLOAD")

    datasets = sorted(df["dataset"].astype(str).unique().tolist())
    modes = ["RAW", "POST_Q1_1"]
    if args.include_q1_zero_diagnostic:
        modes.append("POST_Q1_0")
    print(f"[*] Datasets: {', '.join(datasets)}")
    print(f"[*] Modos   : {', '.join(modes)}")
    print(f"[*] Mensagem esperada: {message}")

    # Resumo shot-level.
    shot_rows = []
    for dataset in datasets:
        d0 = df[df["dataset"] == dataset]
        for mode in modes:
            d = apply_mode_filter(d0, mode)
            if len(d) == 0:
                continue
            for bit in [0, 1]:
                b = d[d["bit_sent"] == bit]
                if len(b) == 0:
                    continue
                cons = b[SPY_COLUMNS].astype(int).sum(axis=1)
                shot_rows.append({
                    "dataset": dataset,
                    "mode": mode,
                    "bit_sent": bit,
                    "n": len(b),
                    "consenso_mean": float(cons.mean()),
                    "espiao_1_mean": float(b["espiao_1"].mean()),
                    "espiao_2_mean": float(b["espiao_2"].mean()),
                    "espiao_3_mean": float(b["espiao_3"].mean()),
                    "q1_rate": float(b["q1_futuro"].mean()),
                    "q0_rate": float(b["q0_passado"].mean()) if "q0_passado" in b.columns else np.nan,
                })
    shot_summary = pd.DataFrame(shot_rows)
    shot_summary.to_csv(outdir / "shot_level_bit_summary.csv", index=False)

    # Decodificação agregada por blocos.
    decode_rows = []
    all_block_features = []
    distance_rows = []
    for dataset in datasets:
        dd = df[df["dataset"] == dataset]
        for mode in modes:
            blocks = aggregate_block_features(dd, mode, args.feature_mode)
            if blocks.empty:
                continue
            all_block_features.append(blocks)
            dec = decode_from_block_features(blocks, message, args.header, args.feature_mode)
            row = {
                "dataset": dataset,
                "mode": mode,
                "decoded_message": dec.get("decoded_message", ""),
                "expected_message": message,
                "payload_bit_accuracy": dec.get("payload_bit_accuracy", np.nan),
                "char_accuracy": dec.get("char_accuracy", np.nan),
                "hamming_corrected_count": dec.get("hamming_corrected_count", np.nan),
                "bits_received": dec.get("bits_received", ""),
                "hamming_blocks_raw": json.dumps(dec.get("hamming_blocks_raw", []), ensure_ascii=False),
                "hamming_syndromes": json.dumps(dec.get("hamming_syndromes", []), ensure_ascii=False),
                "status": dec.get("reason", ""),
            }
            decode_rows.append(row)
            for dr in dec.get("distance_rows", []) if dec.get("ok") else []:
                distance_rows.append({"dataset": dataset, "mode": mode, **dr})

    decode_results = pd.DataFrame(decode_rows)
    decode_results.to_csv(outdir / "decode_results.csv", index=False)
    if all_block_features:
        block_features = pd.concat(all_block_features, ignore_index=True)
    else:
        block_features = pd.DataFrame()
    block_features.to_csv(outdir / "block_features.csv", index=False)
    pd.DataFrame(distance_rows).to_csv(outdir / "decode_distances.csv", index=False)

    # Decodificação por ciclo separada, útil para ver estabilidade.
    cycle_decode_rows = []
    for dataset in datasets:
        dd = df[df["dataset"] == dataset]
        for mode in modes:
            cblocks = aggregate_cycle_block_features(dd, mode, args.feature_mode)
            if cblocks.empty:
                continue
            for cycle, one in cblocks.groupby("cycle"):
                dec = decode_from_block_features(one, message, args.header, args.feature_mode)
                cycle_decode_rows.append({
                    "dataset": dataset,
                    "mode": mode,
                    "cycle": int(cycle),
                    "decoded_message": dec.get("decoded_message", ""),
                    "payload_bit_accuracy": dec.get("payload_bit_accuracy", np.nan),
                    "char_accuracy": dec.get("char_accuracy", np.nan),
                    "hamming_corrected_count": dec.get("hamming_corrected_count", np.nan),
                    "status": dec.get("reason", ""),
                })
    cycle_decode_results = pd.DataFrame(cycle_decode_rows)
    cycle_decode_results.to_csv(outdir / "cycle_decode_results.csv", index=False)

    # Modelo binário por janelas, sem q0/q1 como feature.
    model_rows = []
    for dataset in datasets:
        dd = df[df["dataset"] == dataset]
        for mode in modes:
            print(f"[*] ML windows: dataset={dataset} | mode={mode}")
            windows = build_window_features(dd, mode, args.feature_mode, args.window, exclude_header=True)
            if args.max_windows and len(windows) > args.max_windows:
                windows = windows.sample(args.max_windows, random_state=args.random_seed).reset_index(drop=True)
            if windows.empty:
                model_rows.append({"dataset": dataset, "mode": mode, "model": "logreg", "ok": False, "reason": "sem janelas"})
                continue
            # Logistic com permutação agrupada.
            print(f"    -> LogisticRegression: {len(windows)} janelas")
            res_log = evaluate_binary_model(windows, args.feature_mode, args.n_perm, args.random_seed, model_kind="logreg")
            model_rows.append({"dataset": dataset, "mode": mode, **res_log})
            # RF sem permutação, para comparação rápida.
            if args.include_rf:
                print(f"    -> RandomForest: {len(windows)} janelas")
                res_rf = evaluate_binary_model(windows, args.feature_mode, 0, args.random_seed, model_kind="rf")
                model_rows.append({"dataset": dataset, "mode": mode, **res_rf})

    model_metrics = pd.DataFrame(model_rows)
    model_metrics.to_csv(outdir / "model_metrics.csv", index=False)

    # Teste SHAM: embaralha mapping sequência->bit no decode para estimar pareidolia de mensagem.
    sham_rows = []
    if args.sham_trials > 0 and not block_features.empty:
        rng = np.random.default_rng(args.random_seed)
        for dataset in datasets:
            for mode in modes:
                base = block_features[(block_features["dataset"] == dataset) & (block_features["mode"] == mode)].copy()
                if base.empty:
                    continue
                payload_mask = base["sequence_kind"] == "PAYLOAD"
                true_bits = base.loc[payload_mask, "bit_sent"].to_numpy().copy()
                hits = 0
                best_char_acc = 0.0
                best_msg = ""
                for t in range(args.sham_trials):
                    shuffled = true_bits.copy()
                    rng.shuffle(shuffled)
                    fake = base.copy()
                    fake.loc[payload_mask, "bit_sent"] = shuffled
                    # O decode não usa bit_sent para demodular, mas usa expected para métrica; aqui calculamos coincidência com JANUS.
                    dec = decode_from_block_features(fake, message, args.header, args.feature_mode)
                    msg = dec.get("decoded_message", "")
                    ca = float(dec.get("char_accuracy", 0.0) or 0.0)
                    if msg == message:
                        hits += 1
                    if ca > best_char_acc:
                        best_char_acc = ca
                        best_msg = msg
                sham_rows.append({
                    "dataset": dataset,
                    "mode": mode,
                    "sham_trials": args.sham_trials,
                    "exact_message_hits": hits,
                    "exact_message_rate": hits / args.sham_trials,
                    "best_char_accuracy": best_char_acc,
                    "best_decoded_message": best_msg,
                })
    sham_results = pd.DataFrame(sham_rows)
    sham_results.to_csv(outdir / "sham_message_results.csv", index=False)

    report_lines = []
    report_lines.append("# JANUS V9 — Relatório RAW vs Pós-Seleção")
    report_lines.append("")
    report_lines.append(f"Mensagem esperada: **{message}**")
    report_lines.append(f"Linhas analisadas: **{len(df)}**")
    report_lines.append(f"Feature mode: `{args.feature_mode}`")
    report_lines.append(f"Window ML: `{args.window}`")
    report_lines.append(f"Permutation tests: `{args.n_perm}`")
    report_lines.append("")
    report_lines.append("## Sequência codificada")
    report_lines.append("```json")
    report_lines.append(json.dumps(manifest, ensure_ascii=False, indent=2))
    report_lines.append("```")
    report_lines.append("")
    report_lines.append("## Resumo shot-level por bit")
    report_lines.append(markdown_table(shot_summary, index=False) if not shot_summary.empty else "Sem dados.")
    report_lines.append("")
    report_lines.append("## Decodificação de mensagem — agregada")
    report_lines.append(markdown_table(decode_results[["dataset", "mode", "decoded_message", "expected_message", "payload_bit_accuracy", "char_accuracy", "hamming_corrected_count", "status"]], index=False) if not decode_results.empty else "Sem dados.")
    report_lines.append("")
    report_lines.append("## Decodificação por ciclo")
    report_lines.append(markdown_table(cycle_decode_results, index=False) if not cycle_decode_results.empty else "Sem dados.")
    report_lines.append("")
    report_lines.append("## Métricas ML por janelas — somente espiões")
    cols = [c for c in ["dataset", "mode", "model", "n_windows", "n_sequences", "accuracy", "balanced_accuracy", "auc", "perm_p_grouped", "cm_tn", "cm_fp", "cm_fn", "cm_tp", "reason"] if c in model_metrics.columns]
    report_lines.append(markdown_table(model_metrics[cols], index=False) if not model_metrics.empty else "Sem dados.")
    report_lines.append("")
    if not sham_results.empty:
        report_lines.append("## Controle SHAM / pareidolia de mensagem")
        report_lines.append(markdown_table(sham_results, index=False))
        report_lines.append("")
    report_lines.append("## Interpretação operacional")
    report_lines.append("- `POST_Q1_1`: decodificação com pós-seleção futura, compatível com o protocolo V8.")
    report_lines.append("- `RAW`: tentativa de recuperação macroscópica sem pós-seleção; este é o teste relevante para vazamento operacional/no-signal.")
    report_lines.append("- `NULO`: remove o emaranhamento `CX(0,1)`; deve falhar se o canal depender da ponte EPR.")
    report_lines.append("- `PHAN_STRICT_POSTHOC`: mantém circuito emaranhado sem marreta; deve falhar se a mensagem depender da intervenção ativa e não de pareidolia/drift.")
    report_lines.append("")
    report_lines.append("## Arquivos gerados")
    for name in ["shot_level_bit_summary.csv", "decode_results.csv", "cycle_decode_results.csv", "block_features.csv", "decode_distances.csv", "model_metrics.csv", "sham_message_results.csv"]:
        report_lines.append(f"- `{outdir / name}`")
    report = "\n".join(report_lines)
    report_path = outdir / "JANUS_V9_RAW_POST_REPORT.md"
    report_path.write_text(report, encoding="utf-8")

    print("\n" + report)
    print("\n==========================================================")
    print(" Análise concluída")
    print("==========================================================")
    print(f"Relatório: {report_path}")
    print(f"Decode   : {outdir / 'decode_results.csv'}")
    print(f"ML       : {outdir / 'model_metrics.csv'}")
    return 0


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Janus V9 — JANUS RAW/POST message extraction and analysis")
    sub = p.add_subparsers(dest="cmd", required=True)

    pe = sub.add_parser("extract", help="Extrair dados no IBM Quantum")
    pe.add_argument("--backend", default="ibm_fez")
    pe.add_argument("--channel", default="ibm_quantum_platform")
    pe.add_argument("--ibm-token", default=None)
    pe.add_argument("--message", default="JANUS")
    pe.add_argument("--header", default=DEFAULT_HEADER)
    pe.add_argument("--shots", type=int, default=8192)
    pe.add_argument("--cycles", type=int, default=1)
    pe.add_argument("--theta", default="np.pi/8")
    pe.add_argument("--total-qubits", type=int, default=5)
    pe.add_argument("--outdir", default="janus_v9_run")
    pe.add_argument("--run-tag", default=None)
    pe.add_argument("--include-nulo", action="store_true", help="Inclui controle NULO sem CX(0,1)")
    pe.add_argument("--include-phan-strict", action="store_true", help="Inclui PHAN_STRICT_POSTHOC: emaranhado, sem marreta")
    pe.add_argument("--randomize-order", action="store_true", help="Randomiza ordem dos circuitos/pubs")
    pe.add_argument("--random-seed", type=int, default=42)
    pe.add_argument("--optimization-level", type=int, default=3)
    pe.add_argument("--seed-transpiler", type=int, default=1234)
    pe.add_argument("--initial-layout", default=None, help="Opcional: ex. 0,1,2,3,4")
    pe.set_defaults(func=cmd_extract)

    pa = sub.add_parser("analyze", help="Analisar CSV já extraído")
    pa.add_argument("--input", required=True, help="CSV ou glob. Ex: janus_v9_run/JANUS_V9_RAW_*.csv")
    pa.add_argument("--message", default="JANUS")
    pa.add_argument("--header", default=DEFAULT_HEADER)
    pa.add_argument("--outdir", default="janus_v9_analysis")
    pa.add_argument("--feature-mode", choices=["basic", "full"], default="full")
    pa.add_argument("--window", type=int, default=16)
    pa.add_argument("--n-perm", type=int, default=100)
    pa.add_argument("--random-seed", type=int, default=42)
    pa.add_argument("--include-rf", action="store_true", help="Inclui RandomForest sem permutação")
    pa.add_argument("--include-q1-zero-diagnostic", action="store_true")
    pa.add_argument("--max-windows", type=int, default=0, help="0 = sem limite; útil para testes rápidos")
    pa.add_argument("--sham-trials", type=int, default=200)
    pa.set_defaults(func=cmd_analyze)

    pall = sub.add_parser("all", help="Alias não implementado: rode extract e analyze separadamente")
    pall.set_defaults(func=lambda args: (print("Use extract e depois analyze."), 1)[1])
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_argparser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
