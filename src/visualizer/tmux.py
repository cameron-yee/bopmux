import libtmux
import re


def get_global_tmux_option(option):
    server = libtmux.Server()
    if not server.sessions:
        return

    return server.show_option(option, global_=True)


def update_user_status_background_colors(i, theme):
    server = libtmux.Server()
    if not server.sessions:
        return

    status_style_color = theme[i]
    window_status_current_style_color = theme[max(0, i - 5)]
    window_status_style_color = theme[max(0, i - 10)]

    regex = r"bg=[^,\]]+"
    status_left = get_global_tmux_option("status-left")
    if status_left is not None and status_left:
        updated_status_left = re.sub(
            regex, lambda m: f"bg={status_style_color}", status_left
        )
        server.cmd("set-option", "-g", "status-left", updated_status_left)

    status_right = get_global_tmux_option("status-right")
    if status_right is not None and status_right:
        updated_status_right = re.sub(
            regex, lambda m: f"bg={status_style_color}", status_right
        )
        server.cmd("set-option", "-g", "status-right", updated_status_right)

    server.cmd("set-option", "-g", "status-style", f"bg={status_style_color}")
    server.cmd(
        "set-option",
        "-g",
        "window-status-current-style",
        f"bg={window_status_current_style_color}",
    )
    server.cmd(
        "set-option", "-g", "window-status-style", f"bg={window_status_style_color}"
    )


def reset_user_tmux_option(option, value):
    if value is not None:
        server = libtmux.Server()
        if not server.sessions:
            return
        server.cmd("set-option", "-g", option, value)
