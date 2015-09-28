====================
Automated Photo Dump
====================

This software is for Raspberry Pi based automated photo dump from digital
camera memory cards adhering to "Design rule for Camera File system".

The system is based on recognizing DCF file system on a known or attached
partition and then copying the whole tree to another file system,
designated by the user. After the first use, the destination media is
recognized automatically based on the content therein.

Basic workflow
==============

1. Boot Pi into APD.
2. Plug in the destination media.
3. Plug in the source media (with a proper DCF file system).
4. APD copies the contents from the source to the destination, while
   keeping file metadata. Progress bars are displayed to keep user
   informed.
5. After copying, APD prompts user to remove source media.
6. Another source can be inserted, go to 4, otherwise go to 7.
7. After all source media have been copied, user can exit the software and
   shutdown RasPi at will.

At some point there will be an option to quit-and-shutdown from APD.

Workflow with the media already inserted
========================================

1. Boot Pi into APD.
2. APD asks which USB device to use as source.
3. APD asks which USB device to use as destination.
4. APD copies the contents from the source to the destination, while
   keeping file metadata. Progress bars are displayed to keep user
   informed.
5. After copying, APD prompts user to remove source media.
6. Another source can be inserted, go to 4, otherwise go to 7.
7. After all source media have been copied, user can exit the software and
   shutdown RasPi at will.
