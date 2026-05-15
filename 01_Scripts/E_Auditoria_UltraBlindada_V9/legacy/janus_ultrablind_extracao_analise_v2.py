#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Projeto Janus — Extração + Análise Ultra-Blindada
=================================================

Objetivo
--------
Este script substitui a auditoria panóptica original por uma versão mais rígida,
com rastreabilidade de circuito, layout, job_id, ordem de execução e um controle
PHAN_STRICT em que os rótulos Placebo/Ativo são atribuídos APÓS a coleta de um
único circuito físico. Se PHAN_STRICT der acima de ~50%, há vazamento de análise.
Se PHAN_LEGACY der alto e PHAN_STRICT cair, o problema provável é diferença de
transpiler/layout/ordem/drift, não retrocausalidade.

Subcomandos
-----------
1) Extração em hardware IBM:
   python janus_ultrablind_extracao_analise.py extract --backend ibm_fez --lots 5 --shots 4096 --outdir janus_run

2) Análise dos CSVs gerados:
   python janus_ultrablind_extracao_analise.py analyze --input janus_run/JANUS_RAW_ibm_fez_*.csv --window 16 --n-perm 1000

Dependências
------------
pip install qiskit qiskit-ibm-runtime pandas numpy scipy scikit-learn python-dotenv

Variável de ambiente
--------------------
IBM_QUANTUM_TOKEN="seu_token"

Notas importantes
-----------------
- Use --initial-layout 0,1,2,3,4 quando quiser fixar qubits físicos.
- Use --seed-transpiler para reprodutibilidade.
- O script preserva medições intermediárias dos espiões, como no protocolo original.
- A análise usa validação por lote/grupo e permutation test por grupo.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import glob
import hashlib
import json
import os
import random
import sys
import warnings
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


# =============================================================================
# Utilidades gerais
# =============================================================================


def now_tag() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


def safe_json_dumps(obj) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, sort_keys=True)
    except Exception:
        return str(obj)


def parse_initial_layout(value: Optional[str]) -> Optional[List[int]]:
    if not value:
        return None
    return [int(x.strip()) for x in value.split(",") if x.strip()]


RAW_COLUMNS = [
    "run_tag", "backend", "job_id", "lote", "shot_idx",
    "dataset", "label", "label_code", "role", "logical_name",
    "q1_futuro", "q0_passado", "espiao_1", "espiao_2", "espiao_3",
    "bitstring_raw", "bitstring_reversed",
    "circuit_hash", "layout_summary", "creg_name", "order_idx",
    "theta", "shots_requested", "posthoc_label",
]


# =============================================================================
# Parte 1 — EXTRAÇÃO IBM
# =============================================================================


@dataclass
class PubMeta:
    dataset: str
    label: str
    label_code: int
    role: str
    logical_name: str
    circuit_hash: str
    layout_summary: str
    creg_name: str
    order_idx: int


def import_qiskit_stack():
    try:
        import numpy as _np
        from dotenv import load_dotenv
        from qiskit import QuantumCircuit, transpile
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
        return _np, load_dotenv, QuantumCircuit, transpile, QiskitRuntimeService, Sampler
    except Exception as exc:
        print("[X] Dependências de extração não encontradas.")
        print("    Instale com:")
        print("    pip install qiskit qiskit-ibm-runtime pandas numpy scipy scikit-learn python-dotenv")
        raise exc


def circuit_to_stable_text(circuit) -> str:
    """Tenta serializar o circuito de forma estável para hash/auditoria."""
    try:
        from qiskit import qasm3
        return qasm3.dumps(circuit)
    except Exception:
        pass
    try:
        from qiskit import qasm2
        return qasm2.dumps(circuit)
    except Exception:
        pass
    try:
        return circuit.draw(output="text").single_string()
    except Exception:
        return repr(circuit.data)


def get_layout_summary(circuit) -> str:
    try:
        layout = getattr(circuit, "layout", None)
        if layout is None:
            return "NO_LAYOUT"
        return str(layout)
    except Exception as exc:
        return f"LAYOUT_UNREADABLE:{exc}"


def get_creg_name(circuit) -> str:
    try:
        if circuit.cregs:
            return circuit.cregs[0].name
    except Exception:
        pass
    return "c"


