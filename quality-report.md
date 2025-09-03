# Code Quality Report
Generated on: Wed Sep  3 08:37:41 BST 2025

## Black Formatting Check
Checking Black formatting...
would reformat /Users/willhuntleyclarke/repos/interests/ticker-converter/tests/fixtures/test_helpers.py

Oh no! 💥 💔 💥
1 file would be reformatted, 67 files would be left unchanged.
❌ Black formatting issues found
Fix with: make black
make[1]: *** [black-check] Error 1
Black check failed

## Pylint Analysis
Running Pylint static analysis...
Using default Pylint configuration

--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)

✓ Pylint analysis completed

## MyPy Type Checking
Running MyPy type checking...
Using MyPy configuration: pyproject.toml
Success: no issues found in 27 source files
✓ MyPy type checking completed
if [ ! -f .env ]; then echo -e "Error: .env file not found. Run 'make setup' first."; echo -e "Tip: Copy .env.example to .env and customize the values"; exit 1; fi
echo -e "Checking Black formatting..."
/Applications/Xcode.app/Contents/Developer/usr/bin/make _check_black_deps
.venv/bin/python -c "import black" 2>/dev/null || \
	(echo -e "❌ Black not available. Run 'make install-dev' first." && exit 1)
.venv/bin/python -m black --check src tests --config=pyproject.toml 2>/dev/null || \
	.venv/bin/python -m black --check src tests && \
	echo -e "✓ Black formatting check passed" || \
	(echo -e "❌ Black formatting issues found" && \
	 echo -e "Fix with: make black" && exit 1)
if [ ! -f .env ]; then echo -e "Error: .env file not found. Run 'make setup' first."; echo -e "Tip: Copy .env.example to .env and customize the values"; exit 1; fi
echo -e "Running Pylint static analysis..."
/Applications/Xcode.app/Contents/Developer/usr/bin/make _check_pylint_deps
.venv/bin/python -c "import pylint" 2>/dev/null || \
	(echo -e "❌ Pylint not available. Run 'make install-dev' first." && exit 1)
if [ -f .pylintrc ]; then \
		echo -e "Using Pylint configuration: .pylintrc"; \
		.venv/bin/python -m pylint src --rcfile=.pylintrc; \
	else \
		echo -e "Using default Pylint configuration"; \
		.venv/bin/python -m pylint src; \
	fi && \
	echo -e "✓ Pylint analysis completed" || \
	(echo -e "❌ Pylint issues found" && exit 1)
if [ ! -f .env ]; then echo -e "Error: .env file not found. Run 'make setup' first."; echo -e "Tip: Copy .env.example to .env and customize the values"; exit 1; fi
echo -e "Running MyPy type checking..."
/Applications/Xcode.app/Contents/Developer/usr/bin/make _check_mypy_deps
.venv/bin/python -c "import mypy" 2>/dev/null || \
	(echo -e "❌ MyPy not available. Run 'make install-dev' first." && exit 1)
if [ -f pyproject.toml ]; then \
		echo -e "Using MyPy configuration: pyproject.toml"; \
		.venv/bin/python -m mypy src --config-file=pyproject.toml; \
	else \
		echo -e "Using default MyPy configuration"; \
		.venv/bin/python -m mypy src; \
	fi && \
	echo -e "✓ MyPy type checking completed" || \
	(echo -e "❌ MyPy type issues found" && exit 1)
if [ ! -f .env ]; then echo -e "Error: .env file not found. Run 'make setup' first."; echo -e "Tip: Copy .env.example to .env and customize the values"; exit 1; fi
echo -e "Checking Black formatting..."
/Applications/Xcode.app/Contents/Developer/usr/bin/make _check_black_deps
.venv/bin/python -c "import black" 2>/dev/null || \
	(echo -e "❌ Black not available. Run 'make install-dev' first." && exit 1)
.venv/bin/python -m black --check src tests --config=pyproject.toml 2>/dev/null || \
	.venv/bin/python -m black --check src tests && \
	echo -e "✓ Black formatting check passed" || \
	(echo -e "❌ Black formatting issues found" && \
	 echo -e "Fix with: make black" && exit 1)
if [ ! -f .env ]; then echo -e "Error: .env file not found. Run 'make setup' first."; echo -e "Tip: Copy .env.example to .env and customize the values"; exit 1; fi
echo -e "Running Pylint static analysis..."
/Applications/Xcode.app/Contents/Developer/usr/bin/make _check_pylint_deps
.venv/bin/python -c "import pylint" 2>/dev/null || \
	(echo -e "❌ Pylint not available. Run 'make install-dev' first." && exit 1)
