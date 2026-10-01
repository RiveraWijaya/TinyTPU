// Applies ReLU and unsigned saturation to each selected accumulator.

module output_buffer#(
    parameter DATA_WIDTH = 6,   // width of input operands
    parameter PSUM_WIDTH = 15,  // width of accumulator
    parameter OUTR_WIDTH = 12,  // width of output buffer
    parameter ARRAY_SIZE = 4    // width of systolic array
)(
    // finished signed psums from PEs (muxed outside of this module)
    input logic                     clk,
    input logic                     rst,    // GLOBAL RESET
    input logic                     flush,  // flush pulse from systo fsm
    input logic [ARRAY_SIZE-1:0][PSUM_WIDTH-1:0]    psum,

    // output buffers (12-bit signed)
    output logic [ARRAY_SIZE-1:0][OUTR_WIDTH-1:0]   outBuff
);

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin // reset all output buffers
            for (int cols = 0; cols < ARRAY_SIZE; cols++) begin
                outBuff[cols] <= '0;
            end
        end else if (flush) begin
            for (int cols = 0; cols < ARRAY_SIZE; cols++) begin
                // Temporary variable keeps the signed-width checks Icarus-friendly.
                logic [PSUM_WIDTH-1:0] tmp_psum;
                tmp_psum = psum[cols];
                
                if (tmp_psum[PSUM_WIDTH-1])
                    outBuff[cols] <= '0;                            // ReLU: clamp negatives to zero
                else if (|tmp_psum[PSUM_WIDTH-2:OUTR_WIDTH])
                    outBuff[cols] <= {OUTR_WIDTH{1'b1}};            // saturate positive overflow
                else 
                    outBuff[cols] <= tmp_psum[OUTR_WIDTH-1:0];      // otherwise set buffer to bottom 12 bits
            end
        end

    end

endmodule
