#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
/*
gcc -O0 -g -o toto toto.c -lpthread
*/

extern __inline__ long long rdtsc(void) {
  long long a, d;
  __asm__ volatile ("rdtsc" : "=a" (a), "=d" (d));
  return (d<<32) | a;
}

void f1(){
    long long t = rdtsc();
    printf( "Hello! %lld\n", t );
}

void smthg( ){
    f1();
}

int main(){
    pthread_t t1, t2;

    pthread_create( &t1, NULL, (void*)&smthg, NULL );
    pthread_create( &t2, NULL, (void*)&smthg, NULL );

    pthread_join( t1, NULL );
    pthread_join( t2, NULL );

    return EXIT_SUCCESS;
}
