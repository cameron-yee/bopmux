# bopmux

Turns TMUX status bar into a sound visualizer

## Building

1. Clone repo
2. Run `sudo ./build.sh`

## Running

1. Run `bopmux start [gray,blue,pink]`
2. Play Spotify or whatever
3. Run `bopmux stop` to stop

You have to be running TMUX. Should be obvious, but you never know.

## Force kill

`pgrep -f "bopmux-visualizer"` followed by `kill <PID>`

### MacOS

Mac doesn't expose sound directly, so you have to create a multi-output device using BlackHole. Set your sound output to the multi-output device you created and you should be good.

## TODO

1. Create themes (gray, blue, party, etc)
2. Handle kill signal, SIGTERM

## Development Commands

- VENV: `source .venv/bin/activate`
- Run: `uv run main.py`
- Add: `uv add <dep>`
