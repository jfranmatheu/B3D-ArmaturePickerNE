
def clear_graphic_caches():
    from .draw import clear_batch_cache, clear_gputex_cache
    from .offscreen import clear_offscreen_cache
    clear_batch_cache()
    clear_gputex_cache()
    clear_offscreen_cache()
