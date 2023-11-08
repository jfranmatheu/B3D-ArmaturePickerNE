
def get_subclasses_recursive(base_cls, only_outermost: bool = False):
    all_subclasses = []

    def iter_subclasses(cls):
        nonlocal all_subclasses
        subclasses = cls.__subclasses__()
        if only_outermost and len(subclasses) == 0:
            all_subclasses.append(cls)
        else:
            for subclass in subclasses:
                if not only_outermost:
                    all_subclasses.append(subclass)
                iter_subclasses(subclass)

    iter_subclasses(base_cls)
    return all_subclasses
