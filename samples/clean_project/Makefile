# A clean, normal Makefile -- no suspicious hooks or obfuscation.
# Used as a baseline for scanner comparison against the build_system/ samples.

CC      = gcc
CFLAGS  = -Wall -Wextra -std=c99 -O2
TARGET  = hello
SRCS    = main.c
OBJS    = $(SRCS:.c=.o)

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(TARGET) $(OBJS)
