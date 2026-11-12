#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include "miniz.h"
#include <dirent.h>
#include <libndls.h>
#include <ctype.h>

#define MAXPATH 512
static int exists(const char *p){struct stat st; return stat(p,&st)==0;}
static int safe(const char *p){
 if(!p[0]||p[0]=='/'||p[0]=='\\'||strchr(p,':'))return 0;
 const char *s=p; while(*s){const char *e=strchr(s,'/');size_t n=e?(size_t)(e-s):strlen(s);
 if(!n||(n==1&&s[0]=='.')||(n==2&&s[0]=='.'&&s[1]=='.'))return 0;
 for(size_t i=0;i<n;i++)if((unsigned char)s[i]<32||s[i]=='\\')return 0;
 if(!e)break;s=e+1;
 }return 1;
}
static int dirs(const char *path){
 char b[MAXPATH];size_t n=strlen(path);if(!n||n>=sizeof(b))return 0;
 strcpy(b,path);for(size_t i=1;i<=n;i++){if(b[i]=='/'||b[i]==0){char c=b[i];b[i]=0;if(!exists(b)&&mkdir(b,0777)!=0)return 0;b[i]=c;}}return 1;
}
static int parent(const char *p){char b[MAXPATH];if(strlen(p)>=sizeof(b))return 0;strcpy(b,p);char *s=strrchr(b,'/');if(!s)return 1;*s=0;return !*b||dirs(b);}
static int extract(const char *file,const char *dest){
 mz_zip_archive z={0};int ok=1;
 if(!mz_zip_reader_init_file(&z,file,0)){puts("Cannot open archive");return 0;}
 if(!dirs(dest)){mz_zip_reader_end(&z);return 0;}
 for(mz_uint i=0;i<mz_zip_reader_get_num_files(&z);i++){
 mz_zip_archive_file_stat st;char path[MAXPATH];
 if(!mz_zip_reader_file_stat(&z,i,&st)||!safe(st.m_filename)||(st.m_bit_flag&1)){puts("Unsafe/encrypted entry");ok=0;break;}
 if(snprintf(path,sizeof(path),"%s/%s",dest,st.m_filename)>=(int)sizeof(path)){ok=0;break;}
 if(mz_zip_reader_is_file_a_directory(&z,i)){if(!dirs(path)){ok=0;break;}continue;}
 if(exists(path)||!parent(path)){puts("Existing file / invalid directory");ok=0;break;}
 if(!mz_zip_reader_extract_to_file(&z,i,path,0)){puts("Extraction failed");remove(path);ok=0;break;}
 printf("Extracted: %s\n",st.m_filename);
 }
 mz_zip_reader_end(&z);return ok;
}
static int add(mz_zip_archive *z,const char *path,const char *name){
 struct stat st;if(stat(path,&st))return 0;
 if(S_ISDIR(st.st_mode)){puts("Folder packing comes in run 002");return 0;}
 return mz_zip_writer_add_file(z,name,path,NULL,0,MZ_BEST_SPEED);
}
static int create(const char *file,const char *source){
 mz_zip_archive z={0};char name[MAXPATH];const char *base=strrchr(source,'/');
 base=base?base+1:source;
 if(!safe(base)||exists(file)||strlen(base)>=sizeof(name))return 0;
 strcpy(name,base);
 if(!mz_zip_writer_init_file(&z,file,0))return 0;
 int ok=add(&z,source,name)&&mz_zip_writer_finalize_archive(&z);
 mz_zip_writer_end(&z);if(!ok)remove(file);return ok;
}


/* UltraZIP 003: nCXplorer-inspired pixel UI. No terminal output is used. */
#define MAXENT 128
#define W 320
#define H 240
#define BG 0x10A3
#define PANEL 0x18E4
#define BAR 0x08A2
#define CYAN 0x05DF
#define TEXT 0xFFFF
#define MUTED 0xAD55
#define DARK 0x0000
#define GOLD 0xFD20
#define GREEN 0x47E9
#define RED 0xF945
typedef struct { char name[256]; int directory; unsigned long size; } entry_t;
static entry_t entries[MAXENT];
static int count=0,selected=0,view=0;
static char cwd[MAXPATH]="/documents";
static char feedback[112]="ENTER: menu  LEFT: parent";
static char chosen[MAXPATH]="";
static int menu=0,menusel=0,listing=0;
static char listings[80][57];
static int nlisting=0,listscroll=0;
static unsigned short pixels[W*H];

