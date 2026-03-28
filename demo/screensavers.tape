# screensavers.tape -- Showcase screensaver animations
# Cycles through several screensaver views to demonstrate the ambient mode.
#
# Record: vhs demo/screensavers.tape
# Output: demo/screensavers.gif

Output demo/screensavers.gif

# -- Window & font setup --------------------------------------------------
Set FontSize 16
Set Width 800
Set Height 600
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms
Set Padding 16

# -- Launch the panel viewer -----------------------------------------------
Type "cd ~/Desktop/Projects/claude-panel && uv run claude-panel"
Enter

# Wait for TUI to render
Sleep 3s

# Navigate past main and status screens to reach screensavers
Right
Sleep 1s
Right
Sleep 3s

# Cycle to next screensaver
Right
Sleep 3s

# Cycle to another screensaver
Right
Sleep 3s

# Let the last one animate for a moment
Sleep 2s

# Quit
Type "q"
Sleep 500ms
