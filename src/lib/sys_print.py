import sys

def print_progress_bar(job_title, progress, length):
    progress = int((progress * 100) / length)
    sys.stdout.write("\r  " + job_title + " %d%%" % progress)
    sys.stdout.flush()