def build_logical_circuits(theta: float, total_qubits: int = 5):
    """
    Constrói os circuitos lógicos.

    Qubits/clbits:
      c0/q0 = Q0 passado
      c1/q1 = Q1 futuro
      c2/q2 = espião 1
      c3/q3 = espião 2
      c4/q4 = espião 3
    """
    _np, _load_dotenv, QuantumCircuit, _transpile, _Service, _Sampler = import_qiskit_stack()

    def aplicar_espioes(qc):
        qc.barrier(label="T0_START_WEAK_MEAS")
        qc.cry(theta, 0, 2)
        qc.measure(2, 2)
        qc.cry(theta, 0, 3)
        qc.measure(3, 3)
        qc.cry(theta, 0, 4)
        qc.measure(4, 4)
        qc.barrier(label="T0_END_WEAK_MEAS")

    def finish(qc, active: bool):
        if active:
            qc.rx(_np.pi / 2, 1)
        qc.barrier(label="T1_FINAL_READOUT")
        qc.measure(1, 1)
        qc.measure(0, 0)
        return qc

    circuits = {}

    # REAL: corda + marreta opcional
    qc = QuantumCircuit(total_qubits, total_qubits, name="REAL_PLACEBO_CORDA_SEM_MARRETA")
    qc.h(0)
    qc.cx(0, 1)
    aplicar_espioes(qc)
    circuits["REAL_PLACEBO"] = finish(qc, active=False)

    qc = QuantumCircuit(total_qubits, total_qubits, name="REAL_ATIVO_CORDA_COM_MARRETA")
    qc.h(0)
    qc.cx(0, 1)
    aplicar_espioes(qc)
    circuits["REAL_ATIVO"] = finish(qc, active=True)

    # NULO: sem corda, mas com marreta opcional
    qc = QuantumCircuit(total_qubits, total_qubits, name="NULO_PLACEBO_SEM_CORDA_SEM_MARRETA")
    qc.h(0)
    qc.h(1)
    aplicar_espioes(qc)
    circuits["NULO_PLACEBO"] = finish(qc, active=False)

    qc = QuantumCircuit(total_qubits, total_qubits, name="NULO_ATIVO_SEM_CORDA_COM_MARRETA")
    qc.h(0)
    qc.h(1)
    aplicar_espioes(qc)
    circuits["NULO_ATIVO"] = finish(qc, active=True)

    # PHAN canônico: corda, sem marreta. Usado para PHAN_STRICT e PHAN_LEGACY.
    qc = QuantumCircuit(total_qubits, total_qubits, name="PHAN_CANONICO_CORDA_SEM_MARRETA")
    qc.h(0)
    qc.cx(0, 1)
    aplicar_espioes(qc)
    circuits["PHAN_CANONICO"] = finish(qc, active=False)

    return circuits


def transpile_circuits(circuits: Dict[str, object], backend, optimization_level: int, seed_transpiler: Optional[int], initial_layout: Optional[List[int]]):
    _np, _load_dotenv, _QuantumCircuit, transpile, _Service, _Sampler = import_qiskit_stack()

    kwargs = {
        "backend": backend,
        "optimization_level": optimization_level,
    }
    if seed_transpiler is not None:
        kwargs["seed_transpiler"] = seed_transpiler
    if initial_layout is not None:
        kwargs["initial_layout"] = initial_layout

    names = list(circuits.keys())
    print("[*] Transpilando circuitos...")
    transpiled_list = transpile([circuits[n] for n in names], **kwargs)
    return {n: c for n, c in zip(names, transpiled_list)}


def read_bitstrings_from_pub(pub_result, creg_name: str = "c") -> List[str]:
    """Compatível com SamplerV2/DataBin na maioria das versões."""
    data = pub_result.data
    # Caminho esperado: result.data.c.get_bitstrings()
    try:
        reg = getattr(data, creg_name)
        return list(reg.get_bitstrings())
    except Exception:
        pass

    # Fallback: tente qualquer campo com get_bitstrings()
    for attr in dir(data):
        if attr.startswith("_"):
            continue
        try:
            reg = getattr(data, attr)
            if hasattr(reg, "get_bitstrings"):
                return list(reg.get_bitstrings())
        except Exception:
            continue

    raise RuntimeError("Não consegui extrair bitstrings do resultado SamplerV2.")


def bitstring_to_row(bitstring: str) -> Dict[str, int | str]:
    # Padrão original do projeto: inverter string IBM e mapear c0..c4.
    s = bitstring[::-1]
    if len(s) < 5:
        raise ValueError(f"Bitstring curta demais: {bitstring}")
    return {
        "q1_futuro": int(s[1]),
        "q0_passado": int(s[0]),
        "espiao_1": int(s[2]),
        "espiao_2": int(s[3]),
        "espiao_3": int(s[4]),
        "bitstring_raw": bitstring,
        "bitstring_reversed": s,
    }


def rows_from_pub(
    bitstrings: Sequence[str],
    meta: PubMeta,
    lote: int,
    job_id: str,
    backend_name: str,
    theta: float,
    shots_requested: int,
    run_tag: str,
    strict_posthoc_split: bool = False,
    rng: Optional[random.Random] = None,
) -> List[Dict]:
    rows = []

    if not strict_posthoc_split:
        for shot_idx, bs in enumerate(bitstrings):
            base = bitstring_to_row(bs)
            base.update({
                "run_tag": run_tag,
                "backend": backend_name,
                "job_id": job_id,
                "lote": lote,
                "shot_idx": shot_idx,
                "dataset": meta.dataset,
                "label": meta.label,
                "label_code": meta.label_code,
                "role": meta.role,
                "logical_name": meta.logical_name,
                "circuit_hash": meta.circuit_hash,
                "layout_summary": meta.layout_summary,
                "creg_name": meta.creg_name,
                "order_idx": meta.order_idx,
                "theta": theta,
                "shots_requested": shots_requested,
                "posthoc_label": False,
            })
            rows.append(base)
        return rows

    # PHAN_STRICT: um único circuito físico; rótulo atribuído depois da coleta.
    # Divide meio a meio com shuffle determinístico por lote.
    if rng is None:
        rng = random.Random(42)
    indices = list(range(len(bitstrings)))
    rng.shuffle(indices)
    half = len(indices) // 2
    label_by_idx = {}
    for idx in indices[:half]:
        label_by_idx[idx] = ("Placebo", 0)
    for idx in indices[half:]:
        label_by_idx[idx] = ("Ativo", 1)

    for shot_idx, bs in enumerate(bitstrings):
        label, label_code = label_by_idx[shot_idx]
        base = bitstring_to_row(bs)
        base.update({
            "run_tag": run_tag,
            "backend": backend_name,
            "job_id": job_id,
            "lote": lote,
            "shot_idx": shot_idx,
            "dataset": "PHAN_STRICT_POSTHOC",
            "label": label,
            "label_code": label_code,
            "role": "PHAN_STRICT_SINGLE_CIRCUIT_POSTHOC_LABEL",
            "logical_name": meta.logical_name,
            "circuit_hash": meta.circuit_hash,
            "layout_summary": meta.layout_summary,
            "creg_name": meta.creg_name,
            "order_idx": meta.order_idx,
            "theta": theta,
            "shots_requested": shots_requested,
            "posthoc_label": True,
        })
        rows.append(base)

    return rows


