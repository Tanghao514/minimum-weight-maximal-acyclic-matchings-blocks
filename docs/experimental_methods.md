# Experimental Methods for the Manuscript

## Correctness validation

The implementation was first compared with a definition-level exhaustive optimizer. Every nonempty graph in the NetworkX graph atlas was passed through the production target-class recognizer. For every accepted graph, one unit-weight scenario and two deterministic signed edge-weight/signed vertex-cost scenarios were solved by both algorithms. Every reconstructed witness was independently checked for the matching, induced-forest, and inclusion-wise maximality conditions. A second checker, based on attachment components of the saturated induced forest and not on the block decomposition, was compared with the definition-level checker on every matching of every connected accepted atlas graph. Additional deterministic randomly glued block compositions were compared with exhaustive optimization, and a non-supported house block was required to be rejected.

## Small-instance exhaustive baseline

Four generator families—cactus, block graph, complete-multipartite block tree, and mixed block tree—were tested at orders 4 through 14. Five deterministic graphs were generated for every family/order pair. The production dynamic program and exhaustive optimizer ran on the same in-memory graph. The experiment records optimum equality and descriptive elapsed times; the timing comparison is secondary to the exact agreement check.

## Scale benchmark

The scale matrix contains seven families in unit-weight and signed-weight modes. Sparse families were evaluated at 1,000, 10,000, 50,000, and 100,000 vertices; explicit complete graphs were evaluated at 100, 300, 600, and 1,000 vertices. Weighted and unweighted cases for a fixed family/order pair share the same structural seed and therefore the same graph. Each of the 56 cases was executed three times, with every repetition launched in a fresh Python subprocess. `time.perf_counter` measured generation, solving, and independent witness verification. Peak resident-set size was obtained from `resource.getrusage`. The reported solve time is the median of the three fresh-process repetitions and peak memory is their maximum.

## Integrity and interpretation

Each run records a SHA-256 digest of the canonicalized reconstructed matching. Raw JSONL and CSV data, deterministic seeds, software/hardware metadata, summaries, and plots are retained. Regression against \(|V|+|E|\) is descriptive and is not used as a proof of linearity.
