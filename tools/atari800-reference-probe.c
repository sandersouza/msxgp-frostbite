#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "libatari800.h"
extern int Colours_table[256];
extern int MEMORY_ram_size;
extern int Atari800_machine_type;

int main(int argc, char **argv) {
    unsigned char cartridge[8192]; const char *cartfile=NULL;
    for(int i=1;i+1<argc;i++) if(!strcmp(argv[i],"-cart"))cartfile=argv[i+1];
    if(!cartfile)return 4;
    FILE *cart=fopen(cartfile,"rb");if(!cart)return 4;
    if(fseek(cart,16,SEEK_SET) || fread(cartridge,1,8192,cart)!=8192)return 4;
    fclose(cart);
    if (!libatari800_init(argc-1, argv+1)) return 2;
    printf("machine=%d ram_kib=%d fps=%.9f\n",Atari800_machine_type,MEMORY_ram_size,libatari800_get_fps());
    FILE *ram=fopen("ram-frames.bin","wb");
    FILE *screen=fopen("screen-frames.bin","wb");
    FILE *timing=fopen("frames.tsv","w");
    input_template_t input;
    int startup_dlist_errors=0;
    for (int i=0;i<1200;i++) {
        libatari800_clear_input_array(&input);
        input.start=(i==180);
        if (i>=240) {input.joy0=((i/60)&1)?1:2;input.trig0=1;}
        libatari800_error_code=0; /* error latch, not emulated state */
        int success=libatari800_next_frame(&input);
        if (!success && !(i<=60 && libatari800_error_code==LIBATARI800_DLIST_ERROR)) {
            fprintf(stderr,"frame %d: %s\n",i,libatari800_error_message());return 3;
        }
        if(!success)startup_dlist_errors++;
        unsigned char *mem=libatari800_get_main_memory_ptr();
        if(memcmp(mem+0xa000,cartridge,8192)){fprintf(stderr,"cartridge memory differs at frame%d\n",i);return 5;}
        fwrite(mem,1,8192,ram);
        if (i==179 || i==239 || i==300 || i==600 || i==1199) {
            fwrite(libatari800_get_screen_ptr(),1,384*240,screen);
            char name[32];snprintf(name,sizeof(name),"frame-%04d.ppm",i);FILE *f=fopen(name,"wb");
            fprintf(f,"P6\n384 240\n255\n");
            unsigned char *pixels=libatari800_get_screen_ptr();
            for(int j=0;j<384*240;j++){int rgb=Colours_table[pixels[j]];fputc(rgb>>16,f);fputc(rgb>>8,f);fputc(rgb,f);}fclose(f);
        }
        fprintf(timing,"%d %.9f %u %u %u %u %u\n",i,libatari800_get_fps(),mem[0x81],mem[0xc6],mem[0xc5],mem[0xe4],mem[0xe6]);
    }
    fclose(ram);fclose(screen);fclose(timing);
    printf("complete_frames=1200 cartridge_memory_matches=1200 startup_dlist_errors=%d\n",startup_dlist_errors);
    return 0;
}
