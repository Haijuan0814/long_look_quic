#!/bin/bash

# Check if directory and setting arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <directory>  <runs>"
    exit 1
fi

# Extract directory and setting from arguments
directory="$1"
iterations="$2"

exp="masque"
proj="FEC-HTTP"

# Define the list of object sizes
object_sizes=("5k" "10k" "100k" "200k" "500k" "1mb" "10mb")
# object_sizes=("500k" "200k")

# Define the number of iterations
# iterations=20

# Define the list of settings
settings=("10_9_0" "50_9_0" "100_9_0" "10_9_0.0025" "50_9_0.0025" "100_9_0.0025" "10_25_0" "50_25_0" "100_25_0"  )
# settings=("10_9_0"  "10_9_0.0025" )

# Define the SSH command template
ssh_command='sudo ipfw pipe 60111 config bw %sMbit/s delay %sms plr %s && sudo ipfw pipe 60121 config bw %sMbit/s delay %sms plr %s'


# Loop over each setting
for setting in "${settings[@]}"; do
    # create dir
    mkdir -p "/proj/FEC-HTTP/long-quic/long-look-quic/data/${directory}/${setting}"
    # Extract bandwidth, delay, and loss from the setting
    IFS='_' read -r bandwidth delay loss <<< "$setting"

    # Execute the SSH command
    ssh_command_formatted=$(printf "$ssh_command" "$bandwidth" "$delay" "$loss" "$bandwidth" "$delay" "$loss")

    # Print the SSH command before executing it
    echo "Executing SSH command: $ssh_command_formatted"

    ssh "link1_bridge.$exp.$proj.emulab.net" "$ssh_command_formatted"
    ssh "link2_bridge.$exp.$proj.emulab.net" "$ssh_command_formatted"

    # validate the setting
    ./do_iperf.sh "/proj/FEC-HTTP/long-quic/long-look-quic/data/${directory}/${setting}/" 10.10.4.2
    ./do_ping.sh "/proj/FEC-HTTP/long-quic/long-look-quic/data/${directory}/${setting}/" 10.10.4.2

    # Loop over each object size
    for size in "${object_sizes[@]}"; do
        # Loop for the specified number of iterations
        for ((i=1; i<=$iterations; i++)); do
            # Run the quic_client command and append output to file
            /proj/FEC-HTTP/long-quic/quiche/masque-bin/quiche/quic_client --host=10.10.4.2 --port=443 --disable_certificate_verification  "https://www.example-quic.org/static/${size}.jpg"  --v=1 --stderrthreshold=1 --quiet  2>&1 | grep "MasqueTime" >> "/proj/FEC-HTTP/long-quic/long-look-quic/data/${directory}/${setting}/${size}_quic.txt"
            # Run the masque_client command and append output to file
            /proj/FEC-HTTP/long-quic/quiche/masque-bin/quiche/masque_client --disable_certificate_verification=true 10.10.3.2:9661 "https://www.example-quic.org/static/${size}.jpg"  --dns_on_client  --v=1 --stderrthreshold=1 2>&1 | grep "MasqueTime" >> "/proj/FEC-HTTP/long-quic/long-look-quic/data/${directory}/${setting}/${size}_masque.txt"
        
        done
    done
done