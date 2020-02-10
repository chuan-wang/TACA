import os
import re
import csv
import glob
import shutil
import gzip
import operator
import subprocess
from datetime import datetime
from taca.utils.filesystem import chdir, control_fastq_filename
from taca.illumina.Runs import Run
from taca.illumina.HiSeqX_Runs import HiSeqX_Run
from taca.utils import misc

import logging

logger = logging.getLogger(__name__)

class NextSeq_Run(HiSeqX_Run):

    def __init__(self,  run_dir, samplesheet_folders):
        super(NextSeq_Run, self).__init__(run_dir, samplesheet_folders)
        self._set_sequencer_type()
        self._set_run_type()

    def _set_sequencer_type(self):
        self.sequencer_type = "NextSeq"

    def _set_run_type(self):
        self.run_type = "NGI-RUN"
