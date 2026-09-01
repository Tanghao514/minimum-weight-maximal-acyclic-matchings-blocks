# Small-instance baseline comparison

The production dynamic program and the definition-level exhaustive solver were run on the same deterministic generated graphs. All optimum values agreed.

| Family | n | Instances | Median m | DP median/s | Brute median/s | Median speedup |
|---|---:|---:|---:|---:|---:|---:|
| block_graph | 4 | 5 | 4 | 0.000709 | 0.000242 | 0.44x |
| block_graph | 6 | 5 | 8 | 0.001441 | 0.001766 | 1.41x |
| block_graph | 8 | 5 | 13 | 0.001979 | 0.005629 | 2.99x |
| block_graph | 10 | 5 | 17 | 0.002115 | 0.020599 | 10.68x |
| block_graph | 12 | 5 | 20 | 0.002574 | 0.052247 | 27.36x |
| block_graph | 14 | 5 | 26 | 0.003317 | 0.197687 | 59.60x |
| cactus | 4 | 5 | 4 | 0.000637 | 0.000270 | 0.48x |
| cactus | 6 | 5 | 6 | 0.000650 | 0.000939 | 1.41x |
| cactus | 8 | 5 | 8 | 0.001295 | 0.002582 | 1.81x |
| cactus | 10 | 5 | 11 | 0.001657 | 0.007569 | 4.22x |
| cactus | 12 | 5 | 13 | 0.001423 | 0.030744 | 22.39x |
| cactus | 14 | 5 | 16 | 0.001628 | 0.079237 | 41.95x |
| mixed | 4 | 5 | 4 | 0.000586 | 0.000291 | 0.47x |
| mixed | 6 | 5 | 6 | 0.000765 | 0.001142 | 1.61x |
| mixed | 8 | 5 | 10 | 0.001001 | 0.003219 | 4.96x |
| mixed | 10 | 5 | 11 | 0.000925 | 0.009618 | 10.84x |
| mixed | 12 | 5 | 16 | 0.002143 | 0.037279 | 18.02x |
| mixed | 14 | 5 | 17 | 0.002230 | 0.116236 | 53.93x |
| multipartite | 4 | 5 | 3 | 0.000842 | 0.000149 | 0.18x |
| multipartite | 6 | 5 | 6 | 0.001117 | 0.000506 | 0.62x |
| multipartite | 8 | 5 | 9 | 0.001505 | 0.002131 | 1.43x |
| multipartite | 10 | 5 | 11 | 0.002107 | 0.005480 | 2.60x |
| multipartite | 12 | 5 | 16 | 0.002699 | 0.029625 | 10.38x |
| multipartite | 14 | 5 | 17 | 0.003027 | 0.060266 | 16.76x |
