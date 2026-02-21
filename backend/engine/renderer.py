
def render_ladder(program):

    output = "LD (Ladder Diagram) Logic\n\n"

    for rung in program.rungs:

        output += f"{rung.title}\n\n"

        if not rung.branches or len(rung.branches) == 0:
            output += "    (Empty Rung)\n\n"
            continue

        # --- Render Main Branch (First Branch) ---
        first_branch = rung.branches[0]
        
        line = "|----"
        
        for el in first_branch:
            if el.type == "contact":
                # [ Name ] or [/ Name ]
                # Adjusted spacing for readability
                if el.normally_closed:
                    line += f"[/ {el.name} ]----"
                else:
                    line += f"[ {el.name} ]----"
            elif el.type == "coil": # Should typically be in output, but if in branch (series coil?)
                line += f"( {el.name} )----"
            elif el.type == "timer":
                line += f"( {el.timer_type} {el.name} )----"

        # Add Output (Coil/Timer) at end of line
        if rung.output:
            if rung.output.type == "timer":
                 line += f"| {rung.output.timer_type} {rung.output.name} |----|"
                 # Timer params rendering would need to be added on next line if Model supported it detailedly
            else:
                 line += f"( {rung.output.name} )----|"
        else:
            line += "|" # End rail if no output

        output += line + "\n"

        # --- Render Parallel Branches (Latch/OR) ---
        # Currently supporting 1 parallel level (typical latch)
        if len(rung.branches) > 1:
            for i in range(1, len(rung.branches)):
                branch = rung.branches[i]
                
                # Calculate padding to align with the start?
                # For simple latch, we assume it starts after the first contact or at the rail?
                # User snippet: "     |----" (Indented)
                # This implies the branch bypasses the first element?
                # Or starts at the rail? 
                # "Standard" latch usually starts after the stop button if stop is first.
                # BUT user snippet says:
                # |----[/ Stop ]----[ Start ]----( )
                #      |----[ Motor ]----|
                # This alignment implies correct indentation.
                # Since we don't know EXACTLY which contact it parallels without complex connection data,
                # we will use a standard indentation for now as per user instruction.
                
                branch_line = "     |----" 
                # Note: This hardcoded indent assumes the latch is across the SECOND element (Start Btn).
                # To be safer/industrial, we might want it to start at rail if it's an OR of the whole line.
                # But for "Start/Stop" with Stop First (which is Series), the Latch parallels the START button.
                # So it needs to skip the Stop button.
                
                for el in branch:
                     if el.type == "contact":
                        if el.normally_closed:
                            branch_line += f"[/ {el.name} ]----"
                        else:
                            branch_line += f"[ {el.name} ]----"
                
                branch_line += "|"
                output += branch_line + "\n"

        output += "\n"

    return output