def cmd_extract(args) -> int:
    _np, load_dotenv, _QuantumCircuit, _transpile, QiskitRuntimeService, Sampler = import_qiskit_stack()
    load_dotenv()

    token = os.getenv(args.token_env)
    if not token:
        print(f"[X] Token não encontrado na variável {args.token_env}.")
        return 2

    outdir = ensure_dir(args.outdir)
    run_tag = args.run_tag or f"JANUS_{args.backend}_{now_tag()}"
    raw_path = outdir / f"JANUS_RAW_{args.backend}_{run_tag}.csv"
    manifest_path = outdir / f"JANUS_MANIFEST_{args.backend}_{run_tag}.json"

    print("\n==========================================================")
    print(" 👁️ PROJETO JANUS: EXTRAÇÃO ULTRA-BLINDADA")
    print("==========================================================")
    print(f"[*] Backend        : {args.backend}")
    print(f"[*] Lotes          : {args.lots}")
    print(f"[*] Shots/pub      : {args.shots}")
    print(f"[*] Theta espião   : {args.theta}")
    print(f"[*] Out CSV        : {raw_path}")

    service = QiskitRuntimeService(channel=args.channel, token=token)
    backend = service.backend(args.backend)
    print(f"[*] Conectado      : {backend.name}")

    initial_layout = parse_initial_layout(args.initial_layout)
    circuits_logical = build_logical_circuits(theta=args.theta, total_qubits=5)
    circuits_isa = transpile_circuits(
        circuits_logical,
        backend=backend,
        optimization_level=args.optimization_level,
        seed_transpiler=args.seed_transpiler,
        initial_layout=initial_layout,
    )

    # Metadados fixos por circuito.
    base_meta: Dict[str, PubMeta] = {}
    mapping = {
        "REAL_PLACEBO": ("REAL", "Placebo", 0, "REAL_CORDA_SEM_MARRETA"),
        "REAL_ATIVO": ("REAL", "Ativo", 1, "REAL_CORDA_COM_MARRETA"),
        "NULO_PLACEBO": ("NULO", "Placebo", 0, "NULO_SEM_CORDA_SEM_MARRETA"),
        "NULO_ATIVO": ("NULO", "Ativo", 1, "NULO_SEM_CORDA_COM_MARRETA"),
        "PHAN_CANONICO": ("PHAN_STRICT_POSTHOC", "POSTHOC", -1, "PHAN_CANONICO_SEM_MARRETA"),
    }
    for name, circ in circuits_isa.items():
        text = circuit_to_stable_text(circ)
        ds, label, code, role = mapping[name]
        base_meta[name] = PubMeta(
            dataset=ds,
            label=label,
            label_code=code,
            role=role,
            logical_name=name,
            circuit_hash=sha256_text(text),
            layout_summary=get_layout_summary(circ),
            creg_name=get_creg_name(circ),
            order_idx=-1,
        )

    manifest = {
        "run_tag": run_tag,
        "backend": args.backend,
        "created_at": _dt.datetime.now().isoformat(),
        "lots": args.lots,
        "shots": args.shots,
        "theta": args.theta,
        "optimization_level": args.optimization_level,
        "seed_transpiler": args.seed_transpiler,
        "initial_layout": initial_layout,
        "include_legacy_phan": args.include_legacy_phan,
        "circuits": {k: asdict(v) for k, v in base_meta.items()},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    sampler = Sampler(backend)

    # Inicializa CSV vazio.
    columns = RAW_COLUMNS
    pd.DataFrame(columns=columns).to_csv(raw_path, index=False)

    rng = random.Random(args.random_seed)

    for lote in range(args.lots):
        print(f"\n[*] Lote {lote + 1}/{args.lots}")

        # Lista principal: REAL e NULO + um PHAN_STRICT canônico.
        pub_names = ["REAL_PLACEBO", "REAL_ATIVO", "NULO_PLACEBO", "NULO_ATIVO", "PHAN_CANONICO"]

        # Opcional: PHAN_LEGACY com dois pubs idênticos, mas rotulados antes.
        # Serve para detectar drift/layout/order quando circuitos iguais são executados em slots diferentes.
        if args.include_legacy_phan:
            pub_names.extend(["PHAN_LEGACY_PLACEBO", "PHAN_LEGACY_ATIVO"])
            circuits_isa["PHAN_LEGACY_PLACEBO"] = circuits_isa["PHAN_CANONICO"].copy(name="PHAN_LEGACY_PLACEBO")
            circuits_isa["PHAN_LEGACY_ATIVO"] = circuits_isa["PHAN_CANONICO"].copy(name="PHAN_LEGACY_ATIVO")
            for legacy_name, label, code in [
                ("PHAN_LEGACY_PLACEBO", "Placebo", 0),
                ("PHAN_LEGACY_ATIVO", "Ativo", 1),
            ]:
                circ = circuits_isa[legacy_name]
                text = circuit_to_stable_text(circ)
                base_meta[legacy_name] = PubMeta(
                    dataset="PHAN_LEGACY_IDENTICAL_PUBS",
                    label=label,
                    label_code=code,
                    role="PHAN_LEGACY_IDENTICAL_CIRCUIT_PRELABEL",
                    logical_name=legacy_name,
                    circuit_hash=sha256_text(text),
                    layout_summary=get_layout_summary(circ),
                    creg_name=get_creg_name(circ),
                    order_idx=-1,
                )

        rng.shuffle(pub_names)
        pubs = []
        metas = []
        for order_idx, name in enumerate(pub_names):
            meta = base_meta[name]
            meta = PubMeta(**{**asdict(meta), "order_idx": order_idx})
            pubs.append(circuits_isa[name])
            metas.append(meta)
            print(f"    ordem={order_idx} dataset={meta.dataset:28s} label={meta.label:8s} hash={meta.circuit_hash}")

        try:
            job = sampler.run(pubs, shots=args.shots)
            print(f"    job_id={job.job_id()}")
            result = job.result()
        except Exception as exc:
            print(f"[X] Falha no lote {lote}: {exc}")
            if args.stop_on_error:
                raise
            continue

        lote_rows: List[Dict] = []
        for pub_idx, meta in enumerate(metas):
            bitstrings = read_bitstrings_from_pub(result[pub_idx], creg_name=meta.creg_name)
            strict = meta.logical_name == "PHAN_CANONICO"
            lote_rows.extend(rows_from_pub(
                bitstrings=bitstrings,
                meta=meta,
                lote=lote,
                job_id=job.job_id(),
                backend_name=args.backend,
                theta=args.theta,
                shots_requested=args.shots,
                run_tag=run_tag,
                strict_posthoc_split=strict,
                rng=random.Random(args.random_seed + lote),
            ))

        # CRÍTICO: força a mesma ordem do cabeçalho.
        # Sem columns=columns, pandas escreve na ordem de inserção dos dicts,
        # deslocando campos como dataset/label para espiao_1/espiao_2.
        pd.DataFrame(lote_rows, columns=columns).to_csv(raw_path, mode="a", header=False, index=False)
        print(f"    [+] {len(lote_rows)} linhas gravadas.")

    print("\n==========================================================")
    print(" Extração concluída")
    print("==========================================================")
    print(f"CSV bruto : {raw_path}")
    print(f"Manifesto : {manifest_path}")
    print("\nAgora rode:")
    print(f"python {Path(__file__).name} analyze --input {raw_path} --window 16 --n-perm 1000")
    return 0


# =============================================================================
# Parte 2 — ANÁLISE
# =============================================================================


def import_analysis_stack():
    try:
        from sklearn.base import clone
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score, confusion_matrix
        from sklearn.model_selection import GroupKFold, LeaveOneGroupOut
        from scipy.stats import binomtest, ttest_1samp
        return {
            "clone": clone,
            "RandomForestClassifier": RandomForestClassifier,
            "LogisticRegression": LogisticRegression,
            "accuracy_score": accuracy_score,
            "balanced_accuracy_score": balanced_accuracy_score,
            "roc_auc_score": roc_auc_score,
            "confusion_matrix": confusion_matrix,
            "GroupKFold": GroupKFold,
            "LeaveOneGroupOut": LeaveOneGroupOut,
            "binomtest": binomtest,
            "ttest_1samp": ttest_1samp,
        }
    except Exception as exc:
        print("[X] Dependências de análise não encontradas.")
        print("    Instale com:")
        print("    pip install pandas numpy scipy scikit-learn")
        raise exc


def expand_input_files(patterns: Sequence[str]) -> List[str]:
    files: List[str] = []
    for p in patterns:
        matches = glob.glob(p)
        if matches:
            files.extend(matches)
        elif Path(p).exists():
            files.append(p)
    files = sorted(set(files))
    if not files:
        raise FileNotFoundError(f"Nenhum arquivo encontrado para: {patterns}")
    return files


def looks_like_legacy_misaligned_raw(df: pd.DataFrame) -> bool:
    """
    Detecta CSV gerado pela primeira versão deste script, onde o cabeçalho
    estava correto mas as linhas foram anexadas na ordem dos dicts. Sintoma:
    espiao_1 contém REAL/NULO/PHAN em vez de 0/1.
    """
    if "espiao_1" not in df.columns:
        return False
    espiao_as_number = pd.to_numeric(df["espiao_1"], errors="coerce")
    non_numeric_ratio = float(espiao_as_number.isna().mean()) if len(df) else 0.0
    has_dataset_words = df["espiao_1"].astype(str).str.contains("REAL|NULO|PHAN", regex=True, na=False).any()
    return non_numeric_ratio > 0.20 and bool(has_dataset_words)


def repair_legacy_misaligned_raw(df: pd.DataFrame) -> pd.DataFrame:
    """
    Repara dados já extraídos pela versão bugada, sem exigir nova execução IBM.

    Ordem escrita pela versão bugada:
      q1_futuro, q0_passado, espiao_1, espiao_2, espiao_3, bitstring_raw,
      bitstring_reversed, run_tag, backend, job_id, lote, shot_idx, dataset,
      label, label_code, role, logical_name, circuit_hash, layout_summary,
      creg_name, order_idx, theta, shots_requested, posthoc_label

    Cabeçalho esperado:
      RAW_COLUMNS
    """
    old = df.copy()
    source_file = old["source_file"] if "source_file" in old.columns else None

    mapping = {
        "q1_futuro": "run_tag",
        "q0_passado": "backend",
        "espiao_1": "job_id",
        "espiao_2": "lote",
        "espiao_3": "shot_idx",
        "bitstring_raw": "dataset",
        "bitstring_reversed": "label",
        "run_tag": "label_code",
        "backend": "role",
        "job_id": "logical_name",
        "lote": "q1_futuro",
        "shot_idx": "q0_passado",
        "dataset": "espiao_1",
        "label": "espiao_2",
        "label_code": "espiao_3",
        "role": "bitstring_raw",
        "logical_name": "bitstring_reversed",
        "circuit_hash": "circuit_hash",
        "layout_summary": "layout_summary",
        "creg_name": "creg_name",
        "order_idx": "order_idx",
        "theta": "theta",
        "shots_requested": "shots_requested",
        "posthoc_label": "posthoc_label",
    }

    fixed = pd.DataFrame(index=old.index)
    for correct_col in RAW_COLUMNS:
        old_col = mapping.get(correct_col, correct_col)
        fixed[correct_col] = old[old_col] if old_col in old.columns else pd.NA
    if source_file is not None:
        fixed["source_file"] = source_file
    return fixed


def load_raw_csvs(files: Sequence[str]) -> pd.DataFrame:
    dfs = []
    for f in files:
        df = pd.read_csv(f)
        df["source_file"] = str(f)
        dfs.append(df)
    out = pd.concat(dfs, ignore_index=True)

    if looks_like_legacy_misaligned_raw(out):
        print("[!] CSV detectado com desalinhamento da primeira versão. Reparando em memória...")
        out = repair_legacy_misaligned_raw(out)

    required = {"dataset", "label", "label_code", "lote", "q1_futuro", "espiao_1", "espiao_2", "espiao_3"}
    missing = required - set(out.columns)
    if missing:
        raise ValueError(f"CSV não parece ser JANUS_RAW. Colunas ausentes: {missing}")
    out["row_global"] = np.arange(len(out))
    return out


def add_basic_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    bit_cols = ["q1_futuro", "q0_passado", "espiao_1", "espiao_2", "espiao_3", "label_code", "lote", "shot_idx", "order_idx"]
    for col in bit_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="raise").astype(int)

    df["consenso"] = df["espiao_1"] + df["espiao_2"] + df["espiao_3"]
    df["label_norm"] = df["label"].astype(str)
    df["y"] = df["label_code"].astype(int)

    bad_labels = sorted(set(df["label_norm"].dropna()) - {"Placebo", "Ativo", "POSTHOC"})
    if bad_labels:
        print(f"[!] Labels inesperados encontrados: {bad_labels[:10]}")
    return df


