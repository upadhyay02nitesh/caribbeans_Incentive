"""Where this process is running.

On a normal server the app is long-lived: background threads finish their work
after the response has gone out, and the instance folder is writable. On a
serverless platform (Vercel, Lambda) neither holds — the process is frozen the
moment the response is returned, so a daemon thread may never run, and the
filesystem is read-only apart from /tmp.

Set SERVERLESS=1 (Vercel sets VERCEL=1 for you) and the same code paths run
inline instead of on a thread, and writable files go to /tmp.
"""

import os

SERVERLESS = bool(os.environ.get("SERVERLESS") or os.environ.get("VERCEL") or
                  os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

# Flask needs an absolute path; /tmp is the only writable place on these hosts.
TMP_INSTANCE = "/tmp/instance"


def run_background(target, *args, name=None, **kwargs):
    """Run work after the response — or inline when nothing would survive to run it."""
    if SERVERLESS:
        target(*args, **kwargs)
        return None
    import threading

    thread = threading.Thread(target=target, args=args, kwargs=kwargs, name=name, daemon=True)
    thread.start()
    return thread
