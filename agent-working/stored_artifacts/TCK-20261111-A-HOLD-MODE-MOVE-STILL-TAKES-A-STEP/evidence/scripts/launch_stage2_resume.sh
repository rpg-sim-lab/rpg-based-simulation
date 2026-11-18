#!/bin/bash
# RESUME launcher (HOST FREE + the designer's sha OK only): continues the stopped stage-2 set with RESUME=1. Existing cells are kept; the original stage2_driver.log is never overwritten (this one appends to stage2_driver_resume.log).
# Pattern-free command line.
cd /mnt/data2/rpg-measure/holdmove
WAIVE=crowded_frontier:extinction:role0:6899865649 RESUME=1 ./run_stage2.sh >> stage2_driver_resume.log 2>&1
echo "driver_rc=$?" >> stage2_driver_resume.log
