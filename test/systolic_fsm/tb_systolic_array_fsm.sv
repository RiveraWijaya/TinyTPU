`timescale 1ns/1ps
`default_nettype none

module tb_systolic_array_fsm;
    logic clk;
    logic rst;
    logic ena;
    logic forward_pulse;
    logic clear;
    logic flush;
    logic [6:0] clear_diagonal;
    logic [6:0] flush_diagonal;
    logic [1:0] c_out_select;

    systolic_array_fsm #(
        .K_DIM(8)
    ) dut (
        .clk(clk),
        .rst(rst),
        .ena(ena),
        .forward_pulse(forward_pulse),
        .clear(clear),
        .flush(flush),
        .clear_diagonal(clear_diagonal),
        .flush_diagonal(flush_diagonal),
        .c_out_select(c_out_select)
    );

    initial begin
        $dumpfile("systolic_array_fsm.fst");
        $dumpvars(0, tb_systolic_array_fsm);
    end
endmodule

`default_nettype wire
