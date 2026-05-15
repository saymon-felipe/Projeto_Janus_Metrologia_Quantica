#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JANUS V8 — Auditoria de Massa Bruta / No-Signal Payload Test

Objetivo:
- Analisar um CSV de telegrafia V8 já extraído, sem precisar rodar IBM novamente.
- Testar se a mensagem/payload pode ser recuperada SEM pós-seleção (massa bruta).
- Comparar com a decodificação com q1_futuro == 1 como sanity check.
- Rodar classificação do bit enviado usando apenas espiões t0, com validação por ordem_sequencia.

Importante:
- A análise "raw" NÃO usa q1_futuro para filtrar.
- A análise de features NÃO usa q0_passado nem q1_futuro como input.
- O CSV de telegrafia contém apenas o canal REAL; ele não substitui NULO/PHAN_STRICT.
"""

import argparse
import os
import math
import random
from pathlib import Path

import numpy as np
import pandas as pd

from scipy.stats import skew, kurtosis, binomtest
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    roc_auc_score,
    confusion_matrix,
)

ALFABETO = " ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def char_para_5bit(char: str) -> str:
    idx = ALFABETO.find(char.upper())
    if idx == -1:
        idx = 0
    return format(idx, "05b")


def codificar_hamming_9_5(bits_5: str) -> str:
    d = [int(x) for x in bits_5]
    p1 = d[0] ^ d[1] ^ d[3] ^ d[4]
    p2 = d[0] ^ d[2] ^ d[3]
    p4 = d[1] ^ d[2] ^ d[3]
    p8 = d[4]
    return f"{p1}{p2}{d[0]}{p4}{d[1]}{d[2]}{d[3]}{p8}{d[4]}"


def aplicar_interleaving(blocos_9bits):
    resultado = ""
    for bit_idx in range(9):
        for bloco in blocos_9bits:
            resultado += bloco[bit_idx]
    return resultado


def construir_sequencia(mensagem: str):
    bits_base = [char_para_5bit(c) for c in mensagem]
    blocos_hamming = [codificar_hamming_9_5(b) for b in bits_base]
    payload_interleaved = aplicar_interleaving(blocos_hamming)
    cabecalho_calibracao = "0101"
    sequencia_completa = cabecalho_calibracao + payload_interleaved
    return sequencia_completa, bits_base, blocos_hamming, payload_interleaved


def extrair_features(vetor):
    vetor = np.asarray(vetor, dtype=float)
    if len(vetor) == 0:
        return np.zeros(4, dtype=float)
    # skew/kurtosis podem retornar nan quando vetor constante
    vals = np.array([
        np.mean(vetor),
        np.var(vetor),
        skew(vetor),
        kurtosis(vetor),
    ], dtype=float)
    return np.nan_to_num(vals, nan=0.0, posinf=0.0, neginf=0.0)


def decodificar_hamming(bloco_9):
    b = [int(x) for x in bloco_9]
    s1 = b[0] ^ b[2] ^ b[4] ^ b[6] ^ b[8]
    s2 = b[1] ^ b[2] ^ b[5] ^ b[6]
    s4 = b[3] ^ b[4] ^ b[5] ^ b[6]
    s8 = b[7] ^ b[8]
    sindrome = s1 * 1 + s2 * 2 + s4 * 4 + s8 * 8

    corrigido = False
    if sindrome != 0 and sindrome <= 9:
        b[sindrome - 1] ^= 1
        corrigido = True

    dados_5_bits = f"{b[2]}{b[4]}{b[5]}{b[6]}{b[8]}"
    idx_char = int(dados_5_bits, 2)
    char = ALFABETO[idx_char] if idx_char < len(ALFABETO) else "?"
    return {
        "bloco_original": bloco_9,
        "bloco_corrigido": "".join(str(x) for x in b),
        "dados_5_bits": dados_5_bits,
        "sindrome": sindrome,
        "corrigido": corrigido,
        "char": char,
    }


def reconstruir_mensagem(bits_recebidos: str):
    num_caracteres = len(bits_recebidos) // 9
    blocos = ["" for _ in range(num_caracteres)]

    idx = 0
    for bit_idx in range(9):
        for char_idx in range(num_caracteres):
            if idx < len(bits_recebidos):
                blocos[char_idx] += bits_recebidos[idx]
                idx += 1

    infos = [decodificar_hamming(b) for b in blocos]
    mensagem = "".join(info["char"] for info in infos)
    return mensagem, blocos, infos


def demodular_por_handshake(df, sequencia, modo_nome):
    assinaturas = []
    for i in range(len(sequencia)):
        bloco = df[df["ordem_sequencia"] == i]["consenso"].values
        assinaturas.append(extrair_features(bloco) if len(bloco) > 0 else np.zeros(4))

    assinatura_0 = np.mean([assinaturas[0], assinaturas[2]], axis=0)
    assinatura_1 = np.mean([assinaturas[1], assinaturas[3]], axis=0)

    bits_recebidos = ""
    distancias = []
    for idx, feat in enumerate(assinaturas[4:], start=4):
        d0 = float(np.linalg.norm(feat - assinatura_0))
        d1 = float(np.linalg.norm(feat - assinatura_1))
        bit = "0" if d0 < d1 else "1"
        bits_recebidos += bit
        distancias.append({"ordem_sequencia": idx, "d0": d0, "d1": d1, "bit_recebido": bit})

    mensagem, blocos, infos = reconstruir_mensagem(bits_recebidos)
    bits_esperados = sequencia[4:]
    bit_acc = sum(a == b for a, b in zip(bits_recebidos, bits_esperados)) / len(bits_esperados)

    return {
        "modo": modo_nome,
        "n_linhas": len(df),
        "bits_recebidos": bits_recebidos,
        "bit_accuracy_vs_payload": bit_acc,
        "mensagem": mensagem,
        "blocos": blocos,
        "infos": infos,
        "assinatura_0": assinatura_0.tolist(),
        "assinatura_1": assinatura_1.tolist(),
        "distancias": distancias,
    }


def criar_janelas(df, sequencia, window):
    rows = []
    for ordem, sub in df.groupby("ordem_sequencia", sort=True):
        ordem = int(ordem)
        if ordem < 0 or ordem >= len(sequencia):
            continue
        y = int(sequencia[ordem])

        # Mantém a ordem original das linhas dentro daquele circuito
        sub = sub.reset_index(drop=True)
        n = (len(sub) // window) * window

        cons = sub["consenso"].to_numpy(dtype=float)
        e1 = sub["espiao_1"].to_numpy(dtype=float)
        e2 = sub["espiao_2"].to_numpy(dtype=float)
        e3 = sub["espiao_3"].to_numpy(dtype=float)

        for start in range(0, n, window):
            end = start + window
            v = cons[start:end]
            w1, w2, w3 = e1[start:end], e2[start:end], e3[start:end]

            rows.append({
                "ordem_sequencia": ordem,
                "bit_enviado": y,
                "cons_mean": float(np.mean(v)),
                "cons_var": float(np.var(v)),
                "cons_flicker": float(np.sum(np.abs(np.diff(v))) / len(v)),
                "e1_mean": float(np.mean(w1)),
                "e2_mean": float(np.mean(w2)),
                "e3_mean": float(np.mean(w3)),
                "e1_flicker": float(np.sum(np.abs(np.diff(w1))) / len(w1)),
                "e2_flicker": float(np.sum(np.abs(np.diff(w2))) / len(w2)),
                "e3_flicker": float(np.sum(np.abs(np.diff(w3))) / len(w3)),
            })
    return pd.DataFrame(rows)


def avaliar_modelo(wdf, model_name, features, n_perm=0, random_seed=42):
    X = wdf[features].to_numpy(dtype=float)
    y = wdf["bit_enviado"].to_numpy(dtype=int)
    groups = wdf["ordem_sequencia"].to_numpy(dtype=int)

    if model_name == "logreg":
        clf = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=2000, class_weight="balanced", random_state=random_seed),
        )
    elif model_name == "rf":
        clf = RandomForestClassifier(
            n_estimators=120,
            max_depth=8,
            random_state=random_seed,
            n_jobs=-1,
            class_weight="balanced",
        )
    else:
        raise ValueError(model_name)

    gkf = GroupKFold(n_splits=5)
    preds = np.zeros_like(y)
    probs = np.zeros(len(y), dtype=float)

    for tr, te in gkf.split(X, y, groups):
        clf.fit(X[tr], y[tr])
        preds[te] = clf.predict(X[te])
        if hasattr(clf, "predict_proba"):
            probs[te] = clf.predict_proba(X[te])[:, 1]
        else:
            probs[te] = preds[te]

    acc = accuracy_score(y, preds)
    bal = balanced_accuracy_score(y, preds)
    auc = roc_auc_score(y, probs)
    cm = confusion_matrix(y, preds)

    # p naive é só referência; o mais relevante é permutação por grupo/ordem.
    successes = int(round(acc * len(y)))
    binom_p_naive = binomtest(successes, n=len(y), p=0.5, alternative="greater").pvalue

    perm_p = np.nan
    if n_perm and n_perm > 0:
        rng = np.random.default_rng(random_seed)
        unique_orders = np.array(sorted(wdf["ordem_sequencia"].unique()))
        order_to_label = {
            int(o): int(wdf.loc[wdf["ordem_sequencia"] == o, "bit_enviado"].iloc[0])
            for o in unique_orders
        }
        labels = np.array([order_to_label[int(o)] for o in unique_orders], dtype=int)

        ge = 0
        for p in range(n_perm):
            shuffled = labels.copy()
            rng.shuffle(shuffled)
            perm_map = {int(o): int(lbl) for o, lbl in zip(unique_orders, shuffled)}
            y_perm = np.array([perm_map[int(o)] for o in groups], dtype=int)

            preds_p = np.zeros_like(y_perm)
            probs_p = np.zeros(len(y_perm), dtype=float)
            for tr, te in gkf.split(X, y_perm, groups):
                clf.fit(X[tr], y_perm[tr])
                preds_p[te] = clf.predict(X[te])
                probs_p[te] = clf.predict_proba(X[te])[:, 1]

            acc_p = accuracy_score(y_perm, preds_p)
            if acc_p >= acc:
                ge += 1
        perm_p = (ge + 1) / (n_perm + 1)

    return {
        "model": model_name,
        "n_windows": int(len(wdf)),
        "accuracy": float(acc),
        "balanced_accuracy": float(bal),
        "auc": float(auc),
        "binom_p_naive": float(binom_p_naive),
        "perm_p_grouped": float(perm_p) if not np.isnan(perm_p) else np.nan,
        "cm_tn": int(cm[0, 0]),
        "cm_fp": int(cm[0, 1]),
        "cm_fn": int(cm[1, 0]),
        "cm_tp": int(cm[1, 1]),
    }


def simple_table(df):
    # Sem depender de tabulate
    if df.empty:
        return "(vazio)"
    cols = list(df.columns)
    str_rows = [[str(x) for x in row] for row in df.astype(object).values.tolist()]
    widths = [len(c) for c in cols]
    for row in str_rows:
        for i, x in enumerate(row):
            widths[i] = max(widths[i], len(x))
    header = " | ".join(c.ljust(widths[i]) for i, c in enumerate(cols))
    sep = "-+-".join("-" * w for w in widths)
    body = "\n".join(" | ".join(x.ljust(widths[i]) for i, x in enumerate(row)) for row in str_rows)
    return header + "\n" + sep + "\n" + body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="CSV janus_sinal_v8 gerado pelo transmissor")
    ap.add_argument("--message", default="STEINSGATE", help="Mensagem enviada esperada")
    ap.add_argument("--window", type=int, default=16)
    ap.add_argument("--n-perm", type=int, default=100)
    ap.add_argument("--outdir", default="janus_raw_leakage_analysis")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    sequencia, bits_base, blocos_hamming, payload = construir_sequencia(args.message)

    df = pd.read_csv(args.csv)
    required = ["ordem_sequencia", "q1_futuro", "q0_passado", "espiao_1", "espiao_2", "espiao_3"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(f"CSV sem colunas obrigatórias: {missing}")

    df["consenso"] = df["espiao_1"].astype(int) + df["espiao_2"].astype(int) + df["espiao_3"].astype(int)
    df["bit_enviado"] = df["ordem_sequencia"].map({i: int(b) for i, b in enumerate(sequencia)})

    if df["bit_enviado"].isna().any():
        bad = sorted(df.loc[df["bit_enviado"].isna(), "ordem_sequencia"].unique())
        raise SystemExit(f"CSV contém ordem_sequencia fora da mensagem esperada: {bad[:10]}")

    # Resumos shot-level por bit enviado. Aqui q1/q0 aparecem só para diagnóstico, não como feature.
    shot_summary = (
        df.groupby("bit_enviado")[["consenso", "espiao_1", "espiao_2", "espiao_3", "q0_passado", "q1_futuro"]]
        .mean()
        .reset_index()
    )
    shot_summary.to_csv(outdir / "shot_summary_by_bit.csv", index=False)

    # Demodulações
    modes = [
        ("RAW_MASSA_BRUTA_sem_pos_selecao", df),
        ("POSTSELECT_q1_igual_1_sanity_check", df[df["q1_futuro"] == 1].copy()),
        ("DIAGNOSTICO_q1_igual_0", df[df["q1_futuro"] == 0].copy()),
    ]

    demod_rows = []
    demod_details = {}
    for mode_name, dfx in modes:
        res = demodular_por_handshake(dfx, sequencia, mode_name)
        demod_details[mode_name] = res
        demod_rows.append({
            "modo": mode_name,
            "n_linhas": res["n_linhas"],
            "bit_accuracy_vs_payload": res["bit_accuracy_vs_payload"],
            "mensagem_decodificada": res["mensagem"],
            "bits_recebidos": res["bits_recebidos"],
        })

    demod_df = pd.DataFrame(demod_rows)
    demod_df.to_csv(outdir / "demodulation_summary.csv", index=False)

    # Janela + modelos: só espiões/consenso; nada de q0/q1.
    feature_sets = {
        "basic_consensus_only": ["cons_mean", "cons_var", "cons_flicker"],
        "spy_expanded": [
            "cons_mean", "cons_var", "cons_flicker",
            "e1_mean", "e2_mean", "e3_mean",
            "e1_flicker", "e2_flicker", "e3_flicker",
        ],
    }

    model_rows = []
    for mode_name, dfx in modes:
        wdf = criar_janelas(dfx, sequencia, args.window)
        wdf.to_csv(outdir / f"windows_{mode_name}.csv", index=False)

        for fs_name, features in feature_sets.items():
            for model_name in ["logreg", "rf"]:
                # Permutação em RF é mais pesada. Fazemos apenas na logreg por padrão.
                n_perm = args.n_perm if model_name == "logreg" else 0
                met = avaliar_modelo(wdf, model_name, features, n_perm=n_perm)
                met.update({
                    "modo": mode_name,
                    "feature_set": fs_name,
                })
                model_rows.append(met)

    metrics_df = pd.DataFrame(model_rows)
    metrics_df.to_csv(outdir / "raw_leakage_model_metrics.csv", index=False)

    # Relatório
    lines = []
    lines.append("# JANUS V8 — Auditoria de Massa Bruta / No-Signal Payload Test\n")
    lines.append(f"- CSV: `{args.csv}`")
    lines.append(f"- Mensagem esperada: `{args.message}`")
    lines.append(f"- Sequência total: {len(sequencia)} bits = 4 handshake + {len(payload)} payload")
    lines.append(f"- Linhas totais: {len(df)}")
    lines.append(f"- Ordem_sequencia: {df['ordem_sequencia'].min()}..{df['ordem_sequencia'].max()} ({df['ordem_sequencia'].nunique()} blocos)")
    lines.append(f"- Window: {args.window}")
    lines.append(f"- Permutações agrupadas na LogisticRegression: {args.n_perm}\n")

    lines.append("## Resumo shot-level por bit enviado\n")
    lines.append(simple_table(shot_summary.round(6)))
    lines.append("\n\n## Demodulação por handshake\n")
    lines.append(simple_table(demod_df[["modo", "n_linhas", "bit_accuracy_vs_payload", "mensagem_decodificada"]].round(6)))

    lines.append("\n\n## Métricas de modelos por janela\n")
    cols = [
        "modo", "feature_set", "model", "n_windows", "accuracy", "balanced_accuracy",
        "auc", "binom_p_naive", "perm_p_grouped", "cm_tn", "cm_fp", "cm_fn", "cm_tp"
    ]
    lines.append(simple_table(metrics_df[cols].round(6)))

    lines.append("\n\n## Interpretação automática\n")
    raw_demod = demod_df.loc[demod_df["modo"] == "RAW_MASSA_BRUTA_sem_pos_selecao"].iloc[0]
    post_demod = demod_df.loc[demod_df["modo"] == "POSTSELECT_q1_igual_1_sanity_check"].iloc[0]
    raw_log = metrics_df[
        (metrics_df["modo"] == "RAW_MASSA_BRUTA_sem_pos_selecao")
        & (metrics_df["feature_set"] == "basic_consensus_only")
        & (metrics_df["model"] == "logreg")
    ].iloc[0]

    lines.append(f"- Massa bruta decodificada: `{raw_demod['mensagem_decodificada']}`; bit accuracy: {raw_demod['bit_accuracy_vs_payload']:.3f}.")
    lines.append(f"- Pós-seleção q1=1 decodificada: `{post_demod['mensagem_decodificada']}`; bit accuracy: {post_demod['bit_accuracy_vs_payload']:.3f}.")
    lines.append(f"- Classificação RAW/LogReg/basic: accuracy={raw_log['accuracy']:.3f}, AUC={raw_log['auc']:.3f}, p_perm={raw_log['perm_p_grouped']:.6f}.")
    if raw_demod["bit_accuracy_vs_payload"] < 0.60 and raw_log["auc"] < 0.55:
        lines.append("- Veredito: neste CSV, a massa bruta NÃO recupera payload de forma operacional usando apenas os espiões.")
    else:
        lines.append("- Veredito: existe indício de vazamento na massa bruta; precisa de controles NULO/PHAN e replicação.")

    report = "\n".join(lines)
    (outdir / "JANUS_RAW_NO_SIGNAL_REPORT.md").write_text(report, encoding="utf-8")

    print(report)
    print(f"\nArquivos gerados em: {outdir}")


if __name__ == "__main__":
    main()