def make_window_features(
    df: pd.DataFrame,
    dataset: str,
    postselect: bool,
    window: int,
    feature_mode: str,
) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray, List[str]]:
    d = df[df["dataset"] == dataset].copy()
    if postselect:
        d = d[d["q1_futuro"] == 1].copy()

    d = d[d["label"].isin(["Placebo", "Ativo"])].copy()
    if d.empty or d["y"].nunique() < 2:
        return pd.DataFrame(), np.empty((0, 0)), np.array([]), np.array([]), []

    feature_rows = []
    for (lote, label), g in d.groupby(["lote", "label"], sort=True):
        g = g.sort_values("row_global")
        y_val = int(g["y"].iloc[0])
        vals = g["consenso"].to_numpy(dtype=float)
        e1 = g["espiao_1"].to_numpy(dtype=float)
        e2 = g["espiao_2"].to_numpy(dtype=float)
        e3 = g["espiao_3"].to_numpy(dtype=float)
        q0 = g["q0_passado"].to_numpy(dtype=float) if "q0_passado" in g.columns else np.zeros(len(g))

        n = len(g)
        for start in range(0, n - window + 1, window):
            sl = slice(start, start + window)
            cons = vals[sl]
            row = {
                "dataset": dataset,
                "postselect": postselect,
                "lote": lote,
                "label": label,
                "y": y_val,
                "start": start,
                "n_window": window,
                "cons_mean": float(np.mean(cons)),
                "cons_var": float(np.var(cons)),
                "cons_flicker": float(np.sum(np.abs(np.diff(cons))) / max(1, len(cons) - 1)),
            }
            if feature_mode == "expanded":
                for name, arr in [("e1", e1), ("e2", e2), ("e3", e3), ("q0", q0)]:
                    x = arr[sl]
                    row[f"{name}_mean"] = float(np.mean(x))
                    row[f"{name}_var"] = float(np.var(x))
                    row[f"{name}_flicker"] = float(np.sum(np.abs(np.diff(x))) / max(1, len(x) - 1))
            feature_rows.append(row)

    feat_df = pd.DataFrame(feature_rows)
    if feat_df.empty:
        return feat_df, np.empty((0, 0)), np.array([]), np.array([]), []

    ignore = {"dataset", "postselect", "lote", "label", "y", "start", "n_window"}
    feature_cols = [c for c in feat_df.columns if c not in ignore]
    X = feat_df[feature_cols].to_numpy(dtype=float)
    y = feat_df["y"].to_numpy(dtype=int)
    groups = feat_df["lote"].to_numpy()
    return feat_df, X, y, groups, feature_cols


