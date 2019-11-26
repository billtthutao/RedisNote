import logging

SEVERITY={
    logging.DEBUG:'debug',
    logging.INFO:'info',
    logging.WARNING:'warning',
}

print(SEVERITY)

SEVERITY.update((name,name) for name in SEVERITY.values())

print(SEVERITY)