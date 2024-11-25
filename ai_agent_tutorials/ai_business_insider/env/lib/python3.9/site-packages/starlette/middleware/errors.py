from __future__ import annotations

import html
import inspect
import sys
import traceback
import typing

from starlette._utils import is_async_callable
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import HTMLResponse, PlainTextResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

STYLES = """
p {
    color: #211c1c;
}
.traceback-container {
    border: 1px solid #038BB8;
}
.traceback-title {
    background-color: #038BB8;
    color: lemonchiffon;
    padding: 12px;
    font-size: 20px;
    margin-top: 0px;
}
.frame-line {
    padding-left: 10px;
    font-family: monospace;
}
.frame-filename {
    font-family: monospace;
}
.center-line {
    background-color: #038BB8;
    color: #f9f6e1;
    padding: 5px 0px 5px 5px;
}
.lineno {
    margin-right: 5px;
}
.frame-title {
    font-weight: unset;
    padding: 10px 10px 10px 10px;
    background-color: #E4F4FD;
    margin-right: 10px;
    color: #191f21;
    font-size: 17px;
    border: 1px solid #c7dce8;
}
.collapse-btn {
    float: right;
    padding: 0px 5px 1px 5px;
    border: solid 1px #96aebb;
    cursor: pointer;
}
.collapsed {
  display: none;
}
.source-code {
  font-family: courier;
  font-size: small;
  padding-bottom: 10px;
}
"""

JS = """
<script type="text/javascript">
    function collapse(element){
        const frameId = element.getAttribute("data-frame-id");
        const frame = document.getElementById(frameId);

        if (frame.classList.contains("collapsed")){
            element.innerHTML = "&#8210;";
            frame.classList.remove("collapsed");
        } else {
            element.innerHTML = "+";
            frame.classList.add("collapsed");
        }
    }
</script>
"""

TEMPLATE = """
<html>
    <head>
        <style type='text/css'>
            {styles}
        </style>
        <title>Starlette Debugger</title>
    </head>
    <body>
        <h1>500 Server Error</h1>
        <h2>{error}</h2>
        <div class="traceback-container">
            <p class="traceback-title">Traceback</p>
            <div>{exc_html}</div>
        </div>
        {js}
    </body>
</html>
"""

FRAME_TEMPLATE = """
<div>
    <p class="frame-title">File <span class="frame-filename">{frame_filename}</span>,
    line <i>{frame_lineno}</i>,
    in <b>{frame_name}</b>
    <span class="collapse-btn" data-frame-id="{frame_filename}-{frame_lineno}" onclick="collapse(this)">{collapse_button}</span>
    </p>
    <div id="{frame_filename}-{frame_lineno}" class="source-code {collapsed}">{code_context}</div>
</div>
"""  # noqa: E501

LINE = """
<p><span class="frame-line">
<span class="lineno">{lineno}.</span> {line}</span></p>
"""

CENTER_LINE = """
<p class="center-line"><span class="frame-line center-line">
<span class="lineno">{lineno}.</span> {line}</span></p>
"""


class ServerErrorMiddleware:
    """
    Handles returning 500 responses when a server error occurs.

    If 'debug' is set, then traceback responses will be returned,
    otherwise the designated 'handler' will be called.

    This middleware class should generally be used to wrap *everything*
    else up, so that unhandled exceptions anywhere in the stack
    always result in an appropriate 500 response.
    """

    def __init__(
        self,
        app: ASGIApp,
        handler: typing.Callable[[Request, Exception], typing.Any] | None = None,
        debug: bool = False,
    ) -> None:
        self.app = app
        self.handler = handler
        self.debug = debug

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def _send(message: Message) -> None:
            nonlocal response_started, send

            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, _send)
        except Exception as exc:
            request = Request(scope)
            if self.debug:
                # In debug mode, return traceback responses.
                response = self.debug_response(request, exc)
            elif self.handler is None:
                # Use our default 500 error handler.
                response = self.error_response(request, exc)
            else:
                # Use an installed 500 error handler.
                if is_async_callable(self.handler):
                    response = await self.handler(request, exc)
                else:
                    response = await run_in_threadpool(self.handler, request, exc)

            if not response_started:
                await response(scope, receive, send)

            # We always continue to raise the exception.
            # This allows servers to log the error, or allows test clients
            # to optionally raise the error within the test case.
            raise exc

    def format_line(self, index: int, line: str, frame_lineno: int, frame_index: int) -> str:
        values = {
            # HTML escape - line could contain < or >
            "line": html.escape(line).replace(" ", "&nbsp"),
            "lineno": (frame_lineno - frame_index) + index,
        }

        if index != frame_index:
            return LINE.format(**values)
        return CENTER_LINE.format(**values)

    def generate_frame_html(self, frame: inspect.FrameInfo, is_collapsed: bool) -> str:
        code_context = "".join(
            self.format_line(
                index,
                line,
                frame.lineno,
                frame.index,  # type: ignore[arg-type]
            )
            for index, line in enumerate(frame.code_context or [])
        )

        values = {
            # HTML escape - filename could contain < or >, especially if it's a virtual
            # file e.g. <stdin> in the REPL
            "frame_filename": html.escape(frame.filename),
            "frame_lineno": frame.lineno,
            # HTML escape - if you try very hard it's possible to name a function with <
            # or >
            "frame_name": html.escape(frame.function),
            "code_context": code_context,
            "collapsed": "collapsed" if is_collapsed else "",
            "collapse_button": "+" if is_collapsed else "&#8210;",
        }
        return FRAME_TEMPLATE.format(**values)

    def generate_html(self, exc: Exception, limit: int = 7) -> str:
        traceback_obj = traceback.TracebackException.from_exception(exc, capture_locals=True)

        exc_html = ""
        is_collapsed = False
        exc_traceback = exc.__traceback__
        if exc_traceback is not None:
            frames = inspect.getinnerframes(exc_traceback, limit)
            for frame in reversed(frames):
                exc_html += self.generate_frame_html(frame, is_collapsed)
                is_collapsed = True

        if sys.version_info >= (3, 13):  # pragma: no cover
            exc_type_str = traceback_obj.exc_type_str
        else:  # pragma: no cover
            exc_type_str = traceback_obj.exc_type.__name__

        # escape error class and text
        error = f"{html.escape(exc_type_str)}: {html.escape(str(traceback_obj))}"

        return TEMPLATE.format(styles=STYLES, js=JS, error=error, exc_html=exc_html)

    def generate_plain_text(self, exc: Exception) -> str:
        return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

    def debug_response(self, request: Request, exc: Exception) -> Response:
        accept = request.headers.get("accept", "")

        if "text/html" in accept:
            content = self.generate_html(exc)
            return HTMLResponse(content, status_code=500)
        content = self.generate_plain_text(exc)
        return PlainTextResponse(content, status_code=500)

    def error_response(self, request: Request, exc: Exception) -> Response:
        return PlainTextResponse("Internal Server Error", status_code=500)
