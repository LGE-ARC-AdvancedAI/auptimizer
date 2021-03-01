"""
..
  Copyright (c) 2018 LG Electronics Inc.
  SPDX-License-Identifier: GPL-3.0-or-later

aup.EE.Resource.util.ResourceThreadPoolExecutor
=======================================

Child class of python std ThreadPoolExecutor, extended for customization reasons.

APIs
----
"""

from concurrent.futures import _base
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures.thread import _WorkItem


class ResourceThreadPoolExecutor(ThreadPoolExecutor):
    def __init__(self, *args, **kwargs):
        super(ResourceThreadPoolExecutor, self).__init__(*args, **kwargs)
    
    def submit(self, fn, *args, **kwargs):
        with self._shutdown_lock:
            if self._shutdown:
                return None

            f = _base.Future()
            w = _WorkItem(f, fn, args, kwargs)

            self._work_queue.put(w)
            self._adjust_thread_count()
            return f
