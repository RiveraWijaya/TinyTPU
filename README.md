# TinyTPU V2

TinyTPU V2 is a serialized signed-INT6 matrix engine for Tiny Tapeout. It
computes a 4x8 by 8x4 product on the existing 4x4, 16-PE systolic datapath.
Each PE preserves its accumulator across two consecutive K=4 input tiles, then
the completed result wavefront is flushed, ReLU-clamped, saturated to 12 bits,
and streamed through the original GPIO interface.

## Architecture

- 16 signed 6x6 multiply-accumulate processing elements
- 15-bit signed partial sums (covers the K=8 maximum of +8192)
- four serialized input clocks per systolic update
- persistent K=8 accumulation with no intermediate K=4 flush or clear
- width-generic ReLU and unsigned saturation into 12-bit outputs
- one 12-bit output per clock while the result stream is active

The default shared dimension is `K_DIM=8`. The RTL remains parameterized for
`K_DIM=4` compatibility testing.

## RTL simulation

From `test/`, run the default K=8 suite:

```sh
make K_DIM=8
```

Run the compatibility configuration separately:

```sh
make K_DIM=4
```

The cocotb suite drives only the Tiny Tapeout pins, checks deterministic,
corner-case, and seeded-random signed-INT6 matrices against a Python golden
model, verifies the serialized output stream, and asserts cycle-level latency
and flush cadence.

See [the project datasheet](docs/info.md) for the pin mapping and wavefront
loading convention.
