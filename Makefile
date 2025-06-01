# Makefile for JobOps: clean, install, deploy
.PHONY: clean install deploy

ifeq ($(OS),Windows_NT)
SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -ExecutionPolicy Bypass -Command
endif

clean:
ifeq ($(OS),Windows_NT)
	if (Test-Path '.venv') { Remove-Item -Recurse -Force .venv }
	if (Test-Path 'dist') { Remove-Item -Recurse -Force dist }
else
	@if [ -d .venv ]; then rm -rf .venv; fi
	@if [ -d dist ]; then rm -rf dist; fi
endif

install: clean
ifeq ($(OS),Windows_NT)
	if (!(Test-Path '.venv/Scripts/Activate')) { uv venv --python 3.10 .venv; & .venv/Scripts/python.exe -m ensurepip --upgrade; & .venv/Scripts/python.exe -m pip install --upgrade pip; & .venv/Scripts/python.exe -m pip install uv; }
	uv pip install --prerelease=allow -r pyproject.toml
else
	@if [ ! -d .venv ]; then uv venv --python 3.10 .venv; fi
	UNAME_S := $(shell uname -s)
	ifeq ($(UNAME_S),Linux)
		sudo apt-get update
		sudo apt-get install -y build-essential ffmpeg
	else ifeq ($(UNAME_S),Darwin)
		@if ! command -v brew > /dev/null; then echo "Homebrew not found. Please install Homebrew first: https://brew.sh/" && exit 1; fi
		brew install ffmpeg
	else
		@echo "Unsupported OS: $(UNAME_S)" && exit 1
	endif
	uv pip install --prerelease=allow -r pyproject.toml
endif

deploy:
ifeq ($(OS),Windows_NT)
	pyinstaller --onefile --windowed run_jobops.py --name jobops.exe --collect-all plyer --collect-all requests --collect-all beautifulsoup4 --collect-all numpy --collect-all psutil --collect-all pydantic --collect-all rich --collect-all pdfplumber --collect-all fpdf --collect-all openai --collect-all playwright --collect-all fake_useragent --collect-all fake_http_header --collect-all lxml --collect-all PyYAML --collect-all dotenv --log-level=INFO
else
	UNAME_S := $(shell uname -s)
	ifeq ($(UNAME_S),Linux)
		pyinstaller --onefile --windowed src/jobops/__main__.py --name jobops \
			--collect-all plyer \
			--collect-all requests \
			--collect-all beautifulsoup4 \
			--collect-all numpy \
			--collect-all psutil \
			--collect-all pydantic \
			--collect-all rich \
			--collect-all pdfplumber \
			--collect-all fpdf \
			--collect-all openai \
			--collect-all playwright \
			--collect-all fake_useragent \
			--collect-all fake_http_header \
			--collect-all lxml \
			--collect-all PyYAML \
			--collect-all dotenv \
			--log-level=INFO
	else ifeq ($(UNAME_S),Darwin)
		pyinstaller --onefile --windowed src/jobops/__main__.py --name jobops \
			--collect-all plyer \
			--collect-all requests \
			--collect-all beautifulsoup4 \
			--collect-all numpy \
			--collect-all psutil \
			--collect-all pydantic \
			--collect-all rich \
			--collect-all pdfplumber \
			--collect-all fpdf \
			--collect-all openai \
			--collect-all playwright \
			--collect-all fake_useragent \
			--collect-all fake_http_header \
			--collect-all lxml \
			--collect-all PyYAML \
			--collect-all dotenv \
			--log-level=INFO
	else
		@echo "Unsupported OS: $(UNAME_S)" && exit 1
	endif
endif 