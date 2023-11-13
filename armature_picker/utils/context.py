from enum import Enum, auto

from bpy.types import Context, Window


class CM_ContextSpaceOverride(Enum):
    VIEW_3D = auto()
    NODE_EDITOR = auto()

    class CM:
        def get_context(self, context: Context, area_type: str, window: Window | None = None) -> dict | None:
            if window is not None:
                windows: list[Window] = [window]
            else:
                windows: list[Window] = context.window_manager.windows

            for wnd in windows:
                for area in wnd.screen.areas:
                    if area.type == area_type:
                        for region in area.regions:
                            if region.type == 'WINDOW':
                                return {
                                    'window': wnd,
                                    'area': area,
                                    'region': region,
                                }

        def __init__(self, context: Context, area_type: str, window: Window | None = None) -> None:
            self.override_context = self.get_context(context, area_type, window=window)
            self.cm: lambda x: context.temp_override(x.override_context)

        def __enter__(self) -> None:
            if self.override_context is not None:
                return self.cm()

        def __exit__(self, *args, **kwargs) -> None:
            del self.cm
            del self.override_context


    def __call__(self, context: Context, window: Window | None = None) -> None:
        return CM_ContextSpaceOverride.CM(context, self.name, window=window)
