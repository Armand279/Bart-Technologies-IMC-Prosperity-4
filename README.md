# Bart-Technologies-IMC-Prosperity-4

To install backtester:

go to ./prosperity_rust... type git fetch -> will get data for new rounds

Install the toolchain once:
```sh
    xcode-select --install
    curl https://sh.rustup.rs -sSf | sh
    source "$HOME/.cargo/env"
    python3 --version
```

Then either install the CLI:

```
    make install
```
or just run the backtester directly:
```
    make backtest
```

how to run?
```
    rust_backtester \
    --trader /path/to/trader.py \
    --dataset tutorial \
    --artifact-mode full
```
upload logs to here:
https://prosperity.equirag.com/