def group_cv_predict(model, X: np.ndarray, y: np.ndarray, groups: np.ndarray, random_state: int = 42):
    st = import_analysis_stack()
    clone = st["clone"]
    accuracy_score = st["accuracy_score"]
    balanced_accuracy_score = st["balanced_accuracy_score"]
    roc_auc_score = st["roc_auc_score"]
    confusion_matrix = st["confusion_matrix"]
    GroupKFold = st["GroupKFold"]
    LeaveOneGroupOut = st["LeaveOneGroupOut"]

    unique_groups = np.unique(groups)
    if len(unique_groups) < 2:
        raise ValueError("É preciso pelo menos 2 lotes/grupos para validação por grupo.")

    if len(unique_groups) <= 5:
        splitter = LeaveOneGroupOut()
    else:
        splitter = GroupKFold(n_splits=min(5, len(unique_groups)))

    y_pred = np.zeros_like(y)
    y_score = np.full(len(y), np.nan, dtype=float)

    for train_idx, test_idx in splitter.split(X, y, groups):
        m = clone(model)
        m.fit(X[train_idx], y[train_idx])
        y_pred[test_idx] = m.predict(X[test_idx])
        if hasattr(m, "predict_proba"):
            y_score[test_idx] = m.predict_proba(X[test_idx])[:, 1]
        elif hasattr(m, "decision_function"):
            s = m.decision_function(X[test_idx])
            y_score[test_idx] = s

    acc = float(accuracy_score(y, y_pred))
    bacc = float(balanced_accuracy_score(y, y_pred))
    try:
        auc = float(roc_auc_score(y, y_score)) if not np.isnan(y_score).all() else np.nan
    except Exception:
        auc = np.nan
    cm = confusion_matrix(y, y_pred, labels=[0, 1])
    return {
        "accuracy": acc,
        "balanced_accuracy": bacc,
        "auc": auc,
        "confusion_matrix": cm,
        "y_pred": y_pred,
        "y_score": y_score,
    }


