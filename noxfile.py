import nox

PYTHON_VERSIONS = ["3.10", "3.13"]

nox.options.default_venv_backend = "uv"


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    session.run_install(
        "uv",
        "sync",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.run(
        "pytest",
        "--cov=vss_tools",
        "--cov-report=term-missing",
        "--cov-fail-under=88",
        *session.posargs,
    )
