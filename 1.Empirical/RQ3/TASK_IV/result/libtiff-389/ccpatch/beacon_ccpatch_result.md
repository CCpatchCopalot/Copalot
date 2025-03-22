Crash Replay log for tiffcrop-libtiff-389

Replaying crash - id:000000 (found at 12130 sec.):
TIFFReadDirectoryCheckOrder: Warning, Invalid TIFF directory; tags are not sorted in ascending order.
TIFFReadDirectory: Warning, Unknown field with tag 0 (0x0) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 609 (0x261) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 368 (0x170) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 514 (0x202) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 65535 (0xffff) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 57825 (0xe1e1) encountered.
TIFFReadDirectory: Warning, Unknown field with tag 60897 (0xede1) encountered.
TIFFFetchNormalTag: Warning, IO error during reading of "Tag 0"; tag ignored.
TIFFReadDirectory: Warning, Invalid data type for tag StripOffsets.
TIFFReadDirectory: Warning, Sum of Photometric type-related color channels and ExtraSamples doesn't match SamplesPerPixel. Defining non-color channels as ExtraSamples..
TIFFReadDirectory: Warning, TIFF directory is missing required "StripByteCounts" field, calculating from imagelength.
TIFFAdvanceDirectory: Error fetching directory count.
loadImage: Image lacks Photometric interpretation tag.
=================================================================
==2348281==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x6080000000f2 at pc 0x0000004efb66 bp 0x7ffe33cc08a0 sp 0x7ffe33cc0898
READ of size 1 at 0x6080000000f2 thread T0
    #0 0x4efb65 in extractContigSamplesShifted24bits (/box/tiffcrop-libtiff-389+0x4efb65)
    #1 0x5010c4 in extractCompositeRegions (/box/tiffcrop-libtiff-389+0x5010c4)
    #2 0x4db22a in processCropSelections (/box/tiffcrop-libtiff-389+0x4db22a)
    #3 0x4ce834 in main (/box/tiffcrop-libtiff-389+0x4ce834)
error: failed to decompress '.debug_aranges', zlib is not available
error: failed to decompress '.debug_info', zlib is not available
error: failed to decompress '.debug_abbrev', zlib is not available
error: failed to decompress '.debug_line', zlib is not available
error: failed to decompress '.debug_str', zlib is not available
error: failed to decompress '.debug_loc', zlib is not available
error: failed to decompress '.debug_ranges', zlib is not available
    #4 0x7bb4bdd3a082 in __libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082)
    #5 0x41c5fd in _start (/box/tiffcrop-libtiff-389+0x41c5fd)

0x6080000000f2 is located 0 bytes to the right of 82-byte region [0x6080000000a0,0x6080000000f2)
allocated by thread T0 here:
    #0 0x4980cd in malloc /src/llvm-project/compiler-rt/lib/asan/asan_malloc_linux.cpp:145:3
    #1 0x5a940c in _TIFFmalloc (/box/tiffcrop-libtiff-389+0x5a940c)
    #2 0x4e69a4 in limitMalloc (/box/tiffcrop-libtiff-389+0x4e69a4)
    #3 0x4f43ef in rotateImage (/box/tiffcrop-libtiff-389+0x4f43ef)
    #4 0x4d4d76 in correct_orientation (/box/tiffcrop-libtiff-389+0x4d4d76)
    #5 0x4ce737 in main (/box/tiffcrop-libtiff-389+0x4ce737)
    #6 0x7bb4bdd3a082 in __libc_start_main (/lib/x86_64-linux-gnu/libc.so.6+0x24082)

SUMMARY: AddressSanitizer: heap-buffer-overflow (/box/tiffcrop-libtiff-389+0x4efb65) in extractContigSamplesShifted24bits
Shadow bytes around the buggy address:
  0x0c107fff7fc0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x0c107fff7fd0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x0c107fff7fe0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x0c107fff7ff0: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x0c107fff8000: fa fa fa fa fd fd fd fd fd fd fd fd fd fd fd fa
=>0x0c107fff8010: fa fa fa fa 00 00 00 00 00 00 00 00 00 00[02]fa
  0x0c107fff8020: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c107fff8030: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c107fff8040: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c107fff8050: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x0c107fff8060: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
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
==2348281==ABORTING
Exit value is 1