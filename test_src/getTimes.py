
import scipy.stats as stats
import numpy as np
import pandas as pd
import json
from pprint import pprint

# obj_set1  = [ '5k.html', '10k.html', '100k.html', '200k.html', '500k.html', '1mb.html', '10mb.html',]  
obj_set1  = ['10kx100.html']
obj_set2  = [ '1mbx1.html','500kx2.html' ,'200kx5.html' ,'100kx10.html', '10kx100.html', '5kx200.html' ]  

# obj_set3 = [ '5k.jpg', '10k.jpg', '100k.jpg', '200k.jpg', '500k.jpg', '1mb.jpg', '10mb.jpg',]  

obj_names = obj_set1 + obj_set2

graph1 = [ '10_36_0', '50_36_0', '100_36_0' ]
graph2 = ['10_112_0', '50_112_0', '100_112_0']
graph3 = ['10_36_1', '50_36_1', '100_36_1' ]

settings = graph1 + graph2 + graph3
### Changing
# Q043, v1 ,v2
mainDir = "../data/IMC23_beforetuning/"
### TIMES run
total_runs = 100
# X_36_0, X_36_1, X_112_0
setting = "X_36_1"
# Objs
objs = obj_set1
#####

cases = ["https", "quic"]

print("Setting :", setting)


tcp_df = pd.DataFrame(columns=objs)
quic_df = pd.DataFrame(columns=objs)

for bw in [100]:
    https_obj_times = {}
    quic_obj_times = {}
    for obj in objs:
        print("Object :", obj)
        times = { "https": [], "quic": []}
        for case in cases:
            for expNo in range(1,total_runs + 1):
                file_name = mainDir + setting.replace("X", str(bw)) + "/" + obj.replace(".", "_") + "/resultsDir/"+case+"_"+str(expNo)+".har"
                try:
                    with open( file_name , 'r') as f:
                        j = json.load(f)
                        # print('\t\t', j['log']['entries'][0]['time'])
                        load_t = j['log']['pages'][0]['pageTimings']['onLoad']
                        dns_t = j['log']['entries'][0]['timings']['dns']
                        plt_t = load_t - dns_t
                        times[case].append(plt_t)
                except Exception as e:
                    print("Failed ", e)
            print(file_name)
           # print(times["https"])
           # print(times["quic"])

        https_group1 = np.array(times["https"])
        quic_group2 = np.array(times["quic"])

        for i in range(total_runs):
            print(times["https"][i])

        print("\n")

        for i in range(total_runs):
            print(times['quic'][i])

        # Print the variance of both data groups
        print("TCP PLT Std: ", np.std(https_group1),"\t QUIC PLT Std :", np.std(quic_group2))
        print("TCP PLT 95th: ", np.percentile(https_group1, 95),"\t QUIC PLT 95th :", np.percentile(quic_group2, 95))


        # Calculate Stats and P-value of both data groups
        welch_test = stats.ttest_ind(https_group1, quic_group2, equal_var=False)
        # print(welch_test.pvalue)

        if welch_test.pvalue < 0.01:
            print("Performance Difference Statistically Significant")
        else:
            print("!!!!Performance Difference Statistically INSignificant!!!!")

        https_avg_time = np.average(https_group1)
        print("HTTPS: ", https_avg_time)
        https_obj_times[obj] = https_avg_time

        quic_avg_time = np.average(quic_group2)
        print("QUIC: ", quic_avg_time)
        quic_obj_times[obj] = quic_avg_time
        print("")

    # print("TCP Times :",  https_obj_times)
    # print("QUIC Times :", quic_obj_times)

    # tcp_df = tcp_df.append(https_obj_times, ignore_index = True)
    # quic_df = quic_df.append(quic_obj_times, ignore_index = True)
    tcp_df.loc[len(tcp_df)] = https_obj_times
    quic_df.loc[len(quic_df)] = quic_obj_times

print("QUIC Version : ", mainDir)
print("Setting :", setting)
print("Total Runs :", total_runs)
print("TCP Times")
print(tcp_df)
print()
pprint(tcp_df.to_string(header=False, index=False).split('\n'))

print()
print("QUIC Times")
print(quic_df)
print()
pprint(quic_df.to_string(header=False, index=False).split('\n'))

