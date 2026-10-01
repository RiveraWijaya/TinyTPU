import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, ReadOnly, RisingEdge, Timer


ARRAY_SIZE = 4
K_DIM = 8
PSUM_WIDTH = 15


def signed_bits(value, width):
    value &= (1 << width) - 1
    return value - (1 << width) if value & (1 << (width - 1)) else value


@cocotb.test()
async def test_k8_array_against_golden(dut):
    cocotb.start_soon(Clock(dut.clk, 30, unit="ns").start())

    rng = random.Random(0xA448)
    a = [[rng.randint(-32, 31) for _ in range(K_DIM)] for _ in range(ARRAY_SIZE)]
    b = [[rng.randint(-32, 31) for _ in range(ARRAY_SIZE)] for _ in range(K_DIM)]

    dut.forward_systo.value = 0
    dut.PE_clear.value = 0
    dut.rst.value = 1
    await ClockCycles(dut.clk, 2)
    dut.rst.value = 0

    for step in range(K_DIM + 6):
        for lane in range(ARRAY_SIZE):
            k = step - lane
            a_value = a[lane][k] if 0 <= k < K_DIM else 0
            b_value = b[k][lane] if 0 <= k < K_DIM else 0
            getattr(dut, f"row{lane}_val").value = a_value & 0x3F
            getattr(dut, f"col{lane}_val").value = b_value & 0x3F

        dut.forward_systo.value = 1
        await RisingEdge(dut.clk)
        await ReadOnly()
        await Timer(1, unit="ns")

    dut.forward_systo.value = 0
    packed = int(dut.c_out.value)
    mask = (1 << PSUM_WIDTH) - 1

    for row in range(ARRAY_SIZE):
        for col in range(ARRAY_SIZE):
            offset = (row * ARRAY_SIZE + col) * PSUM_WIDTH
            observed = signed_bits((packed >> offset) & mask, PSUM_WIDTH)
            expected = sum(a[row][k] * b[k][col] for k in range(K_DIM))
            assert observed == expected, (
                f"C[{row}][{col}] expected {expected}, got {observed}"
            )
