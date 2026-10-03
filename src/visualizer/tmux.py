import libtmux
import re


def init_server():
    server = libtmux.Server()
    return server


def get_global_tmux_option(option, server):
    if not server.sessions:
        return

    return server.show_option(option, global_=True)


def initialize_visualizer_config(server):
    if not server.sessions:
        return

    regex = r"bg=[^,\]]+"
    server_commands = []

    pane_active_border_style = get_global_tmux_option(
        "pane-active-border-style", server
    )
    if pane_active_border_style is not None and pane_active_border_style:
        updated_pane_active_border_style = re.sub(
            regex, "fg=#{@visualizer_current_bg}", pane_active_border_style
        )
        server_commands.extend(
            [
                "set-option",
                "-g",
                "pane-active-border-style",
                updated_pane_active_border_style,
                ";",
            ]
        )

    pane_border_style = get_global_tmux_option("pane-border-style", server)
    if pane_border_style is not None and pane_border_style:
        updated_pane_border_style = re.sub(
            regex, "fg=#{@visualizer_bg}", pane_border_style
        )
        server_commands.extend(
            ["set-option", "-g", "pane-border-style", updated_pane_border_style, ";"]
        )

    status_left = get_global_tmux_option("status-left", server)
    if status_left is not None and status_left:
        updated_status_left = re.sub(regex, "bg=#{@visualizer_bg}", status_left)
        server_commands.extend(
            ["set-option", "-g", "status-left", updated_status_left, ";"]
        )

    status_right = get_global_tmux_option("status-right", server)
    if status_right is not None and status_right:
        updated_status_right = re.sub(regex, "bg=#{@visualizer_bg}", status_right)
        server_commands.extend(
            ["set-option", "-g", "status-right", updated_status_right, ";"]
        )

    server_commands.extend(
        [
            "set-option",
            "-g",
            "pane-active-border-style",
            "fg=#{@visualizer_current_bg}",
            ";",
            "set-option",
            "-g",
            "pane-border-style",
            "fg=#{@visualizer_bg}",
            ";",
            "set-option",
            "-g",
            "status-style",
            "bg=#{@visualizer_bg}",
            ";",
            "set-option",
            "-g",
            "window-status-current-style",
            "bg=#{@visualizer_current_bg}",
            ";",
            "set-option",
            "-g",
            "window-status-style",
            "bg=#{@visualizer_window_status_bg}",
            ";",
        ]
    )

    server.cmd(*server_commands)


def update_user_status_background_colors(i, theme, server):
    if not server.sessions:
        return

    status_style_color = theme[i]
    window_status_current_style_color = theme[max(0, i - 5)]
    window_status_style_color = theme[max(0, i - 10)]

    # Push ONLY the colors into the corresponding tmux user variables.
    # No string logic, no parsing, no regex. It updates natively inside tmux.
    server.cmd(
        "set-option",
        "-g",
        "@visualizer_bg",
        status_style_color,
        ";",
        "set-option",
        "-g",
        "@visualizer_current_bg",
        window_status_current_style_color,
        ";",
        "set-option",
        "-g",
        "@visualizer_window_status_bg",
        window_status_style_color,
    )


def reset_user_tmux_option(option, value, server):
    if not server.sessions or value is None:
        return

    server.cmd("set-option", "-g", option, value)
