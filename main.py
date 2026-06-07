import os
import queue
import time
import tmux

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
BLOCK_SIZE = 512
LATENCY = "low"
SAMPLE_RATE = 44100  # Sampling rate (Hz)

ATTACK_SPEED = 0.7     # How fast bars jump up on audio spikes (0.0 to 1.0)
FREQUENCY_BINS = 1     # Number of frequency bins to print
GRAVITY = 0.5          # How fast the bars float down (characters per frame)
MAX_PUMPED_LEVEL = 30  # Maximum height of a terminal bar in characters

REFRESH_RATE = 1 / 60

# Thread-safe queue to pass audio frames from callback to visualizer
audio_queue = queue.Queue()
smoothed_pumped_levels = np.zeros(FREQUENCY_BINS)


def update_frequency_pumped_level(db_value, current_frequency_pumped_level):
    target_frequency_pumped_level = max(0, min(int(db_value), MAX_PUMPED_LEVEL))

    # Apply Physics Engine (Snappy Rise, Constant Gravity Drop)
    if target_frequency_pumped_level > current_frequency_pumped_level:
        return (
            current_frequency_pumped_level
            + (target_frequency_pumped_level - current_frequency_pumped_level)
            * ATTACK_SPEED
        )

    current_frequency_pumped_level -= GRAVITY
    if current_frequency_pumped_level < 0:
        current_frequency_pumped_level = 0

    return current_frequency_pumped_level


def get_frequency_bin_pumped_level(bin_data, current_frequency_pumped_level):
    """
    Convert raw voltage to human-perceived Decibels (dB scale)
    Adds 1e-5 to avoid a mathematically undefined log10(0)
    """
    mean_energy = np.mean(bin_data)
    db_value = 20 * np.log10(mean_energy + 1e-5) + 40
    return update_frequency_pumped_level(db_value, current_frequency_pumped_level)


def process_frequency_bin(bin_index, bin_data):
    global smoothed_pumped_levels

    current_frequency_pumped_level = smoothed_pumped_levels[bin_index]
    updated_frequency_pumped_level = get_frequency_bin_pumped_level(
        bin_data, current_frequency_pumped_level
    )
    smoothed_pumped_levels[bin_index] = updated_frequency_pumped_level

    pumped_level_lookup = int(updated_frequency_pumped_level)
    tmux.update_user_status_style(pumped_level_lookup)


def process_audio_data(audio_data):
    """
    window: Fades the edges of the audio chunk to prevent glitchy noise.
    rfft: Splits the blended wave into its component musical pitches.
    np.abs: Converts the scientific results into simple volume bars you can draw on your screen.
    np.array_split: Splits into frequency bins (low bass -> upper treble)
    """
    window = np.hanning(len(audio_data))
    fft_complex = np.fft.rfft(audio_data * window)
    fft_magnitude = np.abs(fft_complex)

    fft_split = np.array_split(fft_magnitude, FREQUENCY_BINS)

    for i, bin_data in enumerate(fft_split):
        process_frequency_bin(i, bin_data)


def audio_callback(indata, frames, time_info, status):
    global audio_queue
    audio_buffer = np.frombuffer(memoryview(indata), dtype=DATA_TYPE)
    audio_queue.put(audio_buffer.copy())


def main():
    user_status_style = tmux.get_user_status_style()

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
                while not audio_queue.empty():
                    latest_frame = audio_queue.get_nowait()

                if latest_frame is not None:
                    process_audio_data(latest_frame)
        except KeyboardInterrupt:
            tmux.reset_user_status_style(user_status_style)


if __name__ == "__main__":
    main()
