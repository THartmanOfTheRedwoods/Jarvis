#!/usr/bin/env python

import time
import threading


class CallbackThread(threading.Thread):
    def __init__(self, target, callback=None, callback_args=None, callback_kwargs=None, *args, **kwargs):
        self.method = target
        super(CallbackThread, self).__init__(target=self.target_with_callback, *args, **kwargs)
        self.callback = callback
        self.callback_args = callback_args
        self.callback_kwargs = {} if callback_kwargs is None else callback_kwargs

    def target_with_callback(self, *args, **kwargs):
        method_return_val = self.method(*args, **kwargs)
        if method_return_val:
            self.callback_kwargs['method_return_val'] = method_return_val
        if self.callback is not None:
            self.callback(*self.callback_args, **self.callback_kwargs)


def my_thread_job(*args, **kwargs):
    # do any things here
    print("thread start successfully and sleep for 5 seconds")
    for arg in args:
        print(arg)
    for key, val in kwargs.items():
        print("{}, {}".format(key, val))
    time.sleep(5)
    print("thread ended successfully!")
    return "Hi"


def cb(param1, param2, *args, **kwargs):
    # this is run after your thread end
    print("callback function called")
    print("{} {}".format(param1, param2))
    for key, val in kwargs.items():
        print("{}, {}".format(key, val))


if __name__ == '__main__':
    thread = CallbackThread(
        target=my_thread_job,
        callback=cb,
        callback_args=("hello", "world"),
        args=("A", "B"),
        kwargs={"C": 1, "D": 2}
    )
    thread.start()
