import logging

# NOTE(plu5): It is flakey to use the internal map, but getLevelNamesMapping
# was not added until 3.11, and we need to support further back.
level_names = logging._nameToLevel.keys()
# NOTE(plu5): They don't want you to use getLevelName with a
# string. I'm not sure hardcoding the strings is any better, but I
# figure they are kind of part of the interface.
default_level = 'INFO'
debug_level = 'DEBUG'


def configLog(level):
    # type: (str) -> None
    logging.basicConfig(
        format='{asctime}.{msecs:.0f} [{name}] {levelname}: {message}',
        level=level, style='{', datefmt='%H:%M:%S')
    filterWarnings(level, debug_level)


def filterWarnings(current_level, target_level):
    # type: (str, str) -> None
    # Turn third-party warnings into `target_level` logs
    logging.captureWarnings(True)
    logging.getLogger('py.warnings').addFilter(
        lambda record: current_level == target_level)
