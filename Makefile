# easter-ugg-studio/Makefile


#
# Define 'make' and 'make help'
#


define __EPILOG__

make  # shows a few examples and exits zero

make help  # shows many help lines and exits zero
make bin  # updates your Shell Path ~/bin/ Folder
make pips  # installs/ updates Add-on's for Python from PyPi·Org
make smoke  # calls for Code Review from Black, Flake8, and MyPy Strict

endef


define __DOC__
usage: make TARGET

help download, run, and give back changes

positional arguments:
  TARGET  which work to do (one of help, bin, pips, smoke)

examples:
  make  # shows a few examples and exits zero
  make help  # shows many help lines and exits zero
  make bin  # updates your Shell Path ~/bin/ Folder
  make pips  # installs/ updates Python add-on's from PyPi·Org
  make smoke  # calls for Code Review from Black, Flake8, and MyPy Strict
endef


default:
	@$(info $(__EPILOG__))
	@true


help:
	@$(info $(__DOC__))
	@true


#
# Install stale copies into your Shell Path ~/bin/ Folder
#


bin:
	cp -p bin/@ bin/easter-ugg-studio.py ~/bin/.


#
# Installs/ replaces Python add-on's from PyPi·Org
#


.PHONY: bin pips requirements.txt

pips requirements.txt:
	: 'remake our ~/.pyvenvs/pips/ in less than 10s'
	:
	mkdir -p ~/.pyvenvs/  # or ~/.venvs/ or ~/.envs/
	:
	cd ~/.pyvenvs/ && rm -fr pips~
	cd ~/.pyvenvs/ && if [ -e pips ]; then mv -i pips pips~; fi
	:
	cd ~/.pyvenvs/ && python3 -m venv pips
	source ~/.pyvenvs/pips/bin/activate && python3 -m pip install --upgrade pip
	:
	source ~/.pyvenvs/pips/bin/activate && python3 -m pip install --upgrade black
	source ~/.pyvenvs/pips/bin/activate && python3 -m pip install --upgrade flake8
	source ~/.pyvenvs/pips/bin/activate && python3 -m pip install --upgrade flake8-import-order
	source ~/.pyvenvs/pips/bin/activate && python3 -m pip install --upgrade mypy
	:
	source ~/.pyvenvs/pips/bin/activate && python3 -m pip freeze >requirements.txt
	git diff --color-moved requirements.txt
	:


#
# Calls for Python Code Review from Black, Flake8, and MyPy Strict
#


push:  # as in do push now, without rerunning any tests
	git push


smoke: black flake8 mypy
	:


black:
	~/.pyvenvs/black/bin/black \
		--line-length=101 \
			bin/

# --line-length=101  # my 2024 Window Width, over PyPi·Org Black Default of 89 != 80 != 71


flake8:
	~/.pyvenvs/flake8/bin/flake8 \
		--max-line-length=999 --max-complexity 15 --ignore=E203,E704,W503 \
			bin/ 2>&1  \
			|grep -v '^/[^:]*flake8_import_order/styles.py:' \
			|grep -v '  from pkg_resources import iter_entry_points' \
			|cat -

# --max-line-length=999  # Black max line lengths over Flake8 max line lengths
# --max-complexity 10  # limit how much McCabe Cyclomatic Complexity we accept
# --ignore=E203  # Black '[ : ]' rules over E203 whitespace before ':'
# --ignore=E704  # Black of typing.Protocol rules over E704 multiple statements on one line (def)
# --ignore=W503  # 2017 Pep 8 and Black over W503 line break before bin op


mypy:
	~/.pyvenvs/mypy/bin/mypy \
		--strict \
			bin/


#
# Calls for Shell Code Review from ShellCheck
#


shellcheck:
	if ! which shellcheck; then \
		ls /usr/bin/shellcheck || :; \
		echo 'ok by you? or do you want:  date && time  sudo apt install shellcheck'; \
		exit 1; \
	fi
	:
	shellcheck bin/pwnme


# posted as:  https://github.com/pelavarre/easter-ugg-studio/blob/main/Makefile
# copied from:  git clone https://github.com/pelavarre/easter-ugg-studio.git
