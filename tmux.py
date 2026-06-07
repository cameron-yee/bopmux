import libtmux

GRAY_GRADIENT = [
    "#1a1a1a",
    "#212121",
    "#282828",
    "#2f2f2f",
    "#363636",
    "#3d3d3d",
    "#444444",
    "#4b4b4b",
    "#525252",
    "#595959",
    "#606060",
    "#676767",
    "#6e6e6e",
    "#757575",
    "#7c7c7c",
    "#838383",
    "#8a8a8a",
    "#919191",
    "#989898",
    "#9f9f9f",
    "#a6a6a6",
    "#adadad",
    "#b4b4b4",
    "#bbbbbb",
    "#c2c2c2",
    "#c9c9c9",
    "#d0d0d0",
    "#d7d7d7",
    "#dedede",
    "#e6e6e6",
]


def get_user_status_style():
    server = libtmux.Server()
    if not server.sessions:
        return

    status_style = server.show_option("status-style", global_=True)
    return status_style


def update_user_status_style(i):
    server = libtmux.Server()

    if not server.sessions:
        return

    color = GRAY_GRADIENT[i]
    server.cmd("set-option", "-g", "status-style", f"bg={color}")


def reset_user_status_style(user_status_style):
    if user_status_style is not None:
        server = libtmux.Server()
        if not server.sessions:
            return
        server.cmd("set-option", "-g", "status-style", user_status_style)
