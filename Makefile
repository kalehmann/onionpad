FIRMWARE_DIRECTORY = _firmware
CC = mpy-cross
CIRCUP = circup
CIRCUP_OPTIONS = --path $(FIRMWARE_DIRECTORY)
ONIONPAD_LIBRARY = $(FIRMWARE_DIRECTORY)/lib/onionpad
ONIONPAD_PY_FILES = \
    $(shell find onionpad -type f -name '*.py' -printf 'onionpad/%P\n')
ONIONPAD_MPY_FILES = \
    $(patsubst onionpad/%.py,$(ONIONPAD_LIBRARY)/%.mpy,$(ONIONPAD_PY_FILES))
USER_FILES = $(patsubst user%, $(FIRMWARE_DIRECTORY)/user%, $(wildcard user_*))
FIRMWARE_FILES = \
    $(ONIONPAD_LIBRARY) \
    $(ONIONPAD_MPY_FILES) \
    $(FIRMWARE_DIRECTORY)/boot.py \
    $(FIRMWARE_DIRECTORY)/code.py \
    $(USER_FILES)

all: $(FIRMWARE_FILES)

$(FIRMWARE_DIRECTORY)/user_%: user_%
	cp -r $< $@

$(ONIONPAD_LIBRARY):
	mkdir -p $(ONIONPAD_LIBRARY)
	cp boot_out.txt $(ONIONPAD_LIBRARY)
	cp -r onionpad/icons $(ONIONPAD_LIBRARY)/

$(ONIONPAD_LIBRARY)/%.mpy: onionpad/%.py
	$(CC) -o $@ $<

$(FIRMWARE_DIRECTORY)/boot.py: boot.py
	cp $< $@

$(FIRMWARE_DIRECTORY)/code.py: code.py $(wildcard user.py)
	if [[ -f "user.py" ]]; then \
		cp user.py $@; \
	else \
		cp code.py $@; \
	fi

$(FIRMWARE_DIRECTORY)/%.txt: %.txt
	cp $< $@

fetch-libraries: $(FIRMWARE_DIRECTORY)/boot_out.txt
	$(CIRCUP) $(CIRCUP_OPTIONS) install --requirement requirements.txt

clean:
	rm -rf $(FIRMWARE_DIRECTORY)
	$(MAKE) -C docs clean

html:
	$(MAKE) -C docs html

dirhtml:
	$(MAKE) -C docs dirhtml

singlehtml:
	$(MAKE) -C docs singlehtml

.PHONY: clean fetch-libraries html dirhtml singlehtml
