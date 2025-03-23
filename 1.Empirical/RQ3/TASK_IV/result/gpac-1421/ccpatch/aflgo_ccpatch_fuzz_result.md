Replaying crash - id:000429 (found at 11966 sec.):
[32m[MPEG-2 TS] PID 0 AF Location descriptor found - URL http://�
[0m[31m[MPEG-2 TS] PID 0: Bad Adaptation Descriptor found (tag 0) size is 0 but only 33 bytes available
[0m=================================================================
==486619==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x6020000005f1 at pc 0x00000097db43 bp 0x7ffe254a4750 sp 0x7ffe254a4748
READ of size 1 at 0x6020000005f1 thread T0
    #0 0x97db42 in gf_m2ts_process_pmt (/box/MP4Box-1421+0x97db42)
    #1 0x977950 in gf_m2ts_section_complete (/box/MP4Box-1421+0x977950)
    #2 0x976626 in gf_m2ts_gather_section (/box/MP4Box-1421+0x976626)
    #3 0x961cad in gf_m2ts_process_data (/box/MP4Box-1421+0x961cad)
    #4 0x974156 in gf_m2ts_probe_file (/box/MP4Box-1421+0x974156)
    #5 0x88b90c in gf_dasher_add_input (/box/MP4Box-1421+0x88b90c)
    #6 0x4dcfb0 in mp4boxMain (/box/MP4Box-1421+0x4dcfb0)
error: failed to decompress '.debug_aranges', zlib is not available
error: failed to decompress '.debug_info', zlib is not available
error: failed to decompress '.debug_abbrev', zlib is not available
error: failed to decompress '.debug_line', zlib is not available
error: failed to decompress '.debug_str', zlib is not available
error: failed to decompress '.debug_loc', zlib is not available
error: failed to decompress '.debug_ranges', zlib is not available
    #7 0x74388863a082 in __libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082)
    #8 0x41d84d in _start (/box/MP4Box-1421+0x41d84d)

0x6020000005f1 is located 0 bytes to the right of 1-byte region [0x6020000005f0,0x6020000005f1)
allocated by thread T0 here:
    #0 0x49931d in malloc /src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp:145:3
    #1 0x976f40 in gf_m2ts_section_complete (/box/MP4Box-1421+0x976f40)
    #2 0x976626 in gf_m2ts_gather_section (/box/MP4Box-1421+0x976626)

SUMMARY: AddressSanitizer: heap-buffer-overflow (/box/MP4Box-1421+0x97db42) in gf_m2ts_process_pmt
Shadow bytes around the buggy address:
  0x0c047fff8060: fa fa fd fa fa fa fd fd fa fa fd fa fa fa fd fd
  0x0c047fff8070: fa fa fd fa fa fa fd fd fa fa fd fa fa fa fd fd
  0x0c047fff8080: fa fa fd fa fa fa fd fd fa fa fd fa fa fa fd fd
  0x0c047fff8090: fa fa fd fa fa fa fd fd fa fa fd fa fa fa fd fa
  0x0c047fff80a0: fa fa fd fa fa fa fd fd fa fa fd fa fa fa 02 fa
=>0x0c047fff80b0: fa fa 03 fa fa fa 00 00 fa fa 00 00 fa fa[01]fa
  0x0c047fff80c0: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff80d0: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff80e0: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff80f0: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff8100: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
Shadow byte legend (one shadow byte represents 8 application bytes):
  Addressable:           00
  Partially addressable: 01 02 03 04 05 06 07 
  Heap left redzone:       fa
  Freed heap region:       fd
  Stack left redzone:      f1
  Stack mid redzone:       f2
  Stack right redzone:     f3
  Stack after return:      f5
  Stack use after scope:   f8
  Global redzone:          f9
  Global init order:       f6
  Poisoned by user:        f7
  Container overflow:      fc
  Array cookie:            ac
  Intra object redzone:    bb
  ASan internal:           fe
  Left alloca redzone:     ca
  Right alloca redzone:    cb
  Shadow gap:              cc
==486619==ABORTING
Exit value is 1