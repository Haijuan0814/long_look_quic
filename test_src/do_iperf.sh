outfile=$1
host=$2

# iperf3 -f Mbits -R -O 3 -J -c $host > $outfile"_iperf3.json"
iperf3 -R -i 1 -t 60 -V -c $host > $outfile"_iperf3.txt"
# iperf3 -R  -u -b 1000m -i 1 -t 60 -V -c $host > $outfile"_udp_iperf3.txt"
