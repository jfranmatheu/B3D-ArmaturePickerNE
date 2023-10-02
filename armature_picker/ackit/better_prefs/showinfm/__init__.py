# Copyright (c) 2021 Damon Lynch
# SPDX - License - Identifier: MIT

from .showinfm import (
    show_in_file_manager,
    valid_file_manager,
    user_file_manager,
    stock_file_manager,
)
from .system.linux import linux_desktop, LinuxDesktop, linux_desktop_humanize
from .constants import single_file_only, cannot_open_uris
