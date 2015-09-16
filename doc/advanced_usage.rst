Advanced Usage
==============

Query Preprocessors
-------------------

InfiniSDK allows modification of HTTP request just before they are sent to the system through a mechanism query preprocessors.

The system objects exposes a context manager called `api.query_preprocessor`. This context manager gets a function which can modify the request before it is sent.

.. code-block:: python

    def unapproved(request):
        request.url = request.url.set_query_param('approved', 'false')

    with infinibox.api.query_preprocessor(unapproved):
        # Actions that require approval will be rejected within this context
