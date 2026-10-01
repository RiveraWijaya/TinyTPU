import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, ReadOnly, RisingEdge, Timer


@cocotb.test()
async def test_persistent_k8_schedule(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.rst.value = 1
    dut.ena.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst.value = 0
    dut.ena.value = 1

    update_count = 0
    flush_count = 0
    clear_count = 0
    flush_selects = []
    clear_masks = []

    for _ in range(64):
        await RisingEdge(dut.clk)
        await ReadOnly()

        state = int(dut.dut.curr_state.value)
        forward = int(dut.forward_pulse.value)
        flush = int(dut.flush.value)
        clear = int(dut.clear.value)
        completed = int(dut.dut.completed_diagonals.value)

        assert forward == (state == 1)
        assert flush == (state == 2 and completed != 0)
        assert clear == (state == 3 and completed != 0)

        if state == 1:
            update_count += 1
        if flush:
            flush_count += 1
            flush_selects.append(int(dut.c_out_select.value))
        if clear:
            clear_count += 1
            clear_masks.append(int(dut.clear_diagonal.value))

        await Timer(1, unit="ns")

    assert flush_count > 0
    assert clear_count == flush_count
    assert flush_selects[:4] == [0, 1, 2, 3]
    assert clear_masks[:7] == [1 << diagonal for diagonal in range(7)]
