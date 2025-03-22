# aflgo
```
Replaying crash - id:000663 (found at 63765 sec.):
=================================================================
==1014642==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x6020000003b1 at pc 0x00000097db43 bp 0x7ffd97bf58d0 sp 0x7ffd97bf58c8
READ of size 1 at 0x6020000003b1 thread T0
    #0 0x97db42 in gf_m2ts_process_pmt (/box/MP4Box-8c5e847+0x97db42)
    #1 0x977950 in gf_m2ts_section_complete (/box/MP4Box-8c5e847+0x977950)
    #2 0x976626 in gf_m2ts_gather_section (/box/MP4Box-8c5e847+0x976626)
    #3 0x961cad in gf_m2ts_process_data (/box/MP4Box-8c5e847+0x961cad)
    #4 0x974156 in gf_m2ts_probe_file (/box/MP4Box-8c5e847+0x974156)
    #5 0x88b90c in gf_dasher_add_input (/box/MP4Box-8c5e847+0x88b90c)
    #6 0x4dcfb0 in mp4boxMain (/box/MP4Box-8c5e847+0x4dcfb0)
error: failed to decompress '.debug_aranges', zlib is not available
error: failed to decompress '.debug_info', zlib is not available
error: failed to decompress '.debug_abbrev', zlib is not available
error: failed to decompress '.debug_line', zlib is not available
error: failed to decompress '.debug_str', zlib is not available
error: failed to decompress '.debug_loc', zlib is not available
error: failed to decompress '.debug_ranges', zlib is not available
    #7 0x7dc6b403e082 in __libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082)
    #8 0x41d84d in _start (/box/MP4Box-8c5e847+0x41d84d)

0x6020000003b1 is located 0 bytes to the right of 1-byte region [0x6020000003b0,0x6020000003b1)
allocated by thread T0 here:
    #0 0x49931d in malloc /src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp:145:3
    #1 0x976f40 in gf_m2ts_section_complete (/box/MP4Box-8c5e847+0x976f40)
    #2 0x976626 in gf_m2ts_gather_section (/box/MP4Box-8c5e847+0x976626)

SUMMARY: AddressSanitizer: heap-buffer-overflow (/box/MP4Box-8c5e847+0x97db42) in gf_m2ts_process_pmt
Shadow bytes around the buggy address:
  0x0c047fff8020: fa fa fd fd fa fa 00 00 fa fa 00 00 fa fa 00 00
  0x0c047fff8030: fa fa 00 00 fa fa 00 00 fa fa 00 00 fa fa 00 00
  0x0c047fff8040: fa fa 00 00 fa fa 00 00 fa fa 00 00 fa fa 00 00
  0x0c047fff8050: fa fa 00 00 fa fa 00 00 fa fa 00 00 fa fa 00 00
  0x0c047fff8060: fa fa 00 00 fa fa fd fd fa fa 03 fa fa fa 00 00
=>0x0c047fff8070: fa fa 00 00 fa fa[01]fa fa fa fa fa fa fa fa fa
  0x0c047fff8080: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff8090: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff80a0: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff80b0: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff80c0: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
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
==1014642==ABORTING
Exit value is 1
```

