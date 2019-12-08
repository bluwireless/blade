# BLADE Tests
BLADE tests are written using the 'pytest' framework, utilising 'pytest-cov' for coverage metrics.

Tests are intended to target each submodule of BLADE independently, as well as testing cross-unit integrations.

## Running Tests With Coverage
To execute tests with coverage, issue the following command in a shell:
```bash
$> virtualenv venv
$> source venv/bin/activate
$> pip install pytest pytest-cov
$> pytest --cov=blade --cov-report=html
```