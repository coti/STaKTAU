CFLAGS = -g
LDFLAGS = -g
LIBS = -lpthread

EXEC = toto

all: $(EXEC)

toto: toto.o
	$(CC) $(LDFLAGS) -o $@ $^ $(LIBS)

clean:
	rm toto.o toto
