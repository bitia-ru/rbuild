CROSS_COMPILE ?= 

# toolchain definitions
CC = $(CROSS_COMPILE)gcc
CXX = $(CROSS_COMPILE)g++
AS = $(CROSS_COMPILE)gcc
AR = $(CROSS_COMPILE)ar
LD = $(CROSS_COMPILE)gcc
RANLIB = $(CROSS_COMPILE)ranlib
MAKE = make
MV = @mv
MKDIR = mkdir
TOUCH = touch
INST = install


# toolchain mediators
V ?= f

V_CC = $(V_CC_$(V))
V_AS = $(V_AS_$(V))
V_AR = $(V_AR_$(V))
V_INST = $(V_INST_$(V))
V_at = $(V_at_$(V))

V_CC_f = @echo " CC    "$@;
V_CC_s = @
V_CC_v = 

V_CXX_f = @echo " CXX    "$@;
V_CXX_s = @
V_CXX_v = 

V_LD_f = @echo " LD    "$@;
V_LD_s = @
V_LD_v = 

V_AS_f = @echo " AS    "$@;
V_AS_s = @

V_AR_f = @echo " AR    "$@;
V_AR_s = @

V_INST_f = 
V_INST_v = 
V_INST_s = @

V_at_v =
V_at_s = @


MFPATH = $(firstword $(MAKEFILE_LIST))
MFDIR = $(dir $(MFPATH))
SRCDIR ?= .
DESTDIR ?= 

DEFILES_all = $(DEFILES_rbapi)
OBJECTS_all = $(OBJECTS_rbapi)

# common targets
CFLAGS ?= -g -O2
CFLAGS_INT = 

CXXFLAGS ?= -g -O2
CXXFLAGS_INT = 

LDFLAGS ?= 
LDFLAGS_INT = 

INCLUDES ?=
INCLUDES_INT = -I"$(SRCDIR)" 

LIBRARIES ?=
LIBRARIES_INT = 


# target-specific environments

## environment for target 'rbapi'
CSOURCES_rbapi = main.c json.c
CXXSOURCES_rbapi = 
OBJECTS_rbapi = rbapi/main.o rbapi/json.o 
DEFILES_rbapi = $(patsubst %.o,./$(DEPDIR)/%.Po,$(OBJECTS_rbapi))
CFLAGS_rbapi = -std=gnu99
CXXFLAGS_rbapi = 
LDFLAGS_rbapi = 
INCLUDES_rbapi = 
LIBRARIES_rbapi = 

DEPDIR = .deps

.PHONY: all all-m clean install

all:
	$(MAKE) -f $(MFPATH) all-m

all-m: output/rbapi





output/rbapi: $(OBJECTS_rbapi)
	@test -d $(dir $@) || $(MKDIR) -pv $(dir $@)
	$(V_LD)$(LD) $(LDFLAGS_INT) $(LDFLAGS_rbapi) $(LDFLAGS) -o $@ $^ $(LIBRARIES_rbapi)

rbapi/main.o: main.c
	@test -d $(dir $@) || $(MKDIR) -pv $(dir $@)
	$(V_CC)$(CC) $(INCLUDES_INT) $(INCLUDES_rbapi) $(INCLUDES) $(CFLAGS_INT) $(CFLAGS_rbapi) $(CFLAGS) -MT $@ -MD -MP -MF $(DEPDIR)/$*.Tpo -c -o $@ $<
	$(V_at)$(MV) $(DEPDIR)/$*.Tpo $(DEPDIR)/$*.Po

rbapi/json.o: json.c
	@test -d $(dir $@) || $(MKDIR) -pv $(dir $@)
	$(V_CC)$(CC) $(INCLUDES_INT) $(INCLUDES_rbapi) $(INCLUDES) $(CFLAGS_INT) $(CFLAGS_rbapi) $(CFLAGS) -MT $@ -MD -MP -MF $(DEPDIR)/$*.Tpo -c -o $@ $<
	$(V_at)$(MV) $(DEPDIR)/$*.Tpo $(DEPDIR)/$*.Po




clean:
	$(V_RM)$(RM) $(OBJECTS_all)

distclean: clean
	$(V_RM)$(RM) -r $(DEPDIR)

-include $(DEFILES_all)

%.Po:
	@test -d $(dir $@) || $(MKDIR) -pv $(dir $@)
	@$(TOUCH) $@

