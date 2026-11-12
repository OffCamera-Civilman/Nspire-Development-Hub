#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include "miniz.h"
#include <dirent.h>
#define OLD_SCREEN_API
#include <libndls.h>

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

/* UltraZIP 002 - keypad-controlled directory browser, no keyboard paths. */
#define MAXENT 128
typedef struct { char name[256]; int directory; } entry_t;
static entry_t entries[MAXENT];
static int count=0,selected=0;
static char cwd[MAXPATH]="/documents";
static char feedback[160]="Choose file with arrows; Enter to open";
static int zipname(const char *p) {
 size_t n=strlen(p);
 return (n>=4&&!strcmp(p+n-4,".zip")) || (n>=8&&!strcmp(p+n-8,".zip.tns"));
}
static int join(char *out,size_t sz,const char *dir,const char *name){
 return snprintf(out,sz,"%s%s%s",dir,!strcmp(dir,"/")?"":"/",name)<(int)sz;
}
static void refresh(void){
 DIR *d=opendir(cwd);struct dirent *e;count=selected=0;
 if(!d){strcpy(cwd,"/");d=opendir(cwd);}
 if(!d){snprintf(feedback,sizeof(feedback),"Could not open folder");return;}
 while((e=readdir(d))&&count<MAXENT){
   char full[MAXPATH];struct stat st;
   if(!strcmp(e->d_name,".")||!strcmp(e->d_name,".."))continue;
   if(strlen(e->d_name)>=sizeof(entries[0].name))continue;
   if(!join(full,sizeof(full),cwd,e->d_name))continue;
   if(stat(full,&st))continue;
   strcpy(entries[count].name,e->d_name);
   entries[count].directory=S_ISDIR(st.st_mode)?1:0;
   count++;
 }
 closedir(d);
 for(int i=0;i<count;i++)for(int j=i+1;j<count;j++)
   if(entries[j].directory>entries[i].directory ||
      (entries[i].directory==entries[j].directory &&
       strcmp(entries[i].name,entries[j].name)>0)){
     entry_t t=entries[i];entries[i]=entries[j];entries[j]=t;
   }
}
static void updir(void){
 if(!strcmp(cwd,"/"))return;
 char *s=strrchr(cwd,'/');
 if(!s||s==cwd)strcpy(cwd,"/");
 else *s=0;
 refresh();
}
static void draw(void){
 clrscr();
 printf("UltraZIP 002 | ZIP Browser\\n");
 printf("Folder: %.45s\\n",cwd);
 printf("UP/DOWN browse; ENTER open folder\\n");
 printf("1 Extract | 2 Create | 3 List\\n");
 printf("LEFT parent | ESC exit\\n");
 printf("--------------------------------\\n");
 int first=selected-6;if(first<0)first=0;
 for(int i=first;i<count&&i<first+13;i++)
   printf("%c %c %.34s\\n",i==selected?'>':' ',entries[i].directory?'D':' ',entries[i].name);
 if(!count)printf("(empty folder)\\n");
 printf("--------------------------------\\n%.65s\\n",feedback);
}
static void showlist(const char *archive){
 mz_zip_archive z={0};clrscr();
 printf("ZIP contents: %.40s\\n",archive);
 if(mz_zip_reader_init_file(&z,archive,0)){
   int n=(int)mz_zip_reader_get_num_files(&z);
   printf("Entries: %d (first 18 shown)\\n",n);
   for(int i=0;i<n&&i<18;i++){
     mz_zip_archive_file_stat st;
     if(mz_zip_reader_file_stat(&z,i,&st))
       printf("%.42s\\n",st.m_filename);
   }
   mz_zip_reader_end(&z);
 }else printf("Not a supported ZIP file\\n");
 printf("Press any key to return\\n");
 wait_no_key_pressed();wait_key_pressed();wait_no_key_pressed();
}
static void act(int action){
 char full[MAXPATH],out[MAXPATH];
 if(!count||entries[selected].directory){snprintf(feedback,sizeof(feedback),"Select a FILE, not a folder");return;}
 if(!join(full,sizeof(full),cwd,entries[selected].name)){strcpy(feedback,"Path too long");return;}
 if(action!=2&&!zipname(entries[selected].name)){strcpy(feedback,"Select a .zip or .zip.tns archive");return;}
 if(action==3){showlist(full);return;}
 if(action==2){
   if(snprintf(out,sizeof(out),"%s.zip.tns",full)>=(int)sizeof(out)){strcpy(feedback,"Path too long");return;}
   clrscr();printf("Creating ZIP...\\n");
   snprintf(feedback,sizeof(feedback),"%s",create(out,full)?"Created ZIP (refresh folder)":"Create failed (or already exists)");
 }else{
   size_t len=strlen(full);char base[MAXPATH];
   strcpy(base,full);
   if(len>=8&&!strcmp(base+len-8,".zip.tns"))base[len-8]=0;
   else if(len>=4&&!strcmp(base+len-4,".zip"))base[len-4]=0;
   if(snprintf(out,sizeof(out),"%s_unzipped",base)>=(int)sizeof(out)){strcpy(feedback,"Path too long");return;}
   if(exists(out)){strcpy(feedback,"Output folder exists; extraction blocked");return;}
   clrscr();printf("Extracting ZIP...\\n");
   snprintf(feedback,sizeof(feedback),"%s",extract(full,out)?"Extract complete":"Extraction failed / partial output");
 }
 refresh();
}
int main(void){
 refresh();wait_no_key_pressed();
 for(;;){
   draw();wait_key_pressed();
   if(isKeyPressed(KEY_NSPIRE_ESC))break;
   else if(isKeyPressed(KEY_NSPIRE_UP)){if(selected>0)selected--;}
   else if(isKeyPressed(KEY_NSPIRE_DOWN)){if(selected<count-1)selected++;}
   else if(isKeyPressed(KEY_NSPIRE_LEFT)){updir();}
   else if(isKeyPressed(KEY_NSPIRE_ENTER)||isKeyPressed(KEY_NSPIRE_RIGHT)){
     if(count&&entries[selected].directory){
       char next[MAXPATH];
       if(join(next,sizeof(next),cwd,entries[selected].name)){strcpy(cwd,next);refresh();}
     }else if(count)strcpy(feedback,"Use 1 Extract / 2 Create / 3 List");
   }
   else if(isKeyPressed(KEY_NSPIRE_1))act(1);
   else if(isKeyPressed(KEY_NSPIRE_2))act(2);
   else if(isKeyPressed(KEY_NSPIRE_3))act(3);
   wait_no_key_pressed();
 }
 clrscr();return 0;
}
