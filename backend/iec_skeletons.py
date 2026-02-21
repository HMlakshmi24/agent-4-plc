ST_SKELETON = """PROGRAM {program_name}

VAR_INPUT
{input_decls}
END_VAR

VAR_OUTPUT
{output_decls}
END_VAR

VAR
{vars_decls}
END_VAR

(* Output Reset *)
{output_reset}

(* Edge Detection *)
{edge_detection}

(* Timer Calls *)
{timer_section}

(* Main Logic *)
{main_logic}


END_PROGRAM
"""

LD_SKELETON = """NETWORK 1
(* Input Processing & Reset *)
{net1_logic}

NETWORK 2  
(* Main Control Logic *)
{net2_logic}
END_PROGRAM"""

FBD_SKELETON = """PROGRAM {program_name}
(* Network 1: Input Processing *)
{net1_blocks}

(* Network 2: Main Logic *)
{net2_blocks}
END_PROGRAM"""

SFC_SKELETON = """PROGRAM {program_name}
(* Init Step *)
INITIAL_STEP Init:
    {init_action}
END_STEP

(* Transition *)
TRANSITION FROM Init TO Run := {transition};

(* Run Step *)
STEP Run:
    {run_action}
END_STEP
END_PROGRAM"""

IL_SKELETON = """PROGRAM {program_name}
(* Main Instruction List *)
{instructions}
END_PROGRAM"""
