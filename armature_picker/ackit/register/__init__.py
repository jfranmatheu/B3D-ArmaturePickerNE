from .reg_handler import Handlers
from .reg_rna_sub import subscribe_to_rna_change, subscribe_to_rna_change_based_on_context # RNASubscription
from .reg_timer import new_timer_as_decorator


class Register:
    RNA_SUB = subscribe_to_rna_change
    RNA_SUB_CONTEXT = subscribe_to_rna_change_based_on_context
    TIMER = new_timer_as_decorator
    HANDLER = Handlers