typedef struct {char ch; unsigned char row[7];} glyph_t;
static const glyph_t font[] = {
{'A',{14,17,17,31,17,17,17}}, {'B',{30,17,17,30,17,17,30}},
{'C',{14,17,16,16,16,17,14}}, {'D',{30,17,17,17,17,17,30}},
{'E',{31,16,16,30,16,16,31}}, {'F',{31,16,16,30,16,16,16}},
{'G',{15,16,16,23,17,17,15}}, {'H',{17,17,17,31,17,17,17}},
{'I',{31,4,4,4,4,4,31}}, {'J',{1,1,1,1,17,17,14}},
{'K',{17,18,20,24,20,18,17}}, {'L',{16,16,16,16,16,16,31}},
{'M',{17,27,21,21,17,17,17}}, {'N',{17,25,21,19,17,17,17}},
{'O',{14,17,17,17,17,17,14}}, {'P',{30,17,17,30,16,16,16}},
{'Q',{14,17,17,17,21,18,13}}, {'R',{30,17,17,30,20,18,17}},
{'S',{15,16,16,14,1,1,30}}, {'T',{31,4,4,4,4,4,4}},
{'U',{17,17,17,17,17,17,14}}, {'V',{17,17,17,17,17,10,4}},
{'W',{17,17,17,21,21,21,10}}, {'X',{17,17,10,4,10,17,17}},
{'Y',{17,17,10,4,4,4,4}}, {'Z',{31,1,2,4,8,16,31}},
{'0',{14,17,19,21,25,17,14}}, {'1',{4,12,4,4,4,4,14}},
{'2',{14,17,1,2,4,8,31}}, {'3',{30,1,1,14,1,1,30}},
{'4',{2,6,10,18,31,2,2}}, {'5',{31,16,16,30,1,1,30}},
{'6',{14,16,16,30,17,17,14}}, {'7',{31,1,2,4,8,8,8}},
{'8',{14,17,17,14,17,17,14}}, {'9',{14,17,17,15,1,1,14}},
{'.',{0,0,0,0,0,12,12}}, {'-',{0,0,0,31,0,0,0}},
{'_',{0,0,0,0,0,0,31}}, {'/',{1,1,2,4,8,16,16}},
{':',{0,12,12,0,12,12,0}}, {'>',{16,8,4,2,4,8,16}},
{'<',{1,2,4,8,4,2,1}}, {'[',{14,8,8,8,8,8,14}},
{']',{14,2,2,2,2,2,14}}, {'+', {0,4,4,31,4,4,0}},
{'=',{0,31,0,31,0,0,0}}, {' ',{0,0,0,0,0,0,0}},
{'!',{4,4,4,4,4,0,4}}, {'?',{14,17,1,2,4,0,4}},
{'(',{2,4,8,8,8,4,2}}, {')',{8,4,2,2,2,4,8}},
{'#',{10,31,10,10,31,10,0}}, {'*',{0,10,4,31,4,10,0}},
{'%',{25,26,2,4,8,11,19}}, {',',{0,0,0,0,12,12,8}},
};
static void box(int x,int y,int w,int h,unsigned short color){
 if(x<0){w+=x;x=0;}if(y<0){h+=y;y=0;}
 if(x+w>W)w=W-x;if(y+h>H)h=H-y;
 if(w<=0||h<=0)return;
 for(int r=y;r<y+h;r++)for(int c=x;c<x+w;c++)pixels[r*W+c]=color;
}
static void letter(int x,int y,char ch,unsigned short color,int scale){
 unsigned char *dummy=0;(void)dummy;
 const unsigned char *r=NULL;
 ch=(char)toupper((unsigned char)ch);
 for(size_t i=0;i<sizeof(font)/sizeof(font[0]);i++)if(font[i].ch==ch){r=font[i].row;break;}
 if(!r)r=font[sizeof(font)/sizeof(font[0])-1].row;
 for(int j=0;j<7;j++)for(int k=0;k<5;k++)
  if(r[j]&(16>>k))box(x+k*scale,y+j*scale,scale,scale,color);
}
static void label(int x,int y,const char *s,unsigned short col,int scale,int limit){
 if(!s)return;
 int n=0;
 for(;*s&&n<limit;s++,n++)letter(x+n*6*scale,y,*s,col,scale);
}
static void render(void){lcd_blit(pixels,SCR_320x240_565);}
static int zipname(const char *p){
 size_t n=strlen(p);return (n>=4&&!strcmp(p+n-4,".zip"))||(n>=8&&!strcmp(p+n-8,".zip.tns"));
}
static int join(char *out,size_t sz,const char *dir,const char *name){
 return snprintf(out,sz,"%s%s%s",dir,!strcmp(dir,"/")?"":"/",name)<(int)sz;
}
static void status(const char *message){snprintf(feedback,sizeof(feedback),"%s",message);}
static void refresh(void){
 DIR *d=opendir(cwd);struct dirent *e;count=selected=view=0;
 if(!d){strcpy(cwd,"/");d=opendir(cwd);}
 if(!d){status("Folder unavailable");return;}
 while((e=readdir(d))&&count<MAXENT){
  char full[MAXPATH];struct stat st;
  if(!strcmp(e->d_name,".")||!strcmp(e->d_name,".."))continue;
  if(strlen(e->d_name)>=sizeof(entries[0].name))continue;
  if(!join(full,sizeof(full),cwd,e->d_name)||stat(full,&st))continue;
  strcpy(entries[count].name,e->d_name);
  entries[count].directory=S_ISDIR(st.st_mode);
  entries[count].size=(unsigned long)st.st_size;
  count++;
 }
 closedir(d);
 for(int i=0;i<count;i++)for(int j=i+1;j<count;j++)
   if(entries[j].directory>entries[i].directory||
     (entries[i].directory==entries[j].directory&&strcmp(entries[i].name,entries[j].name)>0)){
    entry_t t=entries[i];entries[i]=entries[j];entries[j]=t;
   }
}
static void updir(void){
 if(!strcmp(cwd,"/"))return;
 char *s=strrchr(cwd,'/');if(!s||s==cwd)strcpy(cwd,"/");else *s=0;
 refresh();
}
static void paint(void){
 box(0,0,W,H,BG);box(0,0,W,31,BAR);box(0,29,W,2,CYAN);
 label(11,7,"ULTRAZIP 003",TEXT,2,18);
 label(214,12,"ZIP MANAGER",CYAN,1,17);
 box(0,31,W,25,PANEL);label(8,40,cwd,MUTED,1,51);
 box(0,57,W,18,0x2126);
 label(8,63,"NAME",TEXT,1,24);label(273,63,"SIZE",TEXT,1,8);
 int visible=9;if(selected<view)view=selected;if(selected>=view+visible)view=selected-visible+1;
 for(int n=0;n<visible;n++){
  int i=view+n,y=78+n*15;if(i>=count)break;
  if(i==selected)box(4,y-2,312,15,CYAN);
  unsigned short color=(i==selected)?DARK:TEXT;
  box(9,y+1,10,10,entries[i].directory?GOLD:(zipname(entries[i].name)?GREEN:0x8410));
  if(entries[i].directory)label(11,y+3,"D",DARK,1,1);
  else if(zipname(entries[i].name))label(11,y+3,"Z",DARK,1,1);
  label(27,y,entries[i].name,color,1,39);
  if(!entries[i].directory){
    char sz[20];snprintf(sz,sizeof(sz),"%luK",(entries[i].size+1023)/1024);
    label(270,y,sz,color,1,7);
  }
 }
 if(!count)label(18,100,"NO FILES IN THIS FOLDER",TEXT,1,45);
 box(0,216,W,24,BAR);label(5,221,"ENTER MENU  LEFT BACK  ESC EXIT",TEXT,1,51);
 box(0,204,W,12,PANEL);label(5,206,feedback,CYAN,1,51);
 if(menu){
  box(52,58,216,133,0x0000);box(55,61,210,127,PANEL);
  label(67,69,"FILE ACTIONS",CYAN,2,17);
  const char *options[4]={"OPEN / BROWSE","EXTRACT ZIP","CREATE ZIP","CANCEL"};
  for(int i=0;i<4;i++){
   if(menusel==i)box(62,96+i*20,196,18,CYAN);
   label(72,101+i*20,options[i],menusel==i?DARK:TEXT,1,28);
  }
 }
 if(listing){
  box(18,36,284,176,DARK);box(22,40,276,168,PANEL);
  label(30,48,"ZIP CONTENTS",CYAN,2,20);
  for(int i=0;i<12&&i+listscroll<nlisting;i++)
   label(31,76+i*10,listings[i+listscroll],TEXT,1,42);
  label(31,194,"UP/DOWN SCROLL ESC CLOSE",CYAN,1,40);
 }
 render();
}
static void show_contents(const char *archive){
 mz_zip_archive z={0};nlisting=listscroll=0;
 if(!mz_zip_reader_init_file(&z,archive,0)){status("Cannot open ZIP archive");return;}
 int n=(int)mz_zip_reader_get_num_files(&z);
 for(int i=0;i<n&&i<80;i++){
  mz_zip_archive_file_stat st;
  if(mz_zip_reader_file_stat(&z,i,&st)){
   snprintf(listings[nlisting],sizeof(listings[0]),"%.55s",st.m_filename);nlisting++;
  }
 }
 mz_zip_reader_end(&z);listing=1;
}
static void operate(int action){
 char full[MAXPATH],out[MAXPATH];
 if(!count)return;
 if(!join(full,sizeof(full),cwd,entries[selected].name)){status("Path is too long");return;}
 if(action==0){
  if(entries[selected].directory){
   strcpy(cwd,full);refresh();
  }else if(zipname(entries[selected].name))show_contents(full);
  else status("Choose CREATE ZIP for this file");
  return;
 }
 if(entries[selected].directory){status("Folder ZIP comes in next release");return;}
 if(action==1){
  if(!zipname(entries[selected].name)){status("Select a ZIP archive");return;}
  char base[MAXPATH];strcpy(base,full);size_t len=strlen(base);
  if(len>=8&&!strcmp(base+len-8,".zip.tns"))base[len-8]=0;
  else if(len>=4&&!strcmp(base+len-4,".zip"))base[len-4]=0;
  if(snprintf(out,sizeof(out),"%s_unzipped",base)>=(int)sizeof(out)){status("Output path is too long");return;}
  if(exists(out)){status("Destination exists - not overwritten");return;}
  status("Extracting...");paint();
  int ok=extract(full,out);
  refresh();status(ok?"ZIP extracted successfully":"Extraction failed - check output");return;
 }
 if(action==2){
  if(snprintf(out,sizeof(out),"%s.zip.tns",full)>=(int)sizeof(out)){status("Output path is too long");return;}
  if(exists(out)){status("ZIP already exists - not overwritten");return;}
  status("Compressing...");paint();
  int ok=create(out,full);
  refresh();status(ok?"ZIP created successfully":"Compression failed");
 }
}
int main(void){
 if(!lcd_init(SCR_320x240_565))return 1;
 refresh();wait_no_key_pressed();
 for(;;){
  paint();wait_key_pressed();
  if(listing){
   if(isKeyPressed(KEY_NSPIRE_ESC)||isKeyPressed(KEY_NSPIRE_ENTER))listing=0;
   else if(isKeyPressed(KEY_NSPIRE_UP)&&listscroll>0)listscroll--;
   else if(isKeyPressed(KEY_NSPIRE_DOWN)&&listscroll+12<nlisting)listscroll++;
  }else if(menu){
   if(isKeyPressed(KEY_NSPIRE_ESC)){menu=0;}
   else if(isKeyPressed(KEY_NSPIRE_UP)&&menusel>0)menusel--;
   else if(isKeyPressed(KEY_NSPIRE_DOWN)&&menusel<3)menusel++;
   else if(isKeyPressed(KEY_NSPIRE_ENTER)){
    int action=menusel;menu=0;if(action<3)operate(action);
   }
  }else{
   if(isKeyPressed(KEY_NSPIRE_ESC))break;
   else if(isKeyPressed(KEY_NSPIRE_UP)&&selected>0)selected--;
   else if(isKeyPressed(KEY_NSPIRE_DOWN)&&selected<count-1)selected++;
   else if(isKeyPressed(KEY_NSPIRE_LEFT))updir();
   else if(isKeyPressed(KEY_NSPIRE_ENTER)||isKeyPressed(KEY_NSPIRE_RIGHT)){
    if(count){menu=1;menusel=0;}
   }
   else if(isKeyPressed(KEY_NSPIRE_1))operate(1);
   else if(isKeyPressed(KEY_NSPIRE_2))operate(2);
   else if(isKeyPressed(KEY_NSPIRE_3))operate(0);
  }
  wait_no_key_pressed();
 }
 lcd_init(SCR_TYPE_INVALID);return 0;
}
