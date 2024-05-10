outfile=$1
host=$2

# CPU
printf "CPU info :\n" >> $outfile"_client_info.txt"
cat /proc/cpuinfo >> $outfile"_client_info.txt"

# Memory
printf "\n\n Memory info :\n" >> $outfile"_client_info.txt"
cat /proc/meminfo >> $outfile"_client_info.txt"

# Network
printf "\n\n Network info :\n" >> $outfile"_client_info.txt"
cat /sys/class/net/enp*/speed >> $outfile"_client_info.txt"

## Server Info
# CPU
printf "CPU info :\n" >> $outfile"_server_info.txt"
ssh $host cat /proc/cpuinfo >> $outfile"_server_info.txt"

# Memory
printf "\n\n Memory info :\n" >> $outfile"_server_info.txt"
ssh $host cat /proc/meminfo >> $outfile"_server_info.txt"

# Network
printf "\n\n Network info :\n" >> $outfile"_server_info.txt"
ssh $host cat /sys/class/net/enp*/speed >> $outfile"_server_info.txt"