def grouped_permutation_test(model, X, y, groups, observed_acc: float, n_perm: int, seed: int = 42) -> float:
    if n_perm <= 0:
        return np.nan
    rng = np.random.default_rng(seed)
    count = 0
    valid = 0
    for _ in range(n_perm):
        yp = y.copy()
        for g in np.unique(groups):
            idx = np.where(groups == g)[0]
            yp[idx] = rng.permutation(yp[idx])
        # Se algum fold ficar com classe única no treino, ignore permutação.
        try:
            res = group_cv_predict(model, X, yp, groups)
            perm_acc = res["accuracy"]
            valid += 1
            if perm_acc >= observed_acc:
                count += 1
        except Exception:
            continue
    if valid == 0:
        return np.nan
    return float((count + 1) / (valid + 1))


def shot_level_summary(df: pd.DataFrame, outdir: Path) -> pd.DataFrame:
    records = []
    for dataset, d in df.groupby("dataset"):
        for postselect in [False, True]:
            x = d[d["q1_futuro"] == 1] if postselect else d
            x = x[x["label"].isin(["Placebo", "Ativo"])]
            if x.empty:
                continue
            means = x.groupby("label")[["consenso", "espiao_1", "espiao_2", "espiao_3", "q0_passado", "q1_futuro"]].mean()
            counts = x.groupby("label").size().rename("n")
            joined = means.join(counts)
            if {"Placebo", "Ativo"}.issubset(set(joined.index)):
                rec = {
                    "dataset": dataset,
                    "postselect": postselect,
                    "n_placebo": int(joined.loc["Placebo", "n"]),
                    "n_ativo": int(joined.loc["Ativo", "n"]),
                }
                for col in ["consenso", "espiao_1", "espiao_2", "espiao_3", "q0_passado", "q1_futuro"]:
                    rec[f"{col}_placebo_mean"] = float(joined.loc["Placebo", col])
                    rec[f"{col}_ativo_mean"] = float(joined.loc["Ativo", col])
                    rec[f"{col}_delta_ativo_minus_placebo"] = float(joined.loc["Ativo", col] - joined.loc["Placebo", col])
                records.append(rec)
    summary = pd.DataFrame(records)
    summary.to_csv(outdir / "shot_level_summary.csv", index=False)
    return summary


