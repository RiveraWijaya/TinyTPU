"""Pin-level verification for the K-tiled TinyTPU."""

import os
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, RisingEdge, Timer


ARRAY_SIZE = 4
OUT_WIDTH = 12
K_DIM = int(os.getenv("K_DIM", "8"))
MAX_OUTPUT = (1 << OUT_WIDTH) - 1

# output-buffer lane -> (row, column), indexed by c_out_select
MUX_MAP = {
    0: ((0, 0), (3, 1), (2, 2), (1, 3)),
    1: ((1, 0), (0, 1), (3, 2), (2, 3)),
    2: ((2, 0), (1, 1), (0, 2), (3, 3)),
    3: ((3, 0), (2, 1), (1, 2), (0, 3)),
}


def golden_matmul(a, b):
    return [
        [sum(a[row][k] * b[k][col] for k in range(K_DIM)) for col in range(ARRAY_SIZE)]
        for row in range(ARRAY_SIZE)
    ]


def relu_saturate(value):
    return min(max(value, 0), MAX_OUTPUT)


def pack_int6(value):
    assert -32 <= value <= 31
    return value & 0x3F


def unpack_lanes(packed):
    return [int(packed >> (lane * OUT_WIDTH)) & MAX_OUTPUT for lane in range(ARRAY_SIZE)]


def read_pins(dut):
    return ((int(dut.uio_out.value) & 0xF0) << 4) | int(dut.uo_out.value)


class StreamObserver:
    """Checks that every output-buffer flush is serialized without bubbles."""

    def __init__(self, dut, max_groups):
        self.dut = dut
        self.max_groups = max_groups
        self.cycle = 0
        self.previous_output_state = 0
        self.active_group = None
        self.flushes = []
        self.serial_groups = 0

    async def sample(self):
        await ReadOnly()
        self.cycle += 1

        # handleOutput drives lane N when its pre-edge state was N+1.
        if self.active_group is not None and 1 <= self.previous_output_state <= 4:
            lane = self.previous_output_state - 1
            observed = read_pins(self.dut)
            expected = self.active_group[lane]
            assert observed == expected, (
                f"serialized lane {lane} mismatch at cycle {self.cycle}: "
                f"expected {expected}, got {observed}"
            )
            if lane == 3:
                self.active_group = None
                self.serial_groups += 1

        fsm = self.dut.user_project.systo_fsm_inst
        # Post-edge CLEAR means the preceding FLUSH edge just loaded outBuff.
        if (
            len(self.flushes) < self.max_groups
            and int(fsm.curr_state.value) == 3
            and int(fsm.accumulation_complete.value) == 1
        ):
            assert self.active_group is None, "a new output group overwrote an unserialized group"
            lanes = unpack_lanes(int(self.dut.user_project.outBuff.value))
            select = int(fsm.c_out_select.value)
            self.active_group = lanes
            self.flushes.append((self.cycle, select, lanes))

        self.previous_output_state = int(
            self.dut.user_project.io_interface_inst.O1.state.value
        )


async def clock_one_pair(dut, observer, a_value=0, b_value=0):
    a_bits = pack_int6(a_value)
    b_bits = pack_int6(b_value)
    dut.ui_in.value = (a_bits << 2) | (b_bits >> 4)
    dut.uio_in.value = b_bits & 0x0F
    await RisingEdge(dut.clk)
    await observer.sample()
    await Timer(1, unit="ns")


async def reset_dut(dut):
    dut.ena.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.ena.value = 1


async def run_matrix(dut, a, b, label):
    await reset_dut(dut)
    observer = StreamObserver(dut, max_groups=2 * ARRAY_SIZE - 1)

    # Wavefront input: row i and column i are delayed by i update beats.
    # K+6 update steps cover the full 4x4 drain; the extra group clocks the
    # final buffered step into the array and through the flush state.
    for step in range(K_DIM + 7):
        for lane in range(ARRAY_SIZE):
            k = step - lane
            a_value = a[lane][k] if 0 <= k < K_DIM else 0
            b_value = b[k][lane] if 0 <= k < K_DIM else 0
            await clock_one_pair(dut, observer, a_value, b_value)

    while observer.serial_groups < observer.max_groups:
        await clock_one_pair(dut, observer)

    assert len(observer.flushes) == 7
    assert [select for _, select, _ in observer.flushes] == [0, 1, 2, 3, 0, 1, 2]

    flush_cycles = [cycle for cycle, _, _ in observer.flushes]
    assert flush_cycles[0] == 4 * K_DIM + 2, (
        f"{label}: first flush cycle was {flush_cycles[0]}, "
        f"expected {4 * K_DIM + 2}"
    )
    assert all(b_cycle - a_cycle == 4 for a_cycle, b_cycle in zip(flush_cycles, flush_cycles[1:]))

    golden = golden_matmul(a, b)
    seen = set()
    for diagonal, (_, select, lanes) in enumerate(observer.flushes):
        for lane, (row, col) in enumerate(MUX_MAP[select]):
            if row + col == diagonal:
                expected = relu_saturate(golden[row][col])
                assert lanes[lane] == expected, (
                    f"{label}: C[{row}][{col}] expected {expected} "
                    f"from raw sum {golden[row][col]}, got {lanes[lane]}"
                )
                seen.add((row, col))
            else:
                assert lanes[lane] == 0, (
                    f"{label}: incomplete C[{row}][{col}] leaked to the output "
                    f"during diagonal {diagonal}: got {lanes[lane]}"
                )

    assert len(seen) == ARRAY_SIZE * ARRAY_SIZE
    assert observer.serial_groups == 7
    assert observer.cycle == 4 * K_DIM + 30

    dut._log.info(
        "%s K=%d: first flush=%d cycles, flush interval=4 cycles, "
        "all 16 results serialized by cycle=%d",
        label,
        K_DIM,
        flush_cycles[0],
        observer.cycle,
    )


@cocotb.test()
async def test_k_tiled_signed_int6_matmul(dut):
    """Deterministic, corner-case, and randomized golden-model checks."""

    cocotb.start_soon(Clock(dut.clk, 30, unit="ns").start())

    deterministic_a = [
        [1, -2, 3, -4, 5, -6, 7, -8][:K_DIM],
        [-8, 7, -6, 5, -4, 3, -2, 1][:K_DIM],
        [3, 0, -3, 6, -6, 9, -9, 12][:K_DIM],
        [31, -32, 1, -1, 16, -16, 2, -2][:K_DIM],
    ]
    deterministic_b_full = [
        [1, 2, 3, 4],
        [-1, -2, -3, -4],
        [5, -6, 7, -8],
        [-5, 6, -7, 8],
        [9, 10, -11, -12],
        [-9, -10, 11, 12],
        [13, -14, 15, -16],
        [-13, 14, -15, 16],
    ]
    await run_matrix(dut, deterministic_a, deterministic_b_full[:K_DIM], "deterministic")

    # Includes the +8192 K=8 accumulator-width corner and negative ReLU paths.
    corner_a = [[-32 for _ in range(K_DIM)] for _ in range(ARRAY_SIZE)]
    corner_b = [
        [-32, 31, -32, 31]
        for _ in range(K_DIM)
    ]
    await run_matrix(dut, corner_a, corner_b, "int6 corners")

    rng = random.Random(0x5448)
    for case_index in range(12):
        a = [[rng.randint(-32, 31) for _ in range(K_DIM)] for _ in range(ARRAY_SIZE)]
        b = [[rng.randint(-32, 31) for _ in range(ARRAY_SIZE)] for _ in range(K_DIM)]
        await run_matrix(dut, a, b, f"random seed=0x5448 case={case_index}")
