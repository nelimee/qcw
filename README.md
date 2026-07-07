`qcw` stands for **q**uantum **c**ircuit **w**rapper and aims at providing a unique interface to access quantum circuit information from different frameworks.

This package has been written to improve the modularity of [`qprof`](https://github.com/nelimee/qprof), a tool I wrote during my PhD at CERFACS. It is current quite outdated, but should be installable with old Python versions (see [`pyproject.toml`](./pyproject.toml) for compatibility).

The main package is located in [`src/qcw`](./src/qcw/) and defines the interface that children `qcw-*` namespace packages should implement as well as wrappers to automatically discover the `qcw-*` packages installed.


