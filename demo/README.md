# Demo Recordings

This directory contains [VHS](https://github.com/charmbracelet/vhs) tape files
for recording terminal demo GIFs of claude-panel.

## Prerequisites

Install VHS (requires Go and ffmpeg):

```bash
brew install charmbracelet/tap/vhs
```

VHS also requires `ffmpeg`. If it is not already installed:

```bash
brew install ffmpeg
```

## Recording

Run any tape file to produce a GIF:

```bash
# Main hero demo (~18 seconds)
vhs demo/hero.tape

# Screensaver showcase (~15 seconds)
vhs demo/screensavers.tape

# Quick install animation (~5 seconds)
vhs demo/install.tape
```

Each command writes a `.gif` to the `demo/` directory. GIF files are
gitignored and should not be committed.

## Tape files

| File                | Description                                         | Duration |
|---------------------|-----------------------------------------------------|----------|
| `hero.tape`         | Full walkthrough: mood screen, status, screensaver  | ~18s     |
| `screensavers.tape` | Cycles through screensaver animations               | ~15s     |
| `install.tape`      | One-liner plugin install command                    | ~5s      |

## Tips for best results

- **Theme:** The tapes default to "Catppuccin Mocha". VHS ships with many
  built-in themes -- run `vhs themes` to list them. You can swap the
  `Set Theme` line in any tape file.

- **Font size:** Increase `Set FontSize` for crisper text in smaller
  embeds. 16-18 works well for GitHub README images.

- **Window size:** `Set Width` and `Set Height` control the virtual
  terminal dimensions in pixels. Wider windows (1280+) look better for
  full-panel demos; narrower ones (800) suit focused recordings.

- **Typing speed:** `Set TypingSpeed` controls simulated keystroke delay.
  Lower values (30ms) look snappier; higher values (100ms) look more
  natural.

- **Sleep durations:** Adjust `Sleep` commands to give animations enough
  time to render. If your machine is slower, increase the initial sleep
  after launching the TUI.

- **Re-recording:** Simply re-run the `vhs` command -- it overwrites the
  previous GIF.

- **Compression:** For smaller file sizes, pipe the output through
  `gifsicle`:
  ```bash
  gifsicle -O3 --lossy=80 demo/hero.gif -o demo/hero.gif
  ```
