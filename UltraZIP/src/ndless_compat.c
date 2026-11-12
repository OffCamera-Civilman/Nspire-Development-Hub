/* Ndless libc has no utime(). miniz calls it only to restore extracted
 * files' modification timestamps. Preserve extracted bytes and accept
 * the filesystem's current timestamp instead. No metadata write attempted.
 */
int utime(const char *path, const void *times)
{
    (void)path;
    (void)times;
    return 0;
}
