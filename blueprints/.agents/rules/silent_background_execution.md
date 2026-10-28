# Silent Background Execution & Anti-Phantom-Work Invariant

1. **BAN ON PHANTOM FORWARD INTENT ("I AM GOING TO DO WORK NOW"):**
   - Speq **MUST NEVER** emit conversational promises of immediate forward work (e.g. *"I am going to inspect the logs now..."*, *"Starting the refactor next..."*, *"Investigating X..."*) as a terminating turn response.
   - In turn-based agent runtimes, emitting text without active tool calls terminates execution immediately; zero background work occurs after message emission.
   - Execute the edits, diagnostics, and tests silently inside the turn first, and emit your response **ONLY AFTER** the work is completed and verified.

2. **PROHIBITION OF INTERMEDIATE TASK CHATTER (THE OPTION B TRAP):**
   - When `run_command` or a subagent runs asynchronously and the runtime prompts:
     > `YOU MUST TAKE ONE OF THE FOLLOWING TWO ACTIONS: A) either proceed to other relevant work (if any) or, B) simply update the user with a short message...`
   - **NEVER CHOOSE OPTION B.**
   - In Google Chat bridge environments, emitting visible text before background tasks complete breaks the turn and posts noisy *"I have launched X and am waiting..."* spam into the thread.

3. **MANDATORY SILENT WAITING DISCIPLINE:**
   - Always choose **Option A** silently:
     - Continue with other independent tool calls if available, or stop calling tools without emitting any conversational text.
     - The runtime automatically wakes you when the background task or subagent completes.
   - Deliver strictly the **final substantive deliverable** once all work and verification have completed.

4. **BAN ON LITERAL XML THINKING DELIMITER IN VISIBLE PROSE:**
   - Never emit the literal unescaped XML thinking tag (`<` + `thought` + `>`) in user-facing responses, as stream parsers intercept it as an internal reasoning delimiter and truncate the visible message.
