#!/usr/bin/python

# send_to_mcd.py
#
# A simple script to send hp93000 configuration files such as Pin
# Configuration, Timing, Levels, Patterns and Pattern Master Files to the MCD.
# It detects the file type based on the first line which will be something
# like:
#
#   hp93000,config,0.1
#
# Some files, especially Pin Configuration, require special handling. This is
# supported by looking for a text file such as:
#
#   config.fw.pre
#   config.fw.post
#
# These contain firmware commands to send before and after the file is uploaded.
#
# One concern is that these firmware commands, which have been extracted from
# smarTest 6.5.4 by doing file loads using "diag 2" mode, will not be consisten
# for different versions of smarTest or for different hardware configurations
# or different license configurations. This is most concerning for Pin
# Configuration.
#
# TODO: Command-line option to limit debug output

from sys import stderr, argv, exit
from re import match, search, compile
from subprocess import call
from os import popen, getcwd, chdir, curdir
from os.path import normpath, realpath, dirname, exists, abspath, getctime

usage_string = """
Usage:

    send_to_mcd.py file
"""

def open_compressed(filename):
    try:
        if search(r"\.gz$", filename):
            f = popen("gzip -dc " + filename)
        elif search(r"\.bz2$", filename):
            f = popen("bzip2 -dc " + filename)
        elif search(r"\.xz$", filename):
            f = popen("xz -dc " + filename)
        else:
            f = open(filename, "rt")
    except IOError:
        stderr.write("Error: Failed to open " + filename + "\n")
        exit(1)
    return f

# TODO: How to find the path for these files?
def try_send_fw_file(fw_file):
    """Send a fw file to the mcd pipe if the file exists
    """

    try:
        # Test to see if the file exists and can be read.
        fwf = open(fw_file)
    except IOError:
        pass
    else:
        fwf.close()
        call([myhpt, fw_file])

def get_working_path(filename):
    """Take a filename and return a path sufficient for appending relative
    paths to
    """

    return normpath(getcwd() + '/')


class FileLabelsCalls:
    """Class for stroring the labels and calls contained in each pattern file.
    If a call and label appear in the same file, make it disappear.
    """

    def __init__(self, filename):
        self.filename = filename
        self.labels = set()
        self.calls = set()

    def add_call(self, call):
        if call in self.labels:
            self.labels.remove(call)
        else:
            self.calls.add(call)

    def add_label(self, label):
        if label in self.calls:
            self.calls.remove(label)
        else:
            self.labels.add(label)


re_sqlb = compile(r'SQLB "([^"]*)"')
re_sqpg_call = compile(r'SQPG \d+,CALL,[^,]*,"([^"]*)"')
re_vecc = compile(r'VEC[CD]')


def sort_files_by_who_calls_who(files):
    """Open pattern files and make sure that any file that calls a label in
    another file appears later in the list than the file having the label that
    it calls.
    """

# SQLB "bscan_highz",MPBU,0,1,,(pnobscan)
# SQPG 0,CALL,,"bscan_mask_pins",,(pnobscan)

    flcs = list()
    for file in files:
        flc = FileLabelsCalls(file)
        flcs.append(flc)
        f = open_compressed(file)
        for l in f:
            m = re_sqlb.match(l)
            if m:
                flc.add_label(m.group(1))
            m = re_sqpg_call.match(l)
            if m:
                flc.add_call(m.group(1))
            # Assume no SQLB or SQPG after VECC or VECD
            m = re_vecc.match(l)
            if m:
                break

    # We have a directed acyclic graph of who calls who it's just a matter of I
    # can't remember what to sort the files. Maybe something cheap will work.

    # Go through the list of unsorted files and remove each one that has no
    # outstanding calls and put it on the sorted list. Keep doing this until
    # they are all on the sorted list.

    sorted_list = []
    unsorted_flcs = flcs
    new_unsorted_flcs = []
    label_in_sorted_list = set()
    while(len(unsorted_flcs)):
        for flc in unsorted_flcs:
            add_to_sorted_list = False
            if len(flc.calls) == 0:
                add_to_sorted_list = True
            else:
                add_to_sorted_list = True
                for call in flc.calls:
                    if call not in label_in_sorted_list:
                        add_to_sorted_list = False
            if add_to_sorted_list:
                sorted_list.append(flc.filename)
                for label in flc.labels:
                    label_in_sorted_list.add(label)
            else:
                new_unsorted_flcs.append(flc)
        unsorted_flcs, new_unsorted_flcs = new_unsorted_flcs, []

    return sorted_list


def send_file_and_pre_post(filename, file_type):
    try_send_fw_file(file_type + ".fw.pre")
    try_send_fw_file(filename)
    try_send_fw_file(file_type + ".fw.post")


def do_pattern_master_file(filename):
    """Special handling for pmf files which load other files"""
    base_path = get_working_path(filename)
    f = open_compressed(filename)
    f.readline()  # discard first line since we already know it

    state = 'none'
    path = base_path
    files = []
    for l in f:
        skipline = False
        for w in l.split():
            if skipline:
                continue
            elif w.startswith("--"):
                # Skip comments
                skipline = True
                continue
            elif w == "path:":
                state = 'path'
            elif w == "files:":
                state = 'files'
            elif state == 'path':
                path = base_path + '/'  + w
            elif state == 'files':
                files.append(path + '/' + w)
    f.close()
    files = sort_files_by_who_calls_who(files)

    try_send_fw_file("pattern_master_file.fw.pre")
    for filename in files:
        send_file(filename)
    try_send_fw_file("pattern_master_file.fw.post")


def usage():
    stderr.write(usage_string)


def send_file(filename):
    """Detect the file type and send it along
    """

    f = open_compressed(filename)

    file_type_line = f.readline()
    m = match(r'hp93000,(\w+),([\d.]+)', file_type_line)
    if not m:
        stderr.write(
"""Error: First line of file should look like:

hp93000,filetype,0.1

But instead it is:

""" + file_type_line)
        exit(1)
    else:
        file_type, file_type_version = m.groups()

    f.close()

#    stderr.write("DEBUG: file_type %s, file_version: %s\n" % (file_type, file_type_version))

    if float(file_type_version) != 0.1:
        stderr.write("Warning: Expecting file type version 0.1, but got %s instead"
                % file_type_version)

    if file_type == "pattern_master_file":
        do_pattern_master_file(filename)
    else:
        send_file_and_pre_post(filename, file_type)


def file_is_newer(file_newer, file_older):
    """Return true if file_newer is actually newer than file_older"""
    if not exists(file_newer) or not exists(file_older):
        return False
    return getctime(file_newer) > getctime(file_older)


def make_myhpt():
    """Rebuild myhpt if myhpt.c has been modified or if myhpt isn't there"""
    myhpt_c = dirname(myhpt) + "/myhpt.c"
    if not exists(myhpt) or not file_is_newer(myhpt, myhpt_c):
        working_dir = abspath(curdir)
        chdir(dirname(myhpt))
        r = call(["make", "clean", "all"])
        if r != 0:
            stderr.write("ERROR: send_to_mcd.py failed to 'make clean all' myhpt in " + dirname(myhpt )+ "\n")
            exit(1)
        chdir(working_dir)


if(len(argv) != 2):
    usage()
    exit(1)

filename = argv[1]
myhpt = dirname(realpath(argv[0])) + "/myhpt"
make_myhpt()

send_file(filename)