if [ -f .pylintrc ]; then \
		echo -e "Using Pylint configuration: .pylintrc"; \
		.venv/bin/python -m pylint src --rcfile=.pylintrc; \
	else \
		echo -e "Using default Pylint configuration"; \
		.venv/bin/python -m pylint src; \
	fi && \
	echo -e "✓ Pylint analysis completed" || \
	(echo -e "❌ Pylint issues found" && exit 1)
if [ ! -f .env ]; then echo -e "Error: .env file not found. Run 'make setup' first."; echo -e "Tip: Copy .env.example to .env and customize the values"; exit 1; fi
echo -e "Running MyPy type checking..."
/Applications/Xcode.app/Contents/Developer/usr/bin/make _check_mypy_deps
.venv/bin/python -c "import mypy" 2>/dev/null || \
	(echo -e "❌ MyPy not available. Run 'make install-dev' first." && exit 1)
if [ -f pyproject.toml ]; then \
		echo -e "Using MyPy configuration: pyproject.toml"; \
		.venv/bin/python -m mypy src --config-file=pyproject.toml; \
	else \
		echo -e "Using default MyPy configuration"; \
		.venv/bin/python -m mypy src; \
	fi && \
	echo -e "✓ MyPy type checking completed" || \
	(echo -e "❌ MyPy type issues found" && exit 1)
if [ ! -f .env ]; then echo -e "Error: .env file not found. Run 'make setup' first."; echo -e "Tip: Copy .env.example to .env and customize the values"; exit 1; fi
echo -e "Checking Black formatting..."
/Applications/Xcode.app/Contents/Developer/usr/bin/make _check_black_deps
.venv/bin/python -c "import black" 2>/dev/null || \
	(echo -e "❌ Black not available. Run 'make install-dev' first." && exit 1)
.venv/bin/python -m black --check src tests --config=pyproject.toml 2>/dev/null || \
	.venv/bin/python -m black --check src tests && \
	echo -e "✓ Black formatting check passed" || \
	(echo -e "❌ Black formatting issues found" && \
	 echo -e "Fix with: make black" && exit 1)
if [ ! -f .env ]; then echo -e "Error: .env file not found. Run 'make setup' first."; echo -e "Tip: Copy .env.example to .env and customize the values"; exit 1; fi
echo -e "Running Pylint static analysis..."
/Applications/Xcode.app/Contents/Developer/usr/bin/make _check_pylint_deps
.venv/bin/python -c "import pylint" 2>/dev/null || \
	(echo -e "❌ Pylint not available. Run 'make install-dev' first." && exit 1)
if [ -f .pylintrc ]; then \
		echo -e "Using Pylint configuration: .pylintrc"; \
		.venv/bin/python -m pylint src --rcfile=.pylintrc; \
	else \
		echo -e "Using default Pylint configuration"; \
		.venv/bin/python -m pylint src; \
	fi && \
	echo -e "✓ Pylint analysis completed" || \
	(echo -e "❌ Pylint issues found" && exit 1)
if [ ! -f .env ]; then echo -e "Error: .env file not found. Run 'make setup' first."; echo -e "Tip: Copy .env.example to .env and customize the values"; exit 1; fi
echo -e "Running MyPy type checking..."
/Applications/Xcode.app/Contents/Developer/usr/bin/make _check_mypy_deps
.venv/bin/python -c "import mypy" 2>/dev/null || \
	(echo -e "❌ MyPy not available. Run 'make install-dev' first." && exit 1)
if [ -f pyproject.toml ]; then \
		echo -e "Using MyPy configuration: pyproject.toml"; \
		.venv/bin/python -m mypy src --config-file=pyproject.toml; \
	else \
		echo -e "Using default MyPy configuration"; \
		.venv/bin/python -m mypy src; \
	fi && \
	echo -e "✓ MyPy type checking completed" || \
	(echo -e "❌ MyPy type issues found" && exit 1)
if [ ! -f .env ]; then echo -e "Error: .env file not found. Run 'make setup' first."; echo -e "Tip: Copy .env.example to .env and customize the values"; exit 1; fi
echo -e "Checking Black formatting..."
/Applications/Xcode.app/Contents/Developer/usr/bin/make _check_black_deps
.venv/bin/python -c "import black" 2>/dev/null || \
	(echo -e "❌ Black not available. Run 'make install-dev' first." && exit 1)
