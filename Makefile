SHELL = /bin/bash

IMAGE = xxxxx/dashboard

BUILDER = index.xxxxx.com/tutum/builder

HAS_VERSION := false

GIT_HASH := $(shell git rev-parse --short=8 HEAD)

# If this isn't a git repo or the repo has no tags, git describe will return non-zero
ifeq ($(shell git describe > /dev/null 2>&1 ; echo $$?), 0)
	HAS_VERSION := true
	VERSION := $(shell git describe --tags --long --dirty --always | \
		sed 's/v\([0-9]*\)\.\([0-9]*\)\.\([0-9]*\)-\?.*-\([0-9]*\)-\(.*\)/\1 \2 \3 \4 \5/g')
	VERSION_MAJOR := $(word 1, $(VERSION))
	VERSION_MINOR := $(word 2, $(VERSION))
	VERSION_PATCH := $(word 3, $(VERSION))
	VERSION_REVISION := $(word 4, $(VERSION))
	VERSION_HASH := $(word 5, $(VERSION))
	VERSION_STRING := \
		$(VERSION_MAJOR).$(VERSION_MINOR).$(VERSION_PATCH).$(VERSION_REVISION)-$(VERSION_HASH)
endif

# http://stackoverflow.com/questions/5584872/complex-conditions-check-in-makefile?answertab=active#tab-top
ifndef_any_of = $(filter undefined,$(foreach v,$(1),$(origin $(v))))

all: build

.PHONY: version
version:
ifeq ($(HAS_VERSION), false)
	@echo "Use 'git tag -a vYYYY.MM.DD -m msg' create a tag first"
	exit 1
endif
	@echo "Build version is: v$(VERSION_STRING)"


.PHONY: login
login:
ifeq ($(call ifndef_any_of, EMAIL, USERNAME, PASSWORD),)
	@echo "Login index.xxxxx.com"
	docker login -e $(EMAIL) -u $(USERNAME) -p $(PASSWORD) index.xxxxx.com
	@echo ""
else
	@echo "Login index.xxxxx.com skipping"
	@echo ""
endif


.PHONY: build
build: login
	@echo "Beginning build $(GIT_HASH)"
	docker run --rm -it --privileged \
		-e IMAGE_NAME="index.xxxxx.com/$(IMAGE):$(GIT_HASH)" \
		-v $$HOME/.docker:/.docker:ro \
		-v $(shell pwd):/app \
		-v /var/run/docker.sock:/var/run/docker.sock:rw \
		$(BUILDER)

.PHONY: release
release: version login
	@echo "Beginning build v$(VERSION_STRING)"
	docker run --rm -it --privileged \
		-e IMAGE_NAME="index.xxxxx.com/$(IMAGE):$(VERSION_STRING)" \
		-v $$HOME/.docker:/.docker:ro \
		-v $(shell pwd):/app \
		-v /var/run/docker.sock:/var/run/docker.sock:rw \
		$(BUILDER)

