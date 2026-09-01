# Paper-ready experimental results

The production implementation was validated against exhaustive search on every target-class graph in the NetworkX graph atlas (up to seven vertices), under one unweighted and two signed-weight scenarios per graph. The separate correctness audit records 1,341 solver-versus-brute-force comparisons, 1,341 reconstructed witnesses checked from the definition, 8,734 comparisons between the fast checker and the definition-level checker, and 360 additional randomly generated weighted instances, with no discrepancy.

The scale benchmark contains 56 deterministic cases and 168 fresh-process runs. It covers block graphs, cactus graphs, complete-multipartite block trees, mixtures of cycles and complete-multipartite blocks, a single long cycle, a single sparse $K_{2,n-2}$ block, and dense complete graphs. Both unit-weight and signed-weight instances were tested. Every reported witness passed the independent fast checker.

## Largest instances

| Mode | Family | n | m | Blocks | Matching size | Solve/s | Verify/s | Peak MiB |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| unweighted | mixed_block_tree | 100,000 | 160,284 | 34,736 | 20,079 | 18.8895 | 0.7147 | 331.4 |
| unweighted | block_graph_tree | 100,000 | 211,000 | 44,437 | 12,832 | 27.5315 | 0.4889 | 369.4 |
| unweighted | cactus_block_tree | 100,000 | 116,223 | 33,053 | 27,775 | 13.3866 | 0.7151 | 314.2 |
| unweighted | multipartite_block_tree | 100,000 | 138,278 | 61,679 | 19,022 | 24.6447 | 0.6765 | 345.3 |
| unweighted | single_cycle | 100,000 | 100,000 | 1 | 33,334 | 13.1068 | 0.6497 | 350.8 |
| unweighted | single_K2n | 100,000 | 199,996 | 1 | 1 | 16.7681 | 0.1314 | 448.5 |
| unweighted | dense_complete | 1,000 | 499,500 | 1 | 1 | 23.8351 | 0.0958 | 399.6 |
| weighted | mixed_block_tree | 100,000 | 160,284 | 34,736 | 25,201 | 19.3839 | 0.6770 | 351.8 |
| weighted | block_graph_tree | 100,000 | 211,000 | 44,437 | 18,473 | 27.9829 | 0.5833 | 396.6 |
| weighted | cactus_block_tree | 100,000 | 116,223 | 33,053 | 32,423 | 17.6289 | 0.8229 | 326.9 |
| weighted | multipartite_block_tree | 100,000 | 138,278 | 61,679 | 24,068 | 24.9804 | 0.6309 | 367.4 |
| weighted | single_cycle | 100,000 | 100,000 | 1 | 38,723 | 11.2283 | 0.7175 | 364.7 |
| weighted | single_K2n | 100,000 | 199,996 | 1 | 1 | 17.2534 | 0.1330 | 481.9 |
| weighted | dense_complete | 1,000 | 499,500 | 1 | 1 | 27.3966 | 0.0867 | 452.4 |

## Interpretation boundary

The regressions and plots are descriptive implementation evidence only. The $O(|V|+|E|)$ claim is established by the proof. Runtime and RSS depend on Python, NetworkX, the allocator, hardware, and the deterministic instance generators. Peak RSS includes the interpreter and graph representation, not only the dynamic-programming tables.
