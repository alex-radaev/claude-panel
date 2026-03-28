# hero.tape -- Main hero GIF for README / project page
# Records ~18 seconds of the panel viewer in action:
#   main screen (mood) -> status screen -> ambient screensaver
#
# Record: vhs demo/hero.tape
# Output: demo/hero.gif

Output demo/hero.gif

# -- Window & font setup --------------------------------------------------
Set FontSize 16
Set Width 1280
Set Height 640
Set Theme "Catppuccin Mocha"
Set TypingSpeed 50ms
Set Padding 20

# -- Launch the panel viewer -----------------------------------------------
Type "cd ~/Desktop/Projects/claude-panel && uv run claude-panel"
Enter

# Wait for Textual TUI to fully render
Sleep 3s

# Main screen should be visible with mood emoji
Sleep 2s

# Navigate to the status screen
Right
Sleep 2s

# Navigate to the ambient screensaver
Right
Sleep 5s

# Quit the application
Type "q"
Sleep 500ms
