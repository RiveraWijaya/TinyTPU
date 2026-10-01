/*
 * Systolic-array scheduler.
 *
 * The serialized input interface produces one array update every four clocks.
 * Each PE accumulator remains live until all K_DIM products for its output
 * have arrived. Completed anti-diagonals are flushed and cleared as the
 * wavefront exits the array; incomplete diagonals are never disturbed.
 */

`default_nettype none

module systolic_array_fsm #(
    parameter integer K_DIM = 8,
    parameter integer ARRAY_SIZE = 4
)(
    input  wire        clk,
    input  wire        rst,
    input  wire        ena,

    output logic       forward_pulse,
    output logic       clear,
    output logic       flush,
    output logic [2*ARRAY_SIZE-2:0] clear_diagonal,
    output logic [2*ARRAY_SIZE-2:0] flush_diagonal,
    output logic [1:0] c_out_select
);

localparam integer OUTPUT_DIAGONALS = 2 * ARRAY_SIZE - 1;
localparam integer UPDATE_COUNT_MAX = K_DIM + OUTPUT_DIAGONALS - 1;
localparam integer UPDATE_COUNT_WIDTH = $clog2(UPDATE_COUNT_MAX + 1);
localparam integer PHASE_WIDTH = $clog2(K_DIM);

typedef enum logic [2:0] {
    INIT,
    UPDATE,
    FLUSH,
    CLEAR,
    IDLE
} systo_state_t;

systo_state_t curr_state, next_state;
logic [UPDATE_COUNT_WIDTH-1:0] updates_seen;
logic [PHASE_WIDTH-1:0] completion_phase;
logic [OUTPUT_DIAGONALS-1:0] completed_diagonals;
logic accumulation_complete;

always_ff @(posedge clk or posedge rst) begin
    if (rst)
        curr_state <= INIT;
    else
        curr_state <= next_state;
end

always_comb begin
    next_state = curr_state;

    case (curr_state)
        INIT:   if (ena) next_state = UPDATE;
        UPDATE:          next_state = FLUSH;
        FLUSH:           next_state = CLEAR;
        CLEAR:           next_state = IDLE;
        IDLE:   if (ena) next_state = UPDATE;
        default:         next_state = INIT;
    endcase
end

// Saturating count is sufficient: after the full initial wavefront has
// completed, the same K_DIM-phase pattern repeats for subsequent matrices.
always_ff @(posedge clk or posedge rst) begin
    if (rst)
        updates_seen <= '0;
    else if ((curr_state == UPDATE) && (updates_seen < UPDATE_COUNT_MAX))
        updates_seen <= updates_seen + 1'b1;
end

assign accumulation_complete = (updates_seen >= K_DIM);

// Phase zero corresponds to the first completed output (C[0][0]). The phase
// advances once per array update after the K-beat accumulation warm-up.
always_ff @(posedge clk or posedge rst) begin
    if (rst)
        completion_phase <= '0;
    else if ((curr_state == CLEAR) && accumulation_complete) begin
        if (completion_phase == K_DIM - 1)
            completion_phase <= '0;
        else
            completion_phase <= completion_phase + 1'b1;
    end
end

// A diagonal d completes at update K_DIM+d. Diagonals separated by K_DIM can
// complete together (the K=4 compatibility case), while K=8 has one idle
// phase between successive matrices. This mask prevents premature clears.
always_comb begin
    completed_diagonals = '0;
    if (accumulation_complete) begin
        for (int diagonal = 0; diagonal < OUTPUT_DIAGONALS; diagonal++) begin
            if (((diagonal % K_DIM) == completion_phase) &&
                (updates_seen >= K_DIM + diagonal))
                completed_diagonals[diagonal] = 1'b1;
        end
    end
end

always_comb begin
    forward_pulse = (curr_state == UPDATE);
    flush = (curr_state == FLUSH) && (|completed_diagonals);
    clear = (curr_state == CLEAR) && (|completed_diagonals);
    flush_diagonal = flush ? completed_diagonals : '0;
    clear_diagonal = clear ? completed_diagonals : '0;
end

assign c_out_select = completion_phase[1:0];

endmodule

`default_nettype wire
