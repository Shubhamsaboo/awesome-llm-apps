try:
    from fastapi_cli.cli import main as cli_main

except ImportError:  # pragma: no cover
    cli_main = None  # type: ignore


def main() -> None:
    if not cli_main:  # type: ignore[truthy-function]
        message = 'To use the fastapi command, please install "fastapi[standard]":\n\n\tpip install "fastapi[standard]"\n'
        print(message)
        raise RuntimeError(message)  # noqa: B904
    cli_main()
