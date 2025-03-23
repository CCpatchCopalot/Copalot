# aflgo
```
Replaying crash - id:000024 (found at 14284 sec.):
TIFFReadDirectoryCheckOrder: Warning, Invalid TIFF directory; tags are not sorted in ascending order.
TIFFReadDirectory: Warning, Unknown field with tag 0 (0x0) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 609 (0x261) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 57344 (0xe000) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 28 (0x1c) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 544 (0x220) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 514 (0x202) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 57602 (0xe102) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 58874 (0xe5fa) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 65526 (0xfff6) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 57825 (0xe1e1) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 65535 (0xffff) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 5488 (0x1570) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 743 (0x2e7) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 5120 (0x1400) encountered.
TIFFFetchNormalTag: Warning, IO error during reading of "Tag 0"; tag ignored.
TIFFReadDirectory: Warning, Invalid data type for tag StripOffsets.
TIFFReadDirectory: Warning, TIFF directory is missing required "StripByteCounts" field, calculating from imagelength.
TIFFAdvanceDirectory: Error fetching directory count.
loadImage: Image lacks Photometric interpretation tag.
=================================================================
==2348497==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x6020000000db at pc 0x0000004efb66 bp 0x7ffcf5ebe080 sp 0x7ffcf5ebe078
READ of size 1 at 0x6020000000db thread T0
    #0 0x4efb65 in extractContigSamplesShifted24bits (/box/tiffcrop-cfbb883+0x4efb65)
    #1 0x5010c4 in extractCompositeRegions (/box/tiffcrop-cfbb883+0x5010c4)
    #2 0x4db22a in processCropSelections (/box/tiffcrop-cfbb883+0x4db22a)
    #3 0x4ce834 in main (/box/tiffcrop-cfbb883+0x4ce834)
error: failed to decompress '.debug_aranges', zlib is not available
error: failed to decompress '.debug_info', zlib is not available
error: failed to decompress '.debug_abbrev', zlib is not available
error: failed to decompress '.debug_line', zlib is not available
error: failed to decompress '.debug_str', zlib is not available
error: failed to decompress '.debug_loc', zlib is not available
error: failed to decompress '.debug_ranges', zlib is not available
    #4 0x7a63429c7082 in __libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082)
    #5 0x41c5fd in _start (/box/tiffcrop-cfbb883+0x41c5fd)

0x6020000000db is located 0 bytes to the right of 11-byte region [0x6020000000d0,0x6020000000db)
allocated by thread T0 here:
    #0 0x4980cd in malloc /src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp:145:3
    #1 0x5a940c in _TIFFmalloc (/box/tiffcrop-cfbb883+0x5a940c)
    #2 0x4e69a4 in limitMalloc (/box/tiffcrop-cfbb883+0x4e69a4)
    #3 0x4f43ef in rotateImage (/box/tiffcrop-cfbb883+0x4f43ef)
    #4 0x4d4d76 in correct_orientation (/box/tiffcrop-cfbb883+0x4d4d76)
    #5 0x4ce737 in main (/box/tiffcrop-cfbb883+0x4ce737)
    #6 0x7a63429c7082 in __libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082)

SUMMARY: AddressSanitizer: heap-buffer-overflow (/box/tiffcrop-cfbb883+0x4efb65) in extractContigSamplesShifted24bits
Shadow bytes around the buggy address:
  0x0c047fff7fc0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x0c047fff7fd0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x0c047fff7fe0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x0c047fff7ff0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x0c047fff8000: fa fa 00 00 fa fa 04 fa fa fa fd fa fa fa 00 fa
=>0x0c047fff8010: fa fa 00 fa fa fa fd fd fa fa 00[03]fa fa 00 02
  0x0c047fff8020: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff8030: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff8040: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff8050: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c047fff8060: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
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
==2348497==ABORTING
Exit value is 1

```
# beacon
```
Replaying crash - id:000048 (found at 55907 sec.):
TIFFReadDirectoryCheckOrder: Warning, Invalid TIFF directory; tags are not sorted in ascending order.
TIFFReadDirectory: Warning, Unknown field with tag 0 (0x0) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 609 (0x261) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 64001 (0xfa01) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 65535 (0xffff) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 39426 (0x9a02) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 65280 (0xff00) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 65300 (0xff14) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 368 (0x170) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 61891 (0xf1c3) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 39461 (0x9a25) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 25957 (0x6565) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 8197 (0x2005) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 23130 (0x5a5a) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 514 (0x202) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 46774 (0xb6b6) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 57829 (0xe1e5) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 57825 (0xe1e1) encountered.
TIFFFetchNormalTag: Warning, IO error during reading of "Tag 0"; tag ignored.
TIFFReadDirectory: Warning, Invalid data type for tag StripOffsets.
TIFFFetchNormalTag: Warning, Incorrect count for "Group3Options"; tag ignored.
TIFFReadDirectory: Warning, Invalid data type for tag StripByteCounts.
TIFFReadDirectory: Warning, Sum of Photometric type-related color channels and ExtraSamples doesn't match SamplesPerPixel. Defining non-color channels as ExtraSamples..
TIFFAdvanceDirectory: Error fetching directory count.
loadImage: Image lacks Photometric interpretation tag.
Fax3Decode1D: Warning, Line length mismatch at line 0 of strip 0 (got 1793, expected 1).
Fax3Decode1D: Warning, Line length mismatch at line 1 of strip 0 (got 7, expected 1).
=================================================================
==2348713==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x6030000003b2 at pc 0x0000004efb66 bp 0x7ffd7b452840 sp 0x7ffd7b452838
READ of size 1 at 0x6030000003b2 thread T0
    #0 0x4efb65 in extractContigSamplesShifted24bits (/box/tiffcrop-cfbb883+0x4efb65)
    #1 0x5010c4 in extractCompositeRegions (/box/tiffcrop-cfbb883+0x5010c4)
    #2 0x4db22a in processCropSelections (/box/tiffcrop-cfbb883+0x4db22a)
    #3 0x4ce834 in main (/box/tiffcrop-cfbb883+0x4ce834)
error: failed to decompress '.debug_aranges', zlib is not available
error: failed to decompress '.debug_info', zlib is not available
error: failed to decompress '.debug_abbrev', zlib is not available
error: failed to decompress '.debug_line', zlib is not available
error: failed to decompress '.debug_str', zlib is not available
error: failed to decompress '.debug_loc', zlib is not available
error: failed to decompress '.debug_ranges', zlib is not available
    #4 0x7fc5de819082 in __libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082)
    #5 0x41c5fd in _start (/box/tiffcrop-cfbb883+0x41c5fd)

0x6030000003b2 is located 0 bytes to the right of 18-byte region [0x6030000003a0,0x6030000003b2)
allocated by thread T0 here:
    #0 0x4980cd in malloc /src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp:145:3
    #1 0x5a940c in _TIFFmalloc (/box/tiffcrop-cfbb883+0x5a940c)
    #2 0x4e69a4 in limitMalloc (/box/tiffcrop-cfbb883+0x4e69a4)
    #3 0x4f43ef in rotateImage (/box/tiffcrop-cfbb883+0x4f43ef)
    #4 0x4d4d76 in correct_orientation (/box/tiffcrop-cfbb883+0x4d4d76)
    #5 0x4ce737 in main (/box/tiffcrop-cfbb883+0x4ce737)
    #6 0x7fc5de819082 in __libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082)

SUMMARY: AddressSanitizer: heap-buffer-overflow (/box/tiffcrop-cfbb883+0x4efb65) in extractContigSamplesShifted24bits
Shadow bytes around the buggy address:
  0x0c067fff8020: 00 00 00 00 fa fa 00 00 00 00 fa fa 00 00 00 00
  0x0c067fff8030: fa fa 00 00 00 00 fa fa 00 00 00 00 fa fa 00 00
  0x0c067fff8040: 00 00 fa fa 00 00 00 00 fa fa 00 00 00 00 fa fa
  0x0c067fff8050: 00 00 00 00 fa fa 00 00 00 00 fa fa 00 00 00 00
  0x0c067fff8060: fa fa 00 00 00 00 fa fa 00 00 00 fa fa fa fd fd
=>0x0c067fff8070: fd fa fa fa 00 00[02]fa fa fa fa fa fa fa fa fa
  0x0c067fff8080: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c067fff8090: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c067fff80a0: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c067fff80b0: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c067fff80c0: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
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
==2348713==ABORTING
Exit value is 1
```