# beacon
```
Replaying crash - id:00079 (found at 35322 sec.):
[33m[MPEG-2 TS] TS Packet 2 is scrambled - not supported
[0m[33m[MPEG-2 TS] TS Packet 3 is scrambled - not supported
[0m[33m[MPEG-2 TS] TS Packet 4 is scrambled - not supported
[0m[33m[MPEG-2 TS] TS Packet 5 is scrambled - not supported
[0m[33m[MPEG-2 TS] TS Packet 6 is scrambled - not supported
[0m[33m[MPEG-2 TS] TS Packet 7 is scrambled - not supported
[0m[33m[MPEG-2 TS] TS Packet 8 is scrambled - not supported
[0m[31m[MPEG-2 TS] PID 1863: Bad Adaptation Extension found
[0m=================================================================
==3911088==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x602000000431 at pc 0x000000c69c34 bp 0x7ffe761f3a30 sp 0x7ffe761f3a28
READ of size 1 at 0x602000000431 thread T0
    #0 0xc69c33 in gf_m2ts_process_pmt /benchmark/project-ccpath/gpac-8c5e847/SRC/src/media_tools/mpegts.c:2162:52
    #1 0xc60460 in gf_m2ts_section_complete /benchmark/project-ccpath/gpac-8c5e847/SRC/src/media_tools/mpegts.c:1609:6
    #2 0xc5e3c3 in gf_m2ts_gather_section /benchmark/project-ccpath/gpac-8c5e847/SRC/src/media_tools/mpegts.c:1739:2
    #3 0xc3dbb7 in gf_m2ts_process_packet /benchmark/project-ccpath/gpac-8c5e847/SRC/src/media_tools/mpegts.c:3445:17
    #4 0xc3dbb7 in gf_m2ts_process_data /benchmark/project-ccpath/gpac-8c5e847/SRC/src/media_tools/mpegts.c:3506:8
    #5 0xc5a67a in gf_m2ts_probe_file /benchmark/project-ccpath/gpac-8c5e847/SRC/src/media_tools/mpegts.c:4640:6
    #6 0xc03039 in gf_media_import /benchmark/project-ccpath/gpac-8c5e847/SRC/src/media_tools/media_import.c:10998:6
    #7 0x5391c1 in convert_file_info /benchmark/project-ccpath/gpac-8c5e847/SRC/applications/mp4box/fileimport.c:124:6
    #8 0x5020bb in mp4boxMain /benchmark/project-ccpath/gpac-8c5e847/SRC/applications/mp4box/main.c:4804:6
error: failed to decompress '.debug_aranges', zlib is not available
error: failed to decompress '.debug_info', zlib is not available
error: failed to decompress '.debug_abbrev', zlib is not available
error: failed to decompress '.debug_line', zlib is not available
error: failed to decompress '.debug_str', zlib is not available
error: failed to decompress '.debug_loc', zlib is not available
error: failed to decompress '.debug_ranges', zlib is not available
    #9 0x7945adb98082 in __libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082)
    #10 0x41d89d in _start (/benchmark/bin/AFLGo-ccpath/MP4Box-f40aaaf+0x41d89d)

0x602000000431 is located 0 bytes to the right of 1-byte region [0x602000000430,0x602000000431)
allocated by thread T0 here:
    #0 0x49936d in malloc /src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp:145:3
    #1 0xc5f189 in gf_m2ts_section_complete /benchmark/project-ccpath/gpac-8c5e847/SRC/src/media_tools/mpegts.c:1549:36
    #2 0xc5e3c3 in gf_m2ts_gather_section /benchmark/project-ccpath/gpac-8c5e847/SRC/src/media_tools/mpegts.c:1739:2
    #3 0xc3dbb7 in gf_m2ts_process_packet /benchmark/project-ccpath/gpac-8c5e847/SRC/src/media_tools/mpegts.c:3445:17
    #4 0xc3dbb7 in gf_m2ts_process_data /benchmark/project-ccpath/gpac-8c5e847/SRC/src/media_tools/mpegts.c:3506:8
    #5 0xc5a67a in gf_m2ts_probe_file /benchmark/project-ccpath/gpac-8c5e847/SRC/src/media_tools/mpegts.c:4640:6
    #6 0xc03039 in gf_media_import /benchmark/project-ccpath/gpac-8c5e847/SRC/src/media_tools/media_import.c:10998:6
    #7 0x5391c1 in convert_file_info /benchmark/project-ccpath/gpac-8c5e847/SRC/applications/mp4box/fileimport.c:124:6
    #8 0x5020bb in mp4boxMain /benchmark/project-ccpath/gpac-8c5e847/SRC/applications/mp4box/main.c:4804:6
    #9 0x7945adb98082 in __libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082)

SUMMARY: AddressSanitizer: heap-buffer-overflow /benchmark/project-ccpath/gpac-8c5e847/SRC/src/media_tools/mpegts.c:2162:52 in gf_m2ts_process_pmt
Shadow bytes around the buggy address:
  0x0c047fff8030: fa fa 00 00 fa fa 00 00 fa fa 00 00 fa fa 00 00
  0x0c047fff8040: fa fa 00 00 fa fa 00 00 fa fa 00 00 fa fa 00 00
  0x0c047fff8050: fa fa 00 00 fa fa 00 00 fa fa 00 00 fa fa 00 00
  0x0c047fff8060: fa fa 00 00 fa fa 00 00 fa fa 00 00 fa fa fd fa
  0x0c047fff8070: fa fa 00 00 fa fa fd fd fa fa fd fa fa fa 03 fa
=>0x0c047fff8080: fa fa 00 00 fa fa[01]fa fa fa fa fa fa fa fa fa
  0x0c047fff8090: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff80a0: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff80b0: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff80c0: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff80d0: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
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
==3911088==ABORTING
Aborted
```