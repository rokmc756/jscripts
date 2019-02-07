
https://access.redhat.com/solutions/5407

$ ps aux | awk '{if($1 ~ "weblogic"){Total+=$6}} END {print Total/1024" MB"}'
  7604.53 MB`


https://access.redhat.com/solutions/427733


This can be done by parsing the values /proc/<PID>/smaps as follows:
Raw
# cat /proc/<PID>/smaps | grep -i Swap | awk '{sum+=$2} END {print sum}'
  <Sum of memory swapped out>

# cat /proc/8883/smaps | grep -i RSS | awk '{sum+=$2} END {print sum}'
  <Sum of memory in RAM>
This can also be extracted from /proc/<PID>/status as follows:
Raw
# cat /proc/<PID>/status | egrep "Vm(RSS|Swap)"

