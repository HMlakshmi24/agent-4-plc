To count from 1 to 10 in a Mitsubishi FX/ST PLC using ladder logic, you would follow these steps to create a simple program using basic instructions. Here's how you can set it up:

1. **Initialize the Counter:**
   - Use a Reset (R) instruction to ensure your counter starts from zero. You might use a contact that triggers a reset, such as a start button or an initial power-up signal. The instruction would look like `R C0`, where C0 is the counter you're using.

2. **Set Up Counter Logic:**
   - Insert a normally open contact (NO) that represents the condition under which the counter should increment. This could be a sensor input or a pulse from a clock signal. Let's assume you're using an input on `X0`.
   - The actual counting will occur in a `C` (Counter) instruction. For example, `C0 K10` where C0 is the counter number and K10 is the target count of 10.

3. **Example Ladder Logic:**

   ```
   --| X0 |--------------[ C C0 K10 ]
   --| C0 |--------------( Y0 )
   --| F1 |--------------[ R C0 ]
   ```

   - **X0:** Represents the input that triggers the counter to increment each time it's activated.
   - **C C0 K10:** This instruction counts up every time `X0` is activated until it reaches 10. `C0` is the counter's memory location.
   - **|C0|---(Y0):** Once C0 reaches the count of 10, it will energize output Y0, which can be used for further processing, like turning on a light or activating another part of the system.
   - **F1:** A normally open contact for a reset function. When activated, it will reset the counter back to 0. This could be connected to a reset button or another control signal.

4. **Additional Considerations:**
   - Ensure your PLC cycle time is appropriate for your count speed. Debounce your inputs if necessary to avoid false counting from noisy signals.
   - You might need to consider whether and how to handle the counter roll-over, depending on the application.

This simple implementation should allow your PLC to count signals or events between 1 and 10 and activate an output based on this logic. Remember, this is a basic guide and might require adjustments based on your specific application and equipment needs.