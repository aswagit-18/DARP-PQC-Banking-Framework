"""Reproducible executed benchmark of standardized and classical crypto.

Measurements include OpenSSL command process launch + temp file I/O.
These are CLI-prototype wall clock latencies, not library-level primitive times.
Run: python -m experiments.pqc_benchmark --iterations 30
"""
from __future__ import annotations
import argparse
import csv
import json
import platform
import statistics
import time
from pathlib import Path

from pqc_layer.crypto_backend import OpenSSLPQC
from pqc_layer.access_control import PostQuantumAccessControl
from pqc_layer.transaction_demo import create_transaction_envelope, accept_transaction_envelope

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "tables"


def sampled(fn, n):
    samples = []
    last = None
    for _ in range(n):
        t0 = time.perf_counter_ns()
        last = fn()
        samples.append((time.perf_counter_ns() - t0) / 1e6)
    return last, samples


def record(rows, label, algorithm, samples, key_size_der, output_size):
    ordered = sorted(samples)
    rows.append({
        "operation": label,
        "algorithm": algorithm,
        "runs": len(ordered),
        "mean_ms": round(statistics.mean(ordered), 5),
        "median_ms": round(statistics.median(ordered), 5),
        "p95_ms": round(ordered[max(0, __import__("math").ceil(len(ordered)*.95)-1)], 5),
        "public_key_der_bytes": key_size_der if key_size_der is not None else "",
        "ciphertext_or_signature_bytes": output_size if output_size is not None else "",
    })


def main(n=30):
    if n < 3:
        raise ValueError("At least 3 iterations are required")
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    message = b'Bank transaction signed for benchmark, no personal data.'
    with OpenSSLPQC() as crypto:
        # Key generation is measured as a separate operation.
        for alg in ("X25519", "ML-KEM-512", "ML-KEM-768", "ML-KEM-1024", "ED25519", "ML-DSA-44", "ML-DSA-65", "ML-DSA-87", "SLH-DSA-SHA2-128s"):
            key, gen_samples = sampled(lambda a=alg: crypto.keypair(a), 3)
            size = crypto.public_key_der_size(key)
            record(rows, "key_generation", alg, gen_samples, size, None)
            if alg in {"X25519", "ML-KEM-512", "ML-KEM-768", "ML-KEM-1024"}:
                encapsulated, enc_samples = sampled(lambda: crypto.encapsulate(key), n)
                ct, ss1 = encapsulated
                ss2, dec_samples = sampled(lambda: crypto.decapsulate(key, ct), n)
                if ss1 != ss2:
                    raise AssertionError(f"KEM shared secret mismatch {alg}")
                record(rows, "encapsulate", alg, enc_samples, size, len(ct))
                record(rows, "decapsulate", alg, dec_samples, size, len(ct))
            else:
                sig, sign_samples = sampled(lambda: crypto.sign(key, message), n)
                if not crypto.verify(key, message, sig):
                    raise AssertionError(f"Digital signature failed verification {alg}")
                _, verify_samples = sampled(lambda: crypto.verify(key, message, sig), n)
                record(rows, "sign", alg, sign_samples, size, len(sig))
                record(rows, "verify", alg, verify_samples, size, len(sig))

        kem = crypto.keypair("ML-KEM-768")
        sig = crypto.keypair("ML-DSA-65")
        acl = PostQuantumAccessControl(crypto)
        acl.register("benchmark_teller", "teller", sig)
        times = []
        for i in range(n):
            txn = {"transaction_id": f"BENCH-{i}", "amount_minor_units": 1234, "currency": "INR"}
            start = time.perf_counter_ns()
            envelope = create_transaction_envelope(crypto, acl, kem, sig, actor="benchmark_teller", service_id="S06", action="initiate_payment", transaction=txn)
            receipt = accept_transaction_envelope(crypto, acl, kem, service_id="S06", action="initiate_payment", envelope=envelope)
            times.append((time.perf_counter_ns()-start)/1e6)
            if receipt["transaction"] != txn:
                raise AssertionError("End-to-end check failed")
        record(rows, "full_workflow", "ML-KEM-768+AES-256-GCM+ML-DSA-65+PQ-RBAC", times, None, None)
        metadata = {
            "benchmark_description": "Prototype wall-clock (OpenSSL CLI invocation + temp-file I/O), not raw primitive latency",
            "python": platform.python_version(), "platform": platform.platform(),
            "machine": platform.machine(), "processor": platform.processor(),
            "openssl": crypto.version, "iterations_per_operation": n,
            "input_message_bytes": len(message),
            "notes": "No network, TLS, HSM, banking database or actual customer workload. No direct numerical speed comparisons to other papers across environments. Benchmarks fluctuate."
        }
    with (OUT/"pqc_benchmark.csv").open("w", newline="", encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    (OUT/"pqc_benchmark_metadata.json").write_text(json.dumps(metadata, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    print(f'\n{"Operation":<19} {"Algorithm":<37} {"Median ms":>10} {"Bytes":>8}')
    for r in rows:
        print(f'{r["operation"]:<19} {r["algorithm"]:<37} {r["median_ms"]:10.4f} {str(r["ciphertext_or_signature_bytes"]):>8}')
    print('\nSaved:', OUT/'pqc_benchmark.csv')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--iterations', type=int, default=30)
    main(ap.parse_args().iterations)
