# Invalidated run — do not use

This directory contains a partial, stopped run of the frozen robustness suite.
The pilot runner applied a global cap based on the lowest-dimensional
descriptor, unintentionally reducing the allowed ranks for all descriptors.
The DTD split 1 result therefore does not match the declared rank grid and is
invalid for comparison. It is preserved for provenance; no other condition
from this directory should be treated as a result.

The corrected protocol checks rank feasibility separately per descriptor and
inner fold. Its rerun uses the separate
`results/exploratory/complementary_budget_frozen_v2/` directory.
