import os
import queue
import signal
import sys
import time
from visualizer import themes
from visualizer import tmux

import numpy as np

# Set environment variable before importing sounddevice. Value is not important.
os.environ["SD_ENABLE_ASIO"] = "1"
import sounddevice as sd


# print(sd.query_devices())
# 0 BlackHole 16ch, Core Audio (16 in, 16 out)
# > 1 MacBook Pro Microphone, Core Audio (1 in, 0 out)
# < 2 MacBook Pro Speakers, Core Audio (0 in, 2 out)
DEVICE = 0
DATA_TYPE = np.float32
CHANNELS = 16
TARGET_CHANNEL = (
    0  # Look at only the first channel (e.g., Left Channel) for visualization
)
BLOCK_SIZE = 512
LATENCY = "low"
SAMPLE_RATE = 44100  # Sampling rate (Hz)

ATTACK_SPEED = 0.7  # How fast bars jump up on audio spikes (0.0 to 1.0)
FREQUENCY_BINS = 1  # Number of frequency bins to print
GRAVITY = 0.5  # How fast the bars float down (characters per frame)
REFRESH_RATE = 1 / 30

TMUX_SERVER = None
USER_STATUS_STYLE = None
USER_STATUS_LEFT = None
USER_STATUS_RIGHT = None
USER_WINDOW_STATUS_CURRENT_STYLE = None
USER_WINDOW_STATUS_STYLE = None

# Thread-safe queue to pass audio frames from callback to visualizer
AUDIO_QUEUE = queue.Queue()
SMOOTHED_PUMPED_LEVELS = np.zeros(FREQUENCY_BINS)


def update_frequency_pumped_level(db_value, current_frequency_pumped_level, theme):
    max_pumped_level = len(theme) - 1
    target_frequency_pumped_level = max(0, min(int(db_value), max_pumped_level))

    # Apply Physics Engine (Snappy Rise, Constant Gravity Drop)
    if target_frequency_pumped_level > current_frequency_pumped_level:
        return (
            current_frequency_pumped_level
            + (target_frequency_pumped_level - current_frequency_pumped_level)
            * ATTACK_SPEED
        )

    current_frequency_pumped_level -= GRAVITY
    return max(0.0, current_frequency_pumped_level)


def get_frequency_bin_pumped_level(bin_data, current_frequency_pumped_level, theme):
    """
    Convert raw voltage to human-perceived Decibels (dB scale)
    Adds 1e-5 to avoid a mathematically undefined log10(0)
    """
    mean_energy = np.mean(bin_data)
    db_value = 20 * np.log10(mean_energy + 1e-5) + 40
    return update_frequency_pumped_level(
        db_value, current_frequency_pumped_level, theme
    )


def process_frequency_bin(bin_index, bin_data, theme):
    global SMOOTHED_PUMPED_LEVELS, TMUX_SERVER

    current_frequency_pumped_level = SMOOTHED_PUMPED_LEVELS[bin_index]
    updated_frequency_pumped_level = get_frequency_bin_pumped_level(
        bin_data, current_frequency_pumped_level, theme
    )
    SMOOTHED_PUMPED_LEVELS[bin_index] = updated_frequency_pumped_level

    pumped_level_lookup = int(updated_frequency_pumped_level)

    tmux.update_user_status_background_colors(pumped_level_lookup, theme, TMUX_SERVER)


def process_audio_data(audio_data, theme):
    """
    window: Fades the edges of the audio chunk to prevent glitchy noise.
    rfft: Splits the blended wave into its component musical pitches.
    np.abs: Converts the scientific results into simple volume bars you can draw on your screen.
    np.array_split: Splits into frequency bins (low bass -> upper treble)
    """
    channel_data = audio_data.reshape(-1, CHANNELS)[:, TARGET_CHANNEL]
    window = np.hanning(len(channel_data))
    fft_complex = np.fft.rfft(channel_data * window)
    fft_magnitude = np.abs(fft_complex)

    fft_split = np.array_split(fft_magnitude, FREQUENCY_BINS)

    for i, bin_data in enumerate(fft_split):
        process_frequency_bin(i, bin_data, theme)


