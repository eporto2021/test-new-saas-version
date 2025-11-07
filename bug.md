11-07T02:29:29Z app[185e261c569428] syd [info][07/Nov/2025 02:29:29] INFO "stripe" message='Request to Stripe api' method=post url=https://api.stripe.com/v1/checkout/sessions
2025-11-07T02:29:30Z app[185e261c569428] syd [info][07/Nov/2025 02:29:30] INFO "stripe" message='Stripe API response' path=https://api.stripe.com/v1/checkout/sessions response_code=400
2025-11-07T02:29:30Z app[185e261c569428] syd [info][07/Nov/2025 02:29:30] INFO "stripe" error_code=None error_message='Price `price_1Rsf9ZGeAsCKk11AUxtMmhQs` is not available to be purchased because its product is not active.' error_param=line_items[0][price] error_type=invalid_request_error message='Stripe v1 API error received'
2025-11-07T02:29:30Z app[185e261c569428] syd [info][07/Nov/2025 02:29:30] DEBUG "django.template" Exception while resolving variable 'dark_mode' in template '500.html'.
2025-11-07T02:29:30Z app[185e261c569428] syd [info]Traceback (most recent call last):
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/sync.py", line 489, in thread_handler
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    raise exc_info[1]
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/core/handlers/exception.py", line 42, in inner
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    response = await get_response(request)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/sync.py", line 489, in thread_handler
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    raise exc_info[1]
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/core/handlers/base.py", line 253, in _get_response_async
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    response = await wrapped_callback(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]               ^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/sync.py", line 439, in __call__
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    ret = await asyncio.shield(exec_coro)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/current_thread_executor.py", line 40, in run
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    result = self.fn(*self.args, **self.kwargs)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/sync.py", line 493, in thread_handler
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    return func(*args, **kwargs)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/views/decorators/http.py", line 64, in inner
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    return func(request, *args, **kwargs)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/contrib/auth/decorators.py", line 59, in _view_wrapper
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    return view_func(request, *args, **kwargs)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/apps/subscriptions/views/checkout_views.py", line 21, in create_checkout_session
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    checkout_session = create_stripe_checkout_session(subscription_holder, price_id, request.user)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/apps/subscriptions/helpers.py", line 84, in create_stripe_checkout_session
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    checkout_session = stripe.checkout.Session.create(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/stripe/checkout/_session.py", line 4694, in create
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    cls._static_request(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/stripe/_api_resource.py", line 172, in _static_request
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    return _APIRequestor._global_instance().request(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/stripe/_api_requestor.py", line 197, in request
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    resp = requestor._interpret_response(rbody, rcode, rheaders, api_mode)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/stripe/_api_requestor.py", line 853, in _interpret_response
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    self.handle_error_response(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/stripe/_api_requestor.py", line 336, in handle_error_response
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    raise err
2025-11-07T02:29:30Z app[185e261c569428] syd [info]stripe._error.InvalidRequestError: Request req_vR5GfHt2pzvhwC: Price `price_1Rsf9ZGeAsCKk11AUxtMmhQs` is not available to be purchased because its product is not active.
2025-11-07T02:29:30Z app[185e261c569428] syd [info]During handling of the above exception, another exception occurred:
2025-11-07T02:29:30Z app[185e261c569428] syd [info]Traceback (most recent call last):
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/template/base.py", line 891, in _resolve_lookup
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    current = current[bit]
2025-11-07T02:29:30Z app[185e261c569428] syd [info]              ~~~~~~~^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/template/context.py", line 88, in __getitem__
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    raise KeyError(key)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]KeyError: 'dark_mode'
2025-11-07T02:29:30Z app[185e261c569428] syd [info]During handling of the above exception, another exception occurred:
2025-11-07T02:29:30Z app[185e261c569428] syd [info]Traceback (most recent call last):
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/template/base.py", line 897, in _resolve_lookup
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    if isinstance(current, BaseContext) and getattr(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]                                            ^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]AttributeError: type object 'Context' has no attribute 'dark_mode'
2025-11-07T02:29:30Z app[185e261c569428] syd [info]During handling of the above exception, another exception occurred:
2025-11-07T02:29:30Z app[185e261c569428] syd [info]Traceback (most recent call last):
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/template/base.py", line 907, in _resolve_lookup
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    current = current[int(bit)]
2025-11-07T02:29:30Z app[185e261c569428] syd [info]                      ^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]ValueError: invalid literal for int() with base 10: 'dark_mode'
2025-11-07T02:29:30Z app[185e261c569428] syd [info]During handling of the above exception, another exception occurred:
2025-11-07T02:29:30Z app[185e261c569428] syd [info]Traceback (most recent call last):
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/template/base.py", line 914, in _resolve_lookup
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    raise VariableDoesNotExist(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]django.template.base.VariableDoesNotExist: Failed lookup for key [dark_mode] in [{'True': True, 'False': False, 'None': None}]
2025-11-07T02:29:30Z app[185e261c569428] syd [info][07/Nov/2025 02:29:30] DEBUG "django.template" Exception while resolving variable 'project_meta' in template '500.html'.
2025-11-07T02:29:30Z app[185e261c569428] syd [info]Traceback (most recent call last):
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/sync.py", line 489, in thread_handler
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    raise exc_info[1]
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/core/handlers/exception.py", line 42, in inner
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    response = await get_response(request)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/sync.py", line 489, in thread_handler
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    raise exc_info[1]
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/core/handlers/base.py", line 253, in _get_response_async
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    response = await wrapped_callback(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]               ^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/sync.py", line 439, in __call__
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    ret = await asyncio.shield(exec_coro)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/current_thread_executor.py", line 40, in run
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    result = self.fn(*self.args, **self.kwargs)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/sync.py", line 493, in thread_handler
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    return func(*args, **kwargs)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/views/decorators/http.py", line 64, in inner
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    return func(request, *args, **kwargs)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/contrib/auth/decorators.py", line 59, in _view_wrapper
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    return view_func(request, *args, **kwargs)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/apps/subscriptions/views/checkout_views.py", line 21, in create_checkout_session
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    checkout_session = create_stripe_checkout_session(subscription_holder, price_id, request.user)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/apps/subscriptions/helpers.py", line 84, in create_stripe_checkout_session
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    checkout_session = stripe.checkout.Session.create(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/stripe/checkout/_session.py", line 4694, in create
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    cls._static_request(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/stripe/_api_resource.py", line 172, in _static_request
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    return _APIRequestor._global_instance().request(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/stripe/_api_requestor.py", line 197, in request
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    resp = requestor._interpret_response(rbody, rcode, rheaders, api_mode)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/stripe/_api_requestor.py", line 853, in _interpret_response
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    self.handle_error_response(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/stripe/_api_requestor.py", line 336, in handle_error_response
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    raise err
2025-11-07T02:29:30Z app[185e261c569428] syd [info]stripe._error.InvalidRequestError: Request req_vR5GfHt2pzvhwC: Price `price_1Rsf9ZGeAsCKk11AUxtMmhQs` is not available to be purchased because its product is not active.
2025-11-07T02:29:30Z app[185e261c569428] syd [info]During handling of the above exception, another exception occurred:
2025-11-07T02:29:30Z app[185e261c569428] syd [info]Traceback (most recent call last):
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/template/base.py", line 891, in _resolve_lookup
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    current = current[bit]
2025-11-07T02:29:30Z app[185e261c569428] syd [info]              ~~~~~~~^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/template/context.py", line 88, in __getitem__
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    raise KeyError(key)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]KeyError: 'project_meta'
2025-11-07T02:29:30Z app[185e261c569428] syd [info]During handling of the above exception, another exception occurred:
2025-11-07T02:29:30Z app[185e261c569428] syd [info]Traceback (most recent call last):
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/template/base.py", line 897, in _resolve_lookup
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    if isinstance(current, BaseContext) and getattr(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]                                            ^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]AttributeError: type object 'Context' has no attribute 'project_meta'
2025-11-07T02:29:30Z app[185e261c569428] syd [info]During handling of the above exception, another exception occurred:
2025-11-07T02:29:30Z app[185e261c569428] syd [info]Traceback (most recent call last):
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/template/base.py", line 907, in _resolve_lookup
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    current = current[int(bit)]
2025-11-07T02:29:30Z app[185e261c569428] syd [info]                      ^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]ValueError: invalid literal for int() with base 10: 'project_meta'
2025-11-07T02:29:30Z app[185e261c569428] syd [info]During handling of the above exception, another exception occurred:
2025-11-07T02:29:30Z app[185e261c569428] syd [info]Traceback (most recent call last):
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/template/base.py", line 914, in _resolve_lookup
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    raise VariableDoesNotExist(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]django.template.base.VariableDoesNotExist: Failed lookup for key [project_meta] in [{'True': True, 'False': False, 'None': None}, {'block': <Block Node: meta. Contents: [<TextNode: '\n'>, <IfNode>, <TextNode: '\n'>]>}]
2025-11-07T02:29:30Z app[185e261c569428] syd [info][07/Nov/2025 02:29:30] DEBUG "django.template" Exception while resolving variable 'GOOGLE_ANALYTICS_ID' in template '500.html'.
2025-11-07T02:29:30Z app[185e261c569428] syd [info]Traceback (most recent call last):
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/sync.py", line 489, in thread_handler
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    raise exc_info[1]
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/core/handlers/exception.py", line 42, in inner
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    response = await get_response(request)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/sync.py", line 489, in thread_handler
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    raise exc_info[1]
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/core/handlers/base.py", line 253, in _get_response_async
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    response = await wrapped_callback(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]               ^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/sync.py", line 439, in __call__
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    ret = await asyncio.shield(exec_coro)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/current_thread_executor.py", line 40, in run
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    result = self.fn(*self.args, **self.kwargs)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/sync.py", line 493, in thread_handler
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    return func(*args, **kwargs)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/views/decorators/http.py", line 64, in inner
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    return func(request, *args, **kwargs)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/contrib/auth/decorators.py", line 59, in _view_wrapper
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    return view_func(request, *args, **kwargs)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/apps/subscriptions/views/checkout_views.py", line 21, in create_checkout_session
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    checkout_session = create_stripe_checkout_session(subscription_holder, price_id, request.user)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/apps/subscriptions/helpers.py", line 84, in create_stripe_checkout_session
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    checkout_session = stripe.checkout.Session.create(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/stripe/checkout/_session.py", line 4694, in create
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    cls._static_request(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/stripe/_api_resource.py", line 172, in _static_request
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    return _APIRequestor._global_instance().request(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/stripe/_api_requestor.py", line 197, in request
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    resp = requestor._interpret_response(rbody, rcode, rheaders, api_mode)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/stripe/_api_requestor.py", line 853, in _interpret_response
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    self.handle_error_response(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/stripe/_api_requestor.py", line 336, in handle_error_response
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    raise err
2025-11-07T02:29:30Z app[185e261c569428] syd [info]stripe._error.InvalidRequestError: Request req_vR5GfHt2pzvhwC: Price `price_1Rsf9ZGeAsCKk11AUxtMmhQs` is not available to be purchased because its product is not active.
2025-11-07T02:29:30Z app[185e261c569428] syd [info]During handling of the above exception, another exception occurred:
2025-11-07T02:29:30Z app[185e261c569428] syd [info]Traceback (most recent call last):
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/template/base.py", line 891, in _resolve_lookup
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    current = current[bit]
2025-11-07T02:29:30Z app[185e261c569428] syd [info]              ~~~~~~~^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/template/context.py", line 88, in __getitem__
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    raise KeyError(key)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]KeyError: 'GOOGLE_ANALYTICS_ID'
2025-11-07T02:29:30Z app[185e261c569428] syd [info]During handling of the above exception, another exception occurred:
2025-11-07T02:29:30Z app[185e261c569428] syd [info]Traceback (most recent call last):
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/template/base.py", line 897, in _resolve_lookup
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    if isinstance(current, BaseContext) and getattr(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]                                            ^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]AttributeError: type object 'Context' has no attribute 'GOOGLE_ANALYTICS_ID'
2025-11-07T02:29:30Z app[185e261c569428] syd [info]During handling of the above exception, another exception occurred:
2025-11-07T02:29:30Z app[185e261c569428] syd [info]Traceback (most recent call last):
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/template/base.py", line 907, in _resolve_lookup
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    current = current[int(bit)]
2025-11-07T02:29:30Z app[185e261c569428] syd [info]                      ^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]ValueError: invalid literal for int() with base 10: 'GOOGLE_ANALYTICS_ID'
2025-11-07T02:29:30Z app[185e261c569428] syd [info]During handling of the above exception, another exception occurred:
2025-11-07T02:29:30Z app[185e261c569428] syd [info]Traceback (most recent call last):
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/template/base.py", line 914, in _resolve_lookup
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    raise VariableDoesNotExist(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]django.template.base.VariableDoesNotExist: Failed lookup for key [GOOGLE_ANALYTICS_ID] in [{'True': True, 'False': False, 'None': None}]
2025-11-07T02:29:30Z app[185e261c569428] syd [info][07/Nov/2025 02:29:30] DEBUG "django.template" Exception while resolving variable 'csrf_token' in template '500.html'.
2025-11-07T02:29:30Z app[185e261c569428] syd [info]Traceback (most recent call last):
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/sync.py", line 489, in thread_handler
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    raise exc_info[1]
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/core/handlers/exception.py", line 42, in inner
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    response = await get_response(request)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/sync.py", line 489, in thread_handler
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    raise exc_info[1]
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/core/handlers/base.py", line 253, in _get_response_async
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    response = await wrapped_callback(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]               ^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/sync.py", line 439, in __call__
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    ret = await asyncio.shield(exec_coro)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/current_thread_executor.py", line 40, in run
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    result = self.fn(*self.args, **self.kwargs)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/asgiref/sync.py", line 493, in thread_handler
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    return func(*args, **kwargs)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/views/decorators/http.py", line 64, in inner
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    return func(request, *args, **kwargs)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/contrib/auth/decorators.py", line 59, in _view_wrapper
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    return view_func(request, *args, **kwargs)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/apps/subscriptions/views/checkout_views.py", line 21, in create_checkout_session
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    checkout_session = create_stripe_checkout_session(subscription_holder, price_id, request.user)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/apps/subscriptions/helpers.py", line 84, in create_stripe_checkout_session
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    checkout_session = stripe.checkout.Session.create(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/stripe/checkout/_session.py", line 4694, in create
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    cls._static_request(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/stripe/_api_resource.py", line 172, in _static_request
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    return _APIRequestor._global_instance().request(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/stripe/_api_requestor.py", line 197, in request
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    resp = requestor._interpret_response(rbody, rcode, rheaders, api_mode)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/stripe/_api_requestor.py", line 853, in _interpret_response
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    self.handle_error_response(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    raise KeyError(key)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/template/base.py", line 907, in _resolve_lookup
2025-11-07T02:29:30Z app[185e261c569428] syd [info]          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-11-07T02:29:30Z app[185e261c569428] syd [info]During handling of the above exception, another exception occurred:
2025-11-07T02:29:30Z app[185e261c569428] syd [info]Traceback (most recent call last):
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/template/base.py", line 891, in _resolve_lookup
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    checkout_session = create_stripe_checkout_session(subscription_holder, price_id, request.user)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    if isinstance(current, BaseContext) and getattr(
2025-11-07T02:29:30Z app[185e261c569428] syd [info]  File "/code/.venv/lib/python3.12/site-packages/django/core/handlers/base.py", line 253, in _get_response_async
2025-11-07T02:29:30Z app[185e261c569428] syd [info]Traceback (most recent call last):
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    return func(*args, **kwargs)
2025-11-07T02:29:30Z app[185e261c569428] syd [info]    return func(request, *args, **kwargs)
2025-11-07T02:29:44Z app[2871547f4456d8] syd [info]2025/11/07 02:29:44 INFO New SSH session email=maxdavenport96@gmail.com verified=true


https://test-blue-smoke-97.fly.dev/subscriptions/stripe/create-checkout-session/

When clicking on Check each booking is on the run sheet as a drop off
Suscbribe button