"""experiments.search_spaces -- concrete SearchSpace/Decoder/Validity
instances for this paper's NAS domain, implementing p3net.problem's
generic interfaces."""

from search_spaces.nas_genotype import (
    ACTIVATIONS,
    CELL_EDGES,
    CELL_OPERATIONS,
    HYPERPARAMETER_NAMES,
    LEARNING_RATE_GRID,
    N_EDGES,
    N_NODES,
    NONE_OPERATION,
    TRIVIAL_AUGMENT,
    WEIGHT_DECAY_GRID,
    ContinuousThetaBounds,
    NASConfiguration,
    decode_nas_genotype,
    nas_search_space,
    nas_validity,
)

__all__ = [
    "ACTIVATIONS",
    "CELL_EDGES",
    "CELL_OPERATIONS",
    "HYPERPARAMETER_NAMES",
    "LEARNING_RATE_GRID",
    "N_EDGES",
    "N_NODES",
    "NONE_OPERATION",
    "TRIVIAL_AUGMENT",
    "WEIGHT_DECAY_GRID",
    "ContinuousThetaBounds",
    "NASConfiguration",
    "decode_nas_genotype",
    "nas_search_space",
    "nas_validity",
]