def q1_rate_summary(df: pd.DataFrame, outdir: Path) -> pd.DataFrame:
    x = df[df["label"].isin(["Placebo", "Ativo"])].copy()
    rows = []
    for (dataset, label, lote), g in x.groupby(["dataset", "label", "lote"]):
        rows.append({
            "dataset": dataset,
            "label": label,
            "lote": lote,
            "n": len(g),
            "q1_rate": float(g["q1_futuro"].mean()),
            "consenso_mean_raw": float(g["consenso"].mean()),
        })
    out = pd.DataFrame(rows)
    out.to_csv(outdir / "q1_rate_by_lot.csv", index=False)
    return out


def analyze_one_dataset(df: pd.DataFrame, dataset: str, postselect: bool, window: int, feature_mode: str, n_perm: int, seed: int) -> List[Dict]:
    st = import_analysis_stack()
    RF = st["RandomForestClassifier"]
    LR = st["LogisticRegression"]
    binomtest = st["binomtest"]

    feat_df, X, y, groups, feature_cols = make_window_features(df, dataset, postselect, window, feature_mode)
    if feat_df.empty or len(np.unique(y)) < 2 or len(np.unique(groups)) < 2:
        return []

    models = {
        "RandomForest": RF(n_estimators=300, max_depth=8, random_state=seed, class_weight="balanced"),
        "LogisticRegression": LR(max_iter=5000, class_weight="balanced", solver="liblinear"),
    }

    rows = []
    for model_name, model in models.items():
        res = group_cv_predict(model, X, y, groups)
        acc = res["accuracy"]
        n = len(y)
        hits = int(round(acc * n))
        try:
            binom_p = float(binomtest(hits, n=n, p=0.5, alternative="greater").pvalue)
        except Exception:
            binom_p = np.nan
        perm_p = grouped_permutation_test(model, X, y, groups, acc, n_perm=n_perm, seed=seed) if n_perm else np.nan
        cm = res["confusion_matrix"]
        rows.append({
            "dataset": dataset,
            "postselect": postselect,
            "window": window,
            "feature_mode": feature_mode,
            "model": model_name,
            "n_windows": n,
            "n_lotes": int(len(np.unique(groups))),
            "accuracy": acc,
            "balanced_accuracy": res["balanced_accuracy"],
            "auc": res["auc"],
            "binom_p_naive": binom_p,
            "perm_p_grouped": perm_p,
            "cm_tn": int(cm[0, 0]),
            "cm_fp": int(cm[0, 1]),
            "cm_fn": int(cm[1, 0]),
            "cm_tp": int(cm[1, 1]),
            "feature_cols": ",".join(feature_cols),
        })
    return rows


def interpretation_flags(metrics: pd.DataFrame) -> List[str]:
    flags: List[str] = []
    if metrics.empty:
        return ["Nenhuma métrica calculada."]

    def get_acc(ds, post=True, model="RandomForest"):
        q = metrics[(metrics["dataset"] == ds) & (metrics["postselect"] == post) & (metrics["model"] == model)]
        if q.empty:
            return None
        return float(q.iloc[0]["accuracy"])

    real = get_acc("REAL", True)
    nulo = get_acc("NULO", True)
    phan_strict = get_acc("PHAN_STRICT_POSTHOC", True)
    phan_legacy = get_acc("PHAN_LEGACY_IDENTICAL_PUBS", True)

    if real is not None:
        flags.append(f"REAL pós-seleção RF: {real*100:.2f}%")
    if nulo is not None:
        flags.append(f"NULO pós-seleção RF: {nulo*100:.2f}%")
    if phan_strict is not None:
        flags.append(f"PHAN_STRICT pós-seleção RF: {phan_strict*100:.2f}%")
        if phan_strict > 0.54:
            flags.append("[ALERTA] PHAN_STRICT acima de 54%: há vazamento de análise ou rótulo pós-hoc não independente.")
        else:
            flags.append("[OK] PHAN_STRICT próximo de 50%: controle pós-hoc passou.")
    if phan_legacy is not None:
        flags.append(f"PHAN_LEGACY pós-seleção RF: {phan_legacy*100:.2f}%")
        if phan_legacy > 0.54:
            flags.append("[ALERTA] PHAN_LEGACY alto: diferença de slot/pub/ordem/drift/layout pode estar classificável mesmo com circuito idêntico.")

    if real is not None and nulo is not None:
        if real - nulo > 0.08:
            flags.append("[FORTE] REAL excede NULO por mais de 8 pontos percentuais.")
        else:
            flags.append("[FRACO] Separação REAL-NULO menor que 8 pontos percentuais.")

    return flags


