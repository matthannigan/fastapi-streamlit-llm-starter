[![https://img.shields.io/pypi/v/tenacity.svg](https://img.shields.io/pypi/v/tenacity.svg)](https://pypi.python.org/pypi/tenacity) [![https://circleci.com/gh/jd/tenacity.svg?style=svg](https://circleci.com/gh/jd/tenacity.svg?style=svg)](https://circleci.com/gh/jd/tenacity) [![Mergify Status](https://img.shields.io/endpoint.svg?url=https://api.mergify.com/badges/jd/tenacity&style=flat)](https://mergify.io/)

**Please refer to the** [tenacity documentation](https://tenacity.readthedocs.io/en/latest/) **for a better experience.**

Tenacity is an Apache 2.0 licensed general-purpose retrying library, written in Python, to simplify the task of adding retry behavior to just about anything. It originates from [a fork of retrying](https://github.com/rholder/retrying/issues/65) which is sadly no longer [maintained](https://julien.danjou.info/python-tenacity/). Tenacity isn’t api compatible with retrying but adds significant new functionality and fixes a number of longstanding bugs.

The simplest use case is retrying a flaky function whenever an Exception occurs until a value is returned.

```
import random
from tenacity import retry

@retry
def do_something_unreliable():
    if random.randint(0, 10) &gt; 1:
        raise IOError("Broken sauce, everything is hosed!!!111one")
    else:
        return "Awesome sauce!"

print(do_something_unreliable())
```

## Features

-   Generic Decorator API
-   Specify stop condition (i.e. limit by number of attempts)
-   Specify wait condition (i.e. exponential backoff sleeping between attempts)
-   Customize retrying on Exceptions
-   Customize retrying on expected returned result
-   Retry on coroutines
-   Retry code block with context manager

## Installation

To install _tenacity_, simply:

## Examples

### Basic Retry

As you saw above, the default behavior is to retry forever without waiting when an exception is raised.

```
@retry
def never_gonna_give_you_up():
    print("Retry forever ignoring Exceptions, don't wait between retries")
    raise Exception
```

### Stopping

Let’s be a little less persistent and set some boundaries, such as the number of attempts before giving up.

```
@retry(stop=stop_after_attempt(7))
def stop_after_7_attempts():
    print("Stopping after 7 attempts")
    raise Exception
```

We don’t have all day, so let’s set a boundary for how long we should be retrying stuff.

```
@retry(stop=stop_after_delay(10))
def stop_after_10_s():
    print("Stopping after 10 seconds")
    raise Exception
```

You can combine several stop conditions by using the | operator:

```
@retry(stop=(stop_after_delay(10) | stop_after_attempt(5)))
def stop_after_10_s_or_5_retries():
    print("Stopping after 10 seconds or 5 retries")
    raise Exception
```

### Waiting before retrying

Most things don’t like to be polled as fast as possible, so let’s just wait 2 seconds between retries.

```
@retry(wait=wait_fixed(2))
def wait_2_s():
    print("Wait 2 second between retries")
    raise Exception
```

Some things perform best with a bit of randomness injected.

```
@retry(wait=wait_random(min=1, max=2))
def wait_random_1_to_2_s():
    print("Randomly wait 1 to 2 seconds between retries")
    raise Exception
```

Then again, it’s hard to beat exponential backoff when retrying distributed services and other remote endpoints.

```
@retry(wait=wait_exponential(multiplier=1, min=4, max=10))
def wait_exponential_1():
    print("Wait 2^x * 1 second between each retry starting with 4 seconds, then up to 10 seconds, then 10 seconds afterwards")
    raise Exception
```

Then again, it’s also hard to beat combining fixed waits and jitter (to help avoid thundering herds) when retrying distributed services and other remote endpoints.

```
@retry(wait=wait_fixed(3) + wait_random(0, 2))
def wait_fixed_jitter():
    print("Wait at least 3 seconds, and add up to 2 seconds of random delay")
    raise Exception
```

When multiple processes are in contention for a shared resource, exponentially increasing jitter helps minimise collisions.

```
@retry(wait=wait_random_exponential(multiplier=1, max=60))
def wait_exponential_jitter():
    print("Randomly wait up to 2^x * 1 seconds between each retry until the range reaches 60 seconds, then randomly up to 60 seconds afterwards")
    raise Exception
```

Sometimes it’s necessary to build a chain of backoffs.

```
@retry(wait=wait_chain(*[wait_fixed(3) for i in range(3)] +
                       [wait_fixed(7) for i in range(2)] +
                       [wait_fixed(9)]))
def wait_fixed_chained():
    print("Wait 3s for 3 attempts, 7s for the next 2 attempts and 9s for all attempts thereafter")
    raise Exception
```

### Whether to retry

We have a few options for dealing with retries that raise specific or general exceptions, as in the cases here.

```
class ClientError(Exception):
    """Some type of client error."""

@retry(retry=retry_if_exception_type(IOError))
def might_io_error():
    print("Retry forever with no wait if an IOError occurs, raise any other errors")
    raise Exception

@retry(retry=retry_if_not_exception_type(ClientError))
def might_client_error():
    print("Retry forever with no wait if any error other than ClientError occurs. Immediately raise ClientError.")
    raise Exception
```

We can also use the result of the function to alter the behavior of retrying.

```
def is_none_p(value):
    """Return True if value is None"""
    return value is None

@retry(retry=retry_if_result(is_none_p))
def might_return_none():
    print("Retry with no wait if return value is None")
```

See also these methods:

```
retry_if_exception
retry_if_exception_type
retry_if_not_exception_type
retry_unless_exception_type
retry_if_result
retry_if_not_result
retry_if_exception_message
retry_if_not_exception_message
retry_any
retry_all
```

We can also combine several conditions:

```
def is_none_p(value):
    """Return True if value is None"""
    return value is None

@retry(retry=(retry_if_result(is_none_p) | retry_if_exception_type()))
def might_return_none():
    print("Retry forever ignoring Exceptions with no wait if return value is None")
```

Any combination of stop, wait, etc. is also supported to give you the freedom to mix and match.

It’s also possible to retry explicitly at any time by raising the TryAgain exception:

```
@retry
def do_something():
    result = something_else()
    if result == 23:
       raise TryAgain
```

### Error Handling

Normally when your function fails its final time (and will not be retried again based on your settings), a RetryError is raised. The exception your code encountered will be shown somewhere in the _middle_ of the stack trace.

If you would rather see the exception your code encountered at the _end_ of the stack trace (where it is most visible), you can set reraise=True.

```
@retry(reraise=True, stop=stop_after_attempt(3))
def raise_my_exception():
    raise MyException("Fail")

try:
    raise_my_exception()
except MyException:
    # timed out retrying
    pass
```

### Before and After Retry, and Logging

It’s possible to execute an action before any attempt of calling the function by using the before callback function:

```
import logging
import sys

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(3), before=before_log(logger, logging.DEBUG))
def raise_my_exception():
    raise MyException("Fail")
```

In the same spirit, It’s possible to execute after a call that failed:

```
import logging
import sys

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(3), after=after_log(logger, logging.DEBUG))
def raise_my_exception():
    raise MyException("Fail")
```

It’s also possible to only log failures that are going to be retried. Normally retries happen after a wait interval, so the keyword argument is called `before_sleep`:

```
import logging
import sys

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(3),
       before_sleep=before_sleep_log(logger, logging.DEBUG))
def raise_my_exception():
    raise MyException("Fail")
```

### Statistics

You can access the statistics about the retry made over a function by using the retry attribute attached to the function and its statistics attribute:

```
@retry(stop=stop_after_attempt(3))
def raise_my_exception():
    raise MyException("Fail")

try:
    raise_my_exception()
except Exception:
    pass

print(raise_my_exception.retry.statistics)
```

### Custom Callbacks

You can also define your own callbacks. The callback should accept one parameter called `retry_state` that contains all information about current retry invocation.

For example, you can call a custom callback function after all retries failed, without raising an exception (or you can re-raise or do anything really)

```
def return_last_value(retry_state):
    """return the result of the last call attempt"""
    return retry_state.outcome.result()

def is_false(value):
    """Return True if value is False"""
    return value is False

# will return False after trying 3 times to get a different result
@retry(stop=stop_after_attempt(3),
       retry_error_callback=return_last_value,
       retry=retry_if_result(is_false))
def eventually_return_false():
    return False
```

### RetryCallState

`retry_state` argument is an object of RetryCallState class:

_class_ `tenacity.``RetryCallState`(_retry\_object: tenacity.BaseRetrying, fn: Optional\[WrappedFn\], args: Any, kwargs: Any_)

State related to a single call wrapped with Retrying.

Constant attributes:

Variable attributes:

### Other Custom Callbacks

It’s also possible to define custom callbacks for other keyword arguments.

`my_stop`(_retry\_state_)

<table><colgroup><col> <col></colgroup><tbody><tr><th>Parameters:</th><td><strong>retry_state</strong> (<em>RetryState</em>) – info about current retry invocation</td></tr><tr><th>Returns:</th><td>whether or not retrying should stop</td></tr><tr><th>Return type:</th><td>bool</td></tr></tbody></table>

`my_wait`(_retry\_state_)

<table><colgroup><col> <col></colgroup><tbody><tr><th>Parameters:</th><td><strong>retry_state</strong> (<em>RetryState</em>) – info about current retry invocation</td></tr><tr><th>Returns:</th><td>number of seconds to wait before next retry</td></tr><tr><th>Return type:</th><td>float</td></tr></tbody></table>

`my_retry`(_retry\_state_)

<table><colgroup><col> <col></colgroup><tbody><tr><th>Parameters:</th><td><strong>retry_state</strong> (<em>RetryState</em>) – info about current retry invocation</td></tr><tr><th>Returns:</th><td>whether or not retrying should continue</td></tr><tr><th>Return type:</th><td>bool</td></tr></tbody></table>

`my_before`(_retry\_state_)

<table><colgroup><col> <col></colgroup><tbody><tr><th>Parameters:</th><td><strong>retry_state</strong> (<em>RetryState</em>) – info about current retry invocation</td></tr></tbody></table>

`my_after`(_retry\_state_)

<table><colgroup><col> <col></colgroup><tbody><tr><th>Parameters:</th><td><strong>retry_state</strong> (<em>RetryState</em>) – info about current retry invocation</td></tr></tbody></table>

`my_before_sleep`(_retry\_state_)

<table><colgroup><col> <col></colgroup><tbody><tr><th>Parameters:</th><td><strong>retry_state</strong> (<em>RetryState</em>) – info about current retry invocation</td></tr></tbody></table>

Here’s an example with a custom `before_sleep` function:

```
import logging

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

logger = logging.getLogger(__name__)

def my_before_sleep(retry_state):
    if retry_state.attempt_number &lt; 1:
        loglevel = logging.INFO
    else:
        loglevel = logging.WARNING
    logger.log(
        loglevel, 'Retrying %s: attempt %s ended with: %s',
        retry_state.fn, retry_state.attempt_number, retry_state.outcome)

@retry(stop=stop_after_attempt(3), before_sleep=my_before_sleep)
def raise_my_exception():
    raise MyException("Fail")

try:
    raise_my_exception()
except RetryError:
    pass
```

### Changing Arguments at Run Time

You can change the arguments of a retry decorator as needed when calling it by using the retry\_with function attached to the wrapped function:

```
@retry(stop=stop_after_attempt(3))
def raise_my_exception():
    raise MyException("Fail")

try:
    raise_my_exception.retry_with(stop=stop_after_attempt(4))()
except Exception:
    pass

print(raise_my_exception.retry.statistics)
```

If you want to use variables to set up the retry parameters, you don’t have to use the retry decorator - you can instead use Retrying directly:

```
def never_good_enough(arg1):
    raise Exception('Invalid argument: {}'.format(arg1))

def try_never_good_enough(max_attempts=3):
    retryer = Retrying(stop=stop_after_attempt(max_attempts), reraise=True)
    retryer(never_good_enough, 'I really do try')
```

### Retrying code block

Tenacity allows you to retry a code block without the need to wraps it in an isolated function. This makes it easy to isolate failing block while sharing context. The trick is to combine a for loop and a context manager.

```
from tenacity import Retrying, RetryError, stop_after_attempt

try:
    for attempt in Retrying(stop=stop_after_attempt(3)):
        with attempt:
            raise Exception('My code is failing!')
except RetryError:
    pass
```

You can configure every details of retry policy by configuring the Retrying object.

With async code you can use AsyncRetrying.

```
from tenacity import AsyncRetrying, RetryError, stop_after_attempt

async def function():
   try:
       async for attempt in AsyncRetrying(stop=stop_after_attempt(3)):
           with attempt:
               raise Exception('My code is failing!')
   except RetryError:
       pass
```

In both cases, you may want to set the result to the attempt so it’s available in retry strategies like `retry_if_result`. This can be done accessing the `retry_state` property:

```
from tenacity import AsyncRetrying, retry_if_result

async def function():
   async for attempt in AsyncRetrying(retry=retry_if_result(lambda x: x &lt; 3)):
       with attempt:
           result = 1  # Some complex calculation, function call, etc.
       if not attempt.retry_state.outcome.failed:
           attempt.retry_state.set_result(result)
   return result
```

### Async and retry

Finally, `retry` works also on asyncio and Tornado (>= 4.5) coroutines. Sleeps are done asynchronously too.

```
@retry
async def my_async_function(loop):
    await loop.getaddrinfo('8.8.8.8', 53)
```

```
@retry
@tornado.gen.coroutine
def my_async_function(http_client, url):
    yield http_client.fetch(url)
```

You can even use alternative event loops such as curio or Trio by passing the correct sleep function:

```
@retry(sleep=trio.sleep)
async def my_async_function(loop):
    await asks.get('https://example.org')
```

## Contribute

1.  Check for open issues or open a fresh issue to start a discussion around a feature idea or a bug.
2.  Fork [the repository](https://github.com/jd/tenacity) on GitHub to start making your changes to the **main** branch (or branch off of it).
3.  Write a test which shows that the bug was fixed or that the feature works as expected.
4.  Add a [changelog](https://tenacity.readthedocs.io/en/latest/#Changelogs)
5.  Make the docs better (or more detailed, or more easier to read, or …)

### Changelogs

[reno](https://docs.openstack.org/reno/latest/user/usage.html) is used for managing changelogs. Take a look at their usage docs.

The doc generation will automatically compile the changelogs. You just need to add them.

```
# Opens a template file in an editor
tox -e reno -- new some-slug-for-my-change --edit
```