def audio_callback(indata, frames, time_info, status):
    global AUDIO_QUEUE
    audio_buffer = np.frombuffer(memoryview(indata), dtype=DATA_TYPE)
    AUDIO_QUEUE.put(audio_buffer.copy())


def start(theme):
    global TMUX_SERVER
    global USER_STATUS_STYLE
    global USER_STATUS_LEFT
    global USER_STATUS_RIGHT
    global USER_WINDOW_STATUS_CURRENT_STYLE
    global USER_WINDOW_STATUS_STYLE

    TMUX_SERVER = tmux.init_server()

    USER_STATUS_STYLE = tmux.get_global_tmux_option("status-style", TMUX_SERVER)
    USER_STATUS_LEFT = tmux.get_global_tmux_option("status-left", TMUX_SERVER)
    USER_STATUS_RIGHT = tmux.get_global_tmux_option("status-right", TMUX_SERVER)
    USER_WINDOW_STATUS_CURRENT_STYLE = tmux.get_global_tmux_option(
        "window-status-current-style", TMUX_SERVER
    )
    USER_WINDOW_STATUS_STYLE = tmux.get_global_tmux_option(
        "window-status-style", TMUX_SERVER
    )

    tmux.initialize_visualizer_config(TMUX_SERVER)

    input_stream = sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        blocksize=BLOCK_SIZE,
        device=DEVICE,
        dtype=DATA_TYPE,
        callback=audio_callback,
        latency=LATENCY,
    )

    with input_stream:
        try:
            while True:
                time.sleep(REFRESH_RATE)

                latest_frame = None

                # Consume queue to skip lagging frames and capture ONLY the newest audio data
                while not AUDIO_QUEUE.empty():
                    latest_frame = AUDIO_QUEUE.get_nowait()

                if latest_frame is not None:
                    process_audio_data(latest_frame, theme)
        except KeyboardInterrupt:
            tmux.reset_user_tmux_option("status-style", USER_STATUS_STYLE, TMUX_SERVER)
            tmux.reset_user_tmux_option("status-left", USER_STATUS_LEFT, TMUX_SERVER)
            tmux.reset_user_tmux_option("status-right", USER_STATUS_RIGHT, TMUX_SERVER)
            tmux.reset_user_tmux_option(
                "window-status-current-style",
                USER_WINDOW_STATUS_CURRENT_STYLE,
                TMUX_SERVER,
            )
            tmux.reset_user_tmux_option(
                "window-status-style", USER_WINDOW_STATUS_STYLE, TMUX_SERVER
            )


def run():
    selected_theme = themes.themes.get(sys.argv[1], None)
    if selected_theme is None:
        raise ValueError(f"Selected theme does not exist: {selected_theme}")

    start(selected_theme)


def handle_stop(signum, frame):
    global TMUX_SERVER
    print("visualizer stopped")

    tmux.reset_user_tmux_option("status-style", USER_STATUS_STYLE, TMUX_SERVER)
    tmux.reset_user_tmux_option("status-left", USER_STATUS_LEFT, TMUX_SERVER)
    tmux.reset_user_tmux_option("status-right", USER_STATUS_RIGHT, TMUX_SERVER)
    tmux.reset_user_tmux_option(
        "window-status-current-style", USER_WINDOW_STATUS_CURRENT_STYLE, TMUX_SERVER
    )
    tmux.reset_user_tmux_option(
        "window-status-style", USER_WINDOW_STATUS_STYLE, TMUX_SERVER
    )

    sys.exit(0)


signal.signal(signal.SIGTERM, handle_stop)
signal.signal(signal.SIGINT, handle_stop)