.venv/bin/python -m black --check src tests --config=pyproject.toml 2>/dev/null || \
	.venv/bin/python -m black --check src tests && \
	echo -e "✓ Black formatting check passed" || \
	(echo -e "❌ Black formatting issues found" && \
	 echo -e "Fix with: make black" && exit 1)
if [ ! -f .env ]; then echo -e "Error: .env file not found. Run 'make setup' first."; echo -e "Tip: Copy .env.example to .env and customize the values"; exit 1; fi
echo -e "Running Pylint static analysis..."
/Applications/Xcode.app/Contents/Developer/usr/bin/make _check_pylint_deps
.venv/bin/python -c "import pylint" 2>/dev/null || \
	(echo -e "❌ Pylint not available. Run 'make install-dev' first." && exit 1)
if [ -f .pylintrc ]; then \
		echo -e "Using Pylint configuration: .pylintrc"; \
		.venv/bin/python -m pylint src --rcfile=.pylintrc; \
	else \
		echo -e "Using default Pylint configuration"; \
		.venv/bin/python -m pylint src; \
	fi && \
	echo -e "✓ Pylint analysis completed" || \
	(echo -e "❌ Pylint issues found" && exit 1)
if [ ! -f .env ]; then echo -e "Error: .env file not found. Run 'make setup' first."; echo -e "Tip: Copy .env.example to .env and customize the values"; exit 1; fi
echo -e "Running MyPy type checking..."
/Applications/Xcode.app/Contents/Developer/usr/bin/make _check_mypy_deps
.venv/bin/python -c "import mypy" 2>/dev/null || \
	(echo -e "❌ MyPy not available. Run 'make install-dev' first." && exit 1)
if [ -f pyproject.toml ]; then \
		echo -e "Using MyPy configuration: pyproject.toml"; \
		.venv/bin/python -m mypy src --config-file=pyproject.toml; \
	else \
		echo -e "Using default MyPy configuration"; \
		.venv/bin/python -m mypy src; \
	fi && \
	echo -e "✓ MyPy type checking completed" || \
	(echo -e "❌ MyPy type issues found" && exit 1)
if [ ! -f .env ]; then echo -e "Error: .env file not found. Run 'make setup' first."; echo -e "Tip: Copy .env.example to .env and customize the values"; exit 1; fi
echo -e "Checking Black formatting..."
/Applications/Xcode.app/Contents/Developer/usr/bin/make _check_black_deps
.venv/bin/python -c "import black" 2>/dev/null || \
	(echo -e "❌ Black not available. Run 'make install-dev' first." && exit 1)
.venv/bin/python -m black --check src tests --config=pyproject.toml 2>/dev/null || \
	.venv/bin/python -m black --check src tests && \
	echo -e "✓ Black formatting check passed" || \
	(echo -e "❌ Black formatting issues found" && \
	 echo -e "Fix with: make black" && exit 1)
if [ ! -f .env ]; then echo -e "Error: .env file not found. Run 'make setup' first."; echo -e "Tip: Copy .env.example to .env and customize the values"; exit 1; fi
echo -e "Running Pylint static analysis..."
/Applications/Xcode.app/Contents/Developer/usr/bin/make _check_pylint_deps
.venv/bin/python -c "import pylint" 2>/dev/null || \
	(echo -e "❌ Pylint not available. Run 'make install-dev' first." && exit 1)
if [ -f .pylintrc ]; then \
		echo -e "Using Pylint configuration: .pylintrc"; \
		.venv/bin/python -m pylint src --rcfile=.pylintrc; \
	else \
		echo -e "Using default Pylint configuration"; \
		.venv/bin/python -m pylint src; \
	fi && \
	echo -e "✓ Pylint analysis completed" || \
	(echo -e "❌ Pylint issues found" && exit 1)
if [ ! -f .env ]; then echo -e "Error: .env file not found. Run 'make setup' first."; echo -e "Tip: Copy .env.example to .env and customize the values"; exit 1; fi
echo -e "Running MyPy type checking..."
/Applications/Xcode.app/Contents/Developer/usr/bin/make _check_mypy_deps
.venv/bin/python -c "import mypy" 2>/dev/null || \
	(echo -e "❌ MyPy not available. Run 'make install-dev' first." && exit 1)
if [ -f pyproject.toml ]; then \
		echo -e "Using MyPy configuration: pyproject.toml"; \
		.venv/bin/python -m mypy src --config-file=pyproject.toml; \
	else \
		echo -e "Using default MyPy configuration"; \
		.venv/bin/python -m mypy src; \
	fi && \
	echo -e "✓ MyPy type checking completed" || \
	(echo -e "❌ MyPy type issues found" && exit 1)
