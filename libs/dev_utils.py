import functools
from collections import defaultdict
from inspect import getframeinfo, stack
from os.path import relpath
from pprint import pprint
from time import perf_counter

PROJECT_PATH = __file__.rsplit("/", 2)[0]


def print_type(display_value=True, **kwargs):
    if display_value:
        for k, v in kwargs.items():
            print(f"TYPE INFO -- {k}: {v}, {type(v)}")
    else:
        for k, v in kwargs.items():
            print(f"TYPE INFO -- {k}: {type(v)}")


already_processed = set()


def print_entry_and_return_types(some_function):
    """ Decorator for functions (pages) that require a login, redirect to login page on failure. """
    @functools.wraps(some_function)
    def wrapper(*args, **kwargs):
        name = getframeinfo(stack()[1][0]).filename.strip(PROJECT_PATH) + ": " + some_function.__name__

        # args and kwargs COULD mutate
        args_dict = {i: type(v) for i, v in enumerate(args)}
        kwargs_dict = {k: type(v) for k, v in kwargs.items()}
        # don't print multiple times...

        # place before adding to processed
        if name in already_processed:
            try:
                return some_function(*args, **kwargs)
            except Exception:
                if args_dict:
                    print(f"args in {name} (IT ERRORED!):")
                    pprint(args_dict)
                if kwargs_dict:
                    print(f"kwargs in {name} (IT ERRORED!):")
                    pprint(kwargs_dict)
                raise

        already_processed.add(name)

        rets = some_function(*args, **kwargs)

        if args_dict:
            print(f"args in {name}:")
            pprint(args_dict)

        if kwargs_dict:
            print(f"kwargs in {name}:")
            pprint(kwargs_dict)

        if isinstance(rets, tuple):
            types = ", ".join(str(type(t)) for t in rets)
            print(f"return types - {name} -> ({types})")
        else:
            print(f"return type - {name} -> {type(rets)}")
        return rets

    return wrapper


class timer_class():
    """ This is a simple class that is at the heart of the p() function declared below.
        This class consists of a datetime timer and a single function to access and advance it. """

    def __init__(self):
        self.timestamp = 0

    def set_timer(self, timestamp):
        self.timestamp = timestamp


# we use a defaultdict of timers to allow an arbitrary number of such timers.
timers = defaultdict(timer_class)


def p(timer_label=0, outer_caller=False):
    """ Handy little function that prints the file name line number it was called on and the
        amount of time since the function was last called.
        If you provide a label (anything with a string representation) that will be printed
        along with the time information.

    Examples:
         No parameters (source line numbers present for clarity):
            [app.py:65] p()
            [app.py:66] sleep(0.403)
            [app.py:67] p()
         This example's output:
            app.py:65 -- 0 -- profiling start...
            app.py:67 -- 0 -- 0.405514

         The second statement shows that it took just over the 0.403 time of the sleep statement
         to process between the two p calls.

         With parameters (source line numbers present for clarity):
             [app.py:65] p()
             [app.py:66] sleep(0.403)
             [app.py:67] p(1)
             [app.py:68] sleep(0.321)
             [app.py:69] p(1)
             [app.py:70] p()
         This example's output:
             app.py:65 -- 0 -- profiling start...
             app.py:67 -- 1 -- profiling start...
             app.py:69 -- 1 -- 0.32679
             app.py:70 -- 0 -- 0.731086
         Note that the labels are different for the middle two print statements.
         In this way you can interleave timers with any label you want and time arbitrary,
         overlapping subsections of code.  In this case I have two timers, one timed the
         whole process and one timed only the second timer.
    """
    timestamp = perf_counter()
    timer_object = timers[timer_label]
    if outer_caller:
        caller = getframeinfo(stack()[2][0])
    else:
        caller = getframeinfo(stack()[1][0])

    print("%s:%.f -- %s --" % (relpath(caller.filename), caller.lineno, timer_label), end=" ")
    # the first call to get_timer results in a zero elapsed time, so we can skip it.
    if timer_object.timestamp == 0:
        print("timer start...")
    else:
        print('%.10f' % (timestamp - timer_object.timestamp))
    # and at the very end we need to set the timer to the end of our actions (we have print
    # statements, which are slow)
    timer_object.set_timer(perf_counter())
