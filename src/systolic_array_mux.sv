/*
Four Situations:

Select 0:
Load PE00 c_out to output buffer position 1
Load PE31 c_out to output buffer position 2
Load PE22 c_out to output buffer position 3
Load PE13 c_out to output buffer position 4

Select 1:
Load PE10 c_out to output buffer position 1
Load PE01 c_out to output buffer position 2
Load PE32 c_out to output buffer position 3
Load PE23 c_out to output buffer position 4

Select 2:
Load PE20 c_out to output buffer position 1
Load PE11 c_out to output buffer position 2
Load PE02 c_out to output buffer position 3
Load PE33 c_out to output buffer position 4

Select 3:
Load PE30 c_out to output buffer position 1
Load PE21 c_out to output buffer position 2
Load PE12 c_out to output buffer position 3
Load PE03 c_out to output buffer position 4

*/
module systolic_array_mux #(
    parameter DATA_WIDTH = 6,   // width of input operands
    parameter PSUM_WIDTH  = 15, // width of accumulator
    parameter ARRAY_SIZE = 4
) (
    input logic                     clk,
    input logic                     rst,                    // Global reset

    input logic [2*ARRAY_SIZE-2:0]  clear_diagonal,         // Completed anti-diagonals to clear
    input logic [2*ARRAY_SIZE-2:0]  flush_diagonal,         // Completed anti-diagonals to expose
    output logic [ARRAY_SIZE - 1:0][ARRAY_SIZE - 1:0] PE_clear,
                                                            // clear wire for all PEs

    input logic [ARRAY_SIZE - 1:0][ARRAY_SIZE - 1:0][PSUM_WIDTH-1: 0]   c_out,
                                                            // c_out wire for all PEs
    input logic [1:0]               c_out_select,           // Select which c_out send to ReLU, 4 cases
    output logic [ARRAY_SIZE - 1:0][PSUM_WIDTH-1: 0]  psum  // selected c_out, send to ReLU

);

// reset MUX
always_comb begin
    // Explicit row assignments keep packed-array indexing compatible with
    // Icarus while mapping PE[row][col] to anti-diagonal row+col.
    PE_clear[0] = {clear_diagonal[3], clear_diagonal[2],
                   clear_diagonal[1], clear_diagonal[0]};
    PE_clear[1] = {clear_diagonal[4], clear_diagonal[3],
                   clear_diagonal[2], clear_diagonal[1]};
    PE_clear[2] = {clear_diagonal[5], clear_diagonal[4],
                   clear_diagonal[3], clear_diagonal[2]};
    PE_clear[3] = {clear_diagonal[6], clear_diagonal[5],
                   clear_diagonal[4], clear_diagonal[3]};
end

// c_out MUX
always_comb begin
    // Default everything to 0
    for (int cols = 0; cols < ARRAY_SIZE; cols++) begin
        psum[cols] = '0;
    end

    case (c_out_select)
        2'd0: begin
            if (flush_diagonal[0]) psum[0] = c_out[0][0];
            if (flush_diagonal[4]) begin
                psum[1] = c_out[3][1];
                psum[2] = c_out[2][2];
                psum[3] = c_out[1][3];
            end
        end

        2'd1: begin
            if (flush_diagonal[1]) begin
                psum[0] = c_out[1][0];
                psum[1] = c_out[0][1];
            end
            if (flush_diagonal[5]) begin
                psum[2] = c_out[3][2];
                psum[3] = c_out[2][3];
            end
        end

        2'd2: begin
            if (flush_diagonal[2]) begin
                psum[0] = c_out[2][0];
                psum[1] = c_out[1][1];
                psum[2] = c_out[0][2];
            end
            if (flush_diagonal[6]) psum[3] = c_out[3][3];
        end

        2'd3: begin
            if (flush_diagonal[3]) begin
                psum[0] = c_out[3][0];
                psum[1] = c_out[2][1];
                psum[2] = c_out[1][2];
                psum[3] = c_out[0][3];
            end
        end
    endcase
end

endmodule
