#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include "miniz.h"

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
static void input(char *b,size_t n){if(!fgets(b,n,stdin)){b[0]=0;return;}b[strcspn(b,"\r\n")]=0;}
int main(void){
 char op[16],a[MAXPATH],b[MAXPATH];
 puts("UltraZIP 001 - Ndless test\n1 Extract ZIP\n2 Create ZIP from a file\n3 List ZIP\n0 Exit");
 for(;;){
 printf("\nChoice: ");input(op,sizeof(op));
 if(op[0]=='0'||!op[0])break;
 if(op[0]<'1'||op[0]>'3')continue;
 printf("Archive path: ");input(a,sizeof(a));if(!*a)continue;
 if(op[0]=='1'){printf("Destination directory: ");input(b,sizeof(b));puts(extract(a,b)?"Extract complete":"Extract failed");}
 if(op[0]=='2'){printf("Source file: ");input(b,sizeof(b));puts(create(a,b)?"ZIP created":"Create failed");}
 if(op[0]=='3'){mz_zip_archive z={0};if(mz_zip_reader_init_file(&z,a,0)){for(mz_uint i=0;i<mz_zip_reader_get_num_files(&z);i++){mz_zip_archive_file_stat st;if(mz_zip_reader_file_stat(&z,i,&st))printf("%s (%lu bytes)\n",st.m_filename,(unsigned long)st.m_uncomp_size);}mz_zip_reader_end(&z);}else puts("Cannot open ZIP");}
 }
 return 0;
}