def cmd_analyze(args) -> int:
    outdir = ensure_dir(args.outdir)
    files = expand_input_files(args.input)
    print("\n==========================================================")
    print(" ⚖️ PROJETO JANUS: ANÁLISE ULTRA-BLINDADA")
    print("==========================================================")
    print("[*] Arquivos:")
    for f in files:
        print(f"    - {f}")

    raw = load_raw_csvs(files)
    raw = add_basic_columns(raw)
    print(f"[*] Linhas totais: {len(raw):,}".replace(",", "."))
    print(f"[*] Datasets: {', '.join(sorted(raw['dataset'].astype(str).unique()))}")

    raw.to_csv(outdir / "analysis_input_merged.csv", index=False)

    shot_summary = shot_level_summary(raw, outdir)
    q1_summary = q1_rate_summary(raw, outdir)

    all_metrics = []
    datasets = sorted(raw["dataset"].dropna().astype(str).unique())
    for dataset in datasets:
        for postselect in [False, True]:
            rows = analyze_one_dataset(
                raw,
                dataset=dataset,
                postselect=postselect,
                window=args.window,
                feature_mode=args.feature_mode,
                n_perm=args.n_perm,
                seed=args.seed,
            )
            all_metrics.extend(rows)

    metrics = pd.DataFrame(all_metrics)
    metrics_path = outdir / "model_validation_metrics.csv"
    metrics.to_csv(metrics_path, index=False)

    # Relatório textual.
    report_lines = []
    report_lines.append("# Relatório Janus — Análise Ultra-Blindada\n")
    report_lines.append(f"Arquivos analisados: {len(files)}")
    report_lines.append(f"Linhas totais: {len(raw)}")
    report_lines.append(f"Window: {args.window}")
    report_lines.append(f"Feature mode: {args.feature_mode}")
    report_lines.append(f"Permutation tests: {args.n_perm}\n")

    report_lines.append("## Resumo shot-level\n")
    if not shot_summary.empty:
        report_lines.append(shot_summary.to_markdown(index=False))
    else:
        report_lines.append("Sem resumo shot-level.")

    report_lines.append("\n\n## Métricas de modelo\n")
    if not metrics.empty:
        cols = ["dataset", "postselect", "model", "n_windows", "accuracy", "balanced_accuracy", "auc", "binom_p_naive", "perm_p_grouped", "cm_tn", "cm_fp", "cm_fn", "cm_tp"]
        m2 = metrics[cols].copy()
        for c in ["accuracy", "balanced_accuracy", "auc", "binom_p_naive", "perm_p_grouped"]:
            m2[c] = m2[c].astype(float).map(lambda x: f"{x:.6f}" if pd.notnull(x) else "nan")
        report_lines.append(m2.to_markdown(index=False))
    else:
        report_lines.append("Nenhuma métrica calculada.")

    report_lines.append("\n\n## Flags interpretativas\n")
    for flag in interpretation_flags(metrics):
        report_lines.append(f"- {flag}")

    report_lines.append("\n\n## Arquivos gerados\n")
    report_lines.append(f"- {outdir / 'analysis_input_merged.csv'}")
    report_lines.append(f"- {outdir / 'shot_level_summary.csv'}")
    report_lines.append(f"- {outdir / 'q1_rate_by_lot.csv'}")
    report_lines.append(f"- {metrics_path}")

    report = "\n".join(report_lines)
    report_path = outdir / "JANUS_ANALYSIS_REPORT.md"
    report_path.write_text(report, encoding="utf-8")

    print("\n" + report)
    print("\n==========================================================")
    print(" Análise concluída")
    print("==========================================================")
    print(f"Relatório : {report_path}")
    print(f"Métricas  : {metrics_path}")
    return 0


# =============================================================================
# CLI
# =============================================================================


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Projeto Janus — extração IBM + análise ultra-blindada",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    ex = sub.add_parser("extract", help="Executa extração no IBM Quantum")
    ex.add_argument("--backend", default="ibm_fez", help="Backend IBM Quantum")
    ex.add_argument("--channel", default="ibm_quantum_platform", help="Canal QiskitRuntimeService")
    ex.add_argument("--token-env", default="IBM_QUANTUM_TOKEN", help="Nome da variável de ambiente com token IBM")
    ex.add_argument("--lots", type=int, default=5, help="Número de lotes/jobs")
    ex.add_argument("--shots", type=int, default=4096, help="Shots por pub/circuito")
    ex.add_argument("--theta", type=float, default=float(np.pi / 8), help="Ângulo CRY dos espiões")
    ex.add_argument("--optimization-level", type=int, default=3, choices=[0, 1, 2, 3], help="Nível de transpile")
    ex.add_argument("--seed-transpiler", type=int, default=1234, help="Seed do transpiler")
    ex.add_argument("--initial-layout", default=None, help="Layout físico fixo, exemplo: 12,13,14,15,16")
    ex.add_argument("--include-legacy-phan", action="store_true", help="Inclui PHAN_LEGACY com dois pubs idênticos pré-rotulados")
    ex.add_argument("--random-seed", type=int, default=42, help="Seed para ordem e rótulos pós-hoc")
    ex.add_argument("--run-tag", default=None, help="Tag manual da execução")
    ex.add_argument("--outdir", default="janus_run", help="Pasta de saída")
    ex.add_argument("--stop-on-error", action="store_true", help="Interrompe na primeira falha de job")
    ex.set_defaults(func=cmd_extract)

    an = sub.add_parser("analyze", help="Analisa CSVs brutos gerados pela extração")
    an.add_argument("--input", nargs="+", required=True, help="CSV(s) ou glob(s), exemplo janus_run/JANUS_RAW_*.csv")
    an.add_argument("--window", type=int, default=16, help="Tamanho da janela de features")
    an.add_argument("--feature-mode", choices=["basic", "expanded"], default="basic", help="Features de consenso apenas ou features por espião")
    an.add_argument("--n-perm", type=int, default=1000, help="Número de permutações por teste")
    an.add_argument("--seed", type=int, default=42, help="Seed de análise")
    an.add_argument("--outdir", default="janus_analysis", help="Pasta de relatório")
    an.set_defaults(func=cmd_analyze)

    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
