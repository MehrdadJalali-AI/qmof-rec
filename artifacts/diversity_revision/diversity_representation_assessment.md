# Diversity Representation Assessment

## Current masked objective-score distance

interpretable as application utility but too coarse; retained only as a diagnostic baseline
 Aggregate LEA Rel@5=0.8479, NDCG@5=1.0000, diversity=0.0000.

## Masked continuous physical-descriptor distance

uses density and band gap at full precision; interpretable but limited by missing band gaps and absent structural descriptors
 Aggregate LEA Rel@5=0.8479, NDCG@5=1.0000, diversity=0.0578.

## Formula-derived descriptor distance

available for all formula-bearing records; chemically interpretable but not structure-aware
 Aggregate LEA Rel@5=0.8477, NDCG@5=0.9998, diversity=0.1087.

## Deterministic semantic-proxy distance

reproducible existing semantic score; query-dependent and therefore less suitable as material diversity
 Aggregate LEA Rel@5=0.8479, NDCG@5=1.0000, diversity=0.0000.

## Formula-derived graph-proxy distance

available for all records but proxy-based, not CIF-derived graph embeddings
 Aggregate LEA Rel@5=0.8479, NDCG@5=1.0000, diversity=0.0293.

## Hybrid material distance

chosen final representation: full-precision physical descriptors plus formula and graph proxies; excludes void fraction and gives better material resolution without tuning to outcome
 Aggregate LEA Rel@5=0.8479, NDCG@5=1.0000, diversity=0.0224.

The final protocol selects the hybrid material representation because it avoids absent void fraction, uses full-precision observed density and band gap, keeps missing dimensions masked, and adds query-independent formula/graph-derived resolution. The objective-score representation is retained as a cautionary diagnostic because it is useful for scoring relevance but too discretized for material diversity.
