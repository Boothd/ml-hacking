#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''Parse CSV data from a file and plot features in a graph

This script parses PCAP data from a specified CSV file (pre-processed using pcap_to_csv.py),
plotting features against known packet type.

Example:
    $ python __file__ -i csv_file_data -o /tmp -n 1000000 -l 200 -f -d 12345678

Author: chris.sampson@naimuri.com
'''
import logging.config, yaml
import sys, getopt, os.path, struct, socket
from tempfile import gettempdir
from timeit import default_timer as timer

import matplotlib.pyplot as plt
import numpy as np

'''int:    Bits representing TCP Flags'''
# FLAG_FIN = 1
FLAG_SYN = 2
FLAG_RST = 4
# FLAG_PSH = 8
FLAG_ACK = 16
# FLAG_URG = 32

FLAG_SYNACK = FLAG_SYN + FLAG_ACK
FLAG_RSTACK = FLAG_RST + FLAG_ACK

'''int:    Connection type'''
TYPE_ICMP = 1
TYPE_TCP = 6
TYPE_UDP = 17

'''string:    Column names used to access array data from ingested CSV'''
COL_ROWNUM = 'rownum'
COL_PROTOCOL = 'protocol'
COL_TIME = 'time'
COL_SOURCE_IP = 'src'
COL_DEST_IP = 'dst'
COL_SOURCE_PORT = 'src_port'
COL_DEST_PORT = 'dst_port'
COL_TTL = 'ttl'
COL_LENGTH = 'length'
COL_FRAGMENT = 'fragment'
COL_FLAGS = 'flags'

'''int:    Default lower bounds limit'''
DEFAULT_LOWER_BOUNDS = 200

# setup logging config
logging.config.dictConfig(yaml.load(open(os.path.join('config', 'logging.yaml'))))
logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])

def _print_usage(exit_code=0):
    '''Print usage and exit

    Args:
        exit_code (int):    The exit code to use when terminating the script

    '''
    f = sys.stderr if exit_code > 0 else sys.stdout

    print(__file__ + " -i <input file> [-o <output dir>] [-n <num records>] [-l <lower bounds> [-f] [-d <destination ip>]", file=f)
    print("-i <input file>: CSV format data file to be parsed")
    print("-n <num records>: Number of CSV rows to read as records for input")
    print("-o <output dir>: Directory for output of graph images (if unspecified, images will saved to the system temp directory)")
    print("-l <lower bounds>: Lower bounds for number of points before plotting a destination IP's incoming sources (default = 200)")
    print("-f: output feature graphs (otherwise omitted)")
    print("-d <destination ip>: Destination IP address (decimal format) to process (otherwise all destinations in file will be processed)")

    sys.exit(exit_code)

def _ipv4_int_to_dotted(ip_address):
    '''Convert a decimalised Ipv4 Address to its dotted representation

    Args:
        ip_address (int):       IP (v4) Address in decimalised format

    Returns:
        str:    Decimal-dot representation of all IP (v4) Address bytes

    '''
    return socket.inet_ntoa(struct.pack("!L", int(ip_address)))

def _start_plot():
    # create a new figure
    fig = plt.figure(figsize=(8, 6))
    plt.clf()

    return fig

def _finish_plot(title, output_dir=None, output_file=None):

    # add title
    plt.title(title)

    # scale to axes
    plt.autoscale(tight=False)

    if output_dir is None or output_file is None:
        # display the graph
        plt.show()
    else:
        # save image to output dir
        plt.savefig(os.path.join(output_dir, output_file))
    plt.close()

def _draw_scatter_graph(x_points, y_points, point_labels, x_title, y_title, title, output_dir=None, output_file=None, cmap_name='Paired'):
    '''
    Draw a 2D scatter graph using matplotlib and either save to output_dir or display to user
    '''
    # create a new figure
    _start_plot()

    # plot the points
    plt.scatter(x_points, y_points, c=point_labels, cmap=plt.cm.get_cmap(cmap_name))

    # add axis labels
    plt.xlabel(x_title).set_fontsize('x-small')
    plt.ylabel(y_title).set_fontsize('x-small')

    # complete and save/show the plot
    _finish_plot(title, output_dir, output_file)

def _get_unique_rows(data_arr, fields_arr):
    '''
    Extract unique rows of data from array based on a set of fields
    '''
    return np.unique(data_arr[fields_arr])

def _plot_feature_graphs(csv_data, output_dir=None):
    '''
    Plot several 2D graphs comparing standard features of the data
    '''

    num_graphs = 0

    # plot source/destination IPs
    unique_data = _get_unique_rows(csv_data, [COL_SOURCE_IP, COL_DEST_IP, COL_PROTOCOL])
    _draw_scatter_graph(unique_data[COL_SOURCE_IP], unique_data[COL_DEST_IP], unique_data[COL_PROTOCOL], 'Source IP', 'Destination IP', 'Source vs. Destination IP', output_dir, 'dest_source_ip_analysis.png')
    num_graphs += 1

    # plot source/destination ports
    unique_data = _get_unique_rows(csv_data, [COL_SOURCE_PORT, COL_DEST_PORT, COL_PROTOCOL])
    _draw_scatter_graph(unique_data[COL_SOURCE_PORT], unique_data[COL_DEST_PORT], unique_data[COL_PROTOCOL], 'Source Port', 'Destination Port', 'Source vs. Destination Port', output_dir, 'dest_source_port_analysis.png')
    num_graphs += 1

    # plot time to live/length
    unique_data = _get_unique_rows(csv_data, [COL_TTL, COL_LENGTH, COL_PROTOCOL])
    _draw_scatter_graph(unique_data[COL_TTL], unique_data[COL_LENGTH], unique_data[COL_PROTOCOL], 'Time to Live', 'Packet Length', 'TTL vs. Packet Length', output_dir, 'length_ttl_analysis.png')
    num_graphs += 1

    # plot length/fragment
    unique_data = _get_unique_rows(csv_data, [COL_LENGTH, COL_FRAGMENT, COL_PROTOCOL])
    _draw_scatter_graph(unique_data[COL_LENGTH], unique_data[COL_FRAGMENT], unique_data[COL_PROTOCOL], 'Packet Length', 'Fragment', 'Packet Length vs. Fragment', output_dir, 'fragment_length_analysis.png')
    num_graphs += 1

    # src port/flags
    unique_data = _get_unique_rows(csv_data, [COL_SOURCE_PORT, COL_FLAGS, COL_PROTOCOL])
    _draw_scatter_graph(unique_data[COL_SOURCE_PORT], unique_data[COL_FLAGS], unique_data[COL_PROTOCOL], 'Source Port', 'Flags', 'Source Port vs. TCP Flags', output_dir, 'tcpflags_source_port_analysis.png')
    num_graphs += 1

    return num_graphs

def plot_csv_features(csv_file, lower_bounds, output_dir, num_records=None, draw_feature_graphs=False, destination_ip=None):
    '''Parse PCAP data CSV file content and plot graphs of features vs. known packet type

    Fields expected in input:
        row#
        protocol (IP)
        time
        source (IP Address)
        destination (IP Address)
        source port
        destination port
        time to live (IP)
        length (IP)
        fragment (IP)
        flags (TCP)

    Args:
        csv_file (str):    Filename of CSV file data to be read
        lower_bounds (int): Lower bounds for number of points before plotting a destination IP's incoming sources
        output_dir (str):  Directory for saving graph images (if None, images will be displayed but not saved)
        num_records (int): Maximum number of records to read from input CSV (default: None - all lines)
        draw_feature_graphs (boolean): Whether to draw the feature graphs for the data (default: False)
        destination_ip (int): Destination IP for which to produce analysis (default: None - all IPs)
    '''
    # read CSV file into Numpy multi-dimensional arrays
    step_start = timer()
    csv_data = np.genfromtxt(csv_file,
                            delimiter=',',
                            autostrip=True,
                            dtype=None,
                            names=[COL_ROWNUM,
                                   COL_PROTOCOL,
                                   COL_TIME,
                                   COL_SOURCE_IP,
                                   COL_DEST_IP,
                                   COL_SOURCE_PORT,
                                   COL_DEST_PORT,
                                   COL_TTL,
                                   COL_LENGTH,
                                   COL_FRAGMENT,
                                   COL_FLAGS],
                            missing_values='??',
                            filling_values=0,
                            invalid_raise=False,
                            max_rows=num_records)

    # check that we've got a usable array
    if csv_data is None or not isinstance(csv_data, np.ndarray):
        logger.error("CSV (%s) to array (0 records or parsing failed) (seconds): %f", csv_file, timer() - step_start)
        return

    # stop if there's not enough data in the array to care about
    try:
        if len(csv_data) < lower_bounds:
            logger.warn("CSV (%s) to array (%d records), insufficient records for analysis (%d) (seconds): %f", csv_file, len(csv_data), lower_bounds, timer() - step_start)
            return
    except TypeError:
        logger.exception("Unable to confirm length of imported CSV (%s) array object (%s)", csv_file, type(csv_data))
        import pprint
        logger.debug("Array with no length: %s", pprint.pformat(csv_data))
        return

    # log how long the CSV parsing took and the number of records imported
    logger.info("CSV (%s) to array (%d records) (seconds): %f", csv_file, len(csv_data), timer() - step_start)

    # plot feature graphs from data, if requested
    if draw_feature_graphs:
        step_start = timer()
        feature_graphs_dir = os.path.join(output_dir, "feature_graphs")
        os.makedirs(feature_graphs_dir, exist_ok=True)
        num_graphs = _plot_feature_graphs(csv_data, feature_graphs_dir)
        logger.debug("Feature Graphs plotted (%d) (seconds): %f", num_graphs, timer() - step_start)

    # build up sent/received details about all IPs
    ips = {}

    # iterate through collections of Source IP and record details for IP as a sender
    step_start = timer()
    sorted_src_data = np.sort(csv_data, order=[COL_SOURCE_IP, COL_TIME])

    # split into sub-arrays by unique Source IP
    src_ips = np.split(sorted_src_data, np.where(np.diff(sorted_src_data[COL_SOURCE_IP]))[0] + 1)
    logger.debug("Source IPs sorted and unique (%d) (seconds): %f", len(src_ips), timer() - step_start)

    # track number of destinations for each Source IP if in debug mode
    if logger.isEnabledFor(logging.DEBUG):
        dests = np.zeros([len(src_ips), 1])
        s = 0

    for src_data in src_ips:
        if len(src_data) > 0:
            # determine current Source IP and number of connection records
            src_ip = str(src_data[0][COL_SOURCE_IP])

            # if IP filter specified, ensure we've got a match, otherwise ignore the data
            if destination_ip is None or src_ip == str(destination_ip):
                num_connections = len(src_data)

                # log sent data stats for the IP
                ips[src_ip] = dict(received_bytes=0,
                                    received_connections=0,
                                    received_earliest=0,
                                    received_latest=0,
                                    dst_details=list(),
                                    sent_bytes=np.sum(src_data[COL_LENGTH]),
                                    sent_connections=num_connections,
                                    sent_earliest=src_data[0][COL_TIME],
                                    sent_latest=src_data[-1][COL_TIME],
                                    src_details=src_data)

                # debug output of the destination characteristics for all sources
                if logger.isEnabledFor(logging.DEBUG):
                    dests[s] = len(src_data)
                    s += 1
            else:
                logger.debug("Ignoring Source data for IP %s due to filter", src_ip)

    src_ips = None
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Source Destinations - Num: %d, Min: %d, Max: %d, Avg: %f", len(dests), min(dests), max(dests), sum(dests) / len(dests))
        dests = None

    # iterate through collections of Destination IP and record details for IP as a receiver
    step_start = timer()
    sorted_dst_data = np.sort(csv_data, order=[COL_DEST_IP, COL_TIME])

    # split into sub-arrays by unique Destination IP
    dst_ips = np.split(sorted_dst_data, np.where(np.diff(sorted_dst_data[COL_DEST_IP]))[0] + 1)
    logger.debug("Destination IPs sorted and unique (%d) (seconds): %f", len(dst_ips), timer() - step_start)

    # track number of sources for each Destination IP if in debug mode
    if logger.isEnabledFor(logging.DEBUG):
        sources = np.zeros([len(dst_ips), 1])
        d = 0

    num_graphs = 0
    num_ips = 0

    # iterate through collections of Destination IP and record details for IP as a receiver and output analysis
    dst_analysis_dir = os.path.join(output_dir, "dst_analysis")
    for dst_data in dst_ips:
        if len(dst_data) > 0:
            # determine current Destination IP and number of connection records
            dst_ip = str(dst_data[0][COL_DEST_IP])

            # if IP filter specified, ensure we've got a match, otherwise ignore the data
            if destination_ip is None or dst_ip == str(destination_ip):
                num_connections = len(dst_data)
                total_bytes = np.sum(dst_data[COL_LENGTH])

                # log received data stats for the IP
                ip_rec = None
                if not dst_ip in ips:
                    ip_rec = dict(received_bytes=total_bytes,
                                        received_connections=num_connections,
                                        received_earliest=dst_data[0][COL_TIME],
                                        received_latest=dst_data[-1][COL_TIME],
                                        dst_details=dst_data,
                                        sent_bytes=0,
                                        sent_connections=0,
                                        sent_earliest=0,
                                        sent_latest=0,
                                        src_details=list())
                    ips[dst_ip] = ip_rec
                else:
                    ip_rec = ips[dst_ip]
                    ip_rec["received_bytes"] = total_bytes
                    ip_rec["received_connections"] = num_connections
                    ip_rec["src_details"] = list()
                    ip_rec["dst_details"] = dst_data
                    ip_rec['received_earliest'] = dst_data[0][COL_TIME]
                    ip_rec['received_latest'] = dst_data[-1][COL_TIME]

                # debug output of the source characteristics and times for all destinations
                if logger.isEnabledFor(logging.DEBUG):
                    sources[d] = len(dst_data)
                    d += 1

                # output IP destination graphs (if there are enough incoming connections to make it seem like we'd care...)
                recv_conns = num_connections
                if recv_conns > lower_bounds:
                    # create directory for Destination IP's graphs
                    dst_str = _ipv4_int_to_dotted(int(dst_ip))
                    dst_dir = os.path.join(dst_analysis_dir, dst_str)
                    os.makedirs(dst_dir, exist_ok=True)

                    # graph each Destination IP for:
                    #    * (scatter) Destination Port vs. Source IP
                    # Connection summary subplots for:
                    #    * (pie) #connections received/sent
                    #    * (pie) #bytes received/sent
                    # Time-series subplots for:
                    #    * (scatter) Destination Port connections
                    #    * (line) #connections (with Flags)
                    #        * (line) #SYN (not ACK) connections
                    #        * (line) #ACK (not SYN or RST) connections
                    #        * (line) #SYN-ACK connections
					#        * (line) #RST (not ACK) connections
					#        * (line) #RST-ACK connections
                    #    * (line) #connections (by Type)
                    #        * (line) #TCP connections
                    #        * (line) #ICMP connections
                    #        * (line) #UDP connections
                    #    * (line) #bytes received
                    # Source summary subplots for:
                    #    * (bar) #connections (from Source IP)
                    #    * (bar) #bytes (from Source IP)

                    # plot Destination Ports vs. Source IP (indicating protocols used)
                    # get unique points for plotting only (performance)
                    unique_data = _get_unique_rows(dst_data, [COL_DEST_PORT, COL_SOURCE_IP, COL_PROTOCOL])
                    _draw_scatter_graph(unique_data[COL_DEST_PORT], unique_data[COL_SOURCE_IP], unique_data[COL_PROTOCOL], 'Destination Port', 'Source IP', _ipv4_int_to_dotted(dst_ip), dst_dir, 'ports_and_sources.png')
                    num_graphs += 1


                    # create pie-chart subplots
                    plt.clf()
                    f, (pie_conns, pie_bytes) = plt.subplots(2)

                    # set figure title and x-axis
                    f.suptitle(dst_str + " - Connection Summary")

                    # plot total Received vs. Sent connections
                    dst_rec = ips[dst_ip]
                    sent_conns = dst_rec['sent_connections']
                    # sizes, labels, colours, title, explode=None, output_dir=None, output_file=None
                    pie_conns.pie([recv_conns, sent_conns], labels=['#Received', '#Sent'], explode=[0.1, 0], colors=['r', 'g'], autopct='%1.1f%%', shadow=True, startangle=90)
                    pie_conns.axis('equal')  # set aspect ratio to be equal so that pie is drawn as a circle.
                    num_graphs += 1

                    # plot total Received vs. Sent bytes
                    recv_bytes = total_bytes
                    sent_bytes = dst_rec['sent_bytes']
                    pie_bytes.pie([recv_bytes, sent_bytes], labels=['Bytes Received', 'Bytes Sent'], explode=[0.1, 0], colors=['y', 'b'], autopct='%1.1f%%', shadow=True, startangle=90)
                    pie_bytes.axis('equal')  # set aspect ratio to be equal so that pie is drawn as a circle.
                    num_graphs += 1

                    # scale & save image to output dir
                    plt.autoscale(tight=False)
                    plt.savefig(os.path.join(dst_dir, 'connections_summary.png'))
                    plt.close()


                    # create time-series graphs as subplots in a single figure
                    plt.clf()
                    f, (dst_ports, conn_flags, conn_types, brecv) = plt.subplots(4, sharex=True)

                    # set figure title and x-axis
                    f.suptitle(dst_str + " - Time Series Analysis")
                    brecv.set_xlabel('Time / ms').set_fontsize('x-small')

                    # time-series plot of single Destination IP (indicating Source IPs)
                    # unlikely there will be many duplicates when time being considered
                    dst_ports.scatter(dst_data[COL_TIME], dst_data[COL_DEST_PORT], marker=".", c=dst_data[COL_SOURCE_IP], cmap=plt.cm.get_cmap('Paired'))
                    dst_ports.set_ylabel('Port').set_fontsize('x-small')
                    box = dst_ports.get_position()
                    dst_ports.set_position([box.x0, box.y0, box.width * 0.9, box.height])
                    num_graphs += 1


                    # plot received #connections over time (cumulative sum of connections along the time-sorted array)
                    # get the times from the packet data
                    conn_times = np.array(dst_data[COL_TIME])
                    # create a 2D array of 1s, the same length as the number of connections (times)
                    conn_time_counts = np.ones([len(conn_times), 2])
                    # insert the connection times at index 0, then use the additional column of 1s for the cumsum operation
                    conn_time_counts[:, 0] = conn_times
                    conn_flags.plot(conn_time_counts[:, 0], np.cumsum(conn_time_counts[:, 1]), linestyle='-', color='black', label="All (" + str(len(conn_times)) + ")")
                    conn_times = None
                    conn_time_counts = None
                    conn_flags.set_ylabel("# by Flag").set_fontsize('x-small')

                    # SYN not ACK
                    syn_connections = dst_data[(dst_data[COL_FLAGS] & FLAG_SYN == FLAG_SYN) & (dst_data[COL_FLAGS] & FLAG_ACK != FLAG_ACK)]
                    if len(syn_connections) > 0:
                        syn_times = np.array(syn_connections[COL_TIME])
                        # create a 2D array of 1s, the same length as the number of connections (times)
                        syn_time_counts = np.ones([len(syn_times), 2])
                        # insert the connection times at index 0, then use the additional column of 1s for the cumsum operation
                        syn_time_counts[:, 0] = syn_times
                        conn_flags.plot(syn_time_counts[:, 0], np.cumsum(syn_time_counts[:, 1]), linestyle='-', color='red', label="SYN (" + str(len(syn_connections)) + ")")
                        ip_rec['received_syn'] = len(syn_connections)
                        syn_connections = None
                        syn_times = None
                        syn_time_counts = None

                    # ACK not SYN or RST
                    ack_connections = dst_data[(dst_data[COL_FLAGS] & FLAG_ACK == FLAG_ACK) & (dst_data[COL_FLAGS] & FLAG_SYN != FLAG_SYN) & (dst_data[COL_FLAGS] & FLAG_RST != FLAG_RST)]
                    if len(ack_connections) > 0:
                        ack_times = np.array(ack_connections[COL_TIME])
                        # create a 2D array of 1s, the same length as the number of connections (times)
                        ack_time_counts = np.ones([len(ack_times), 2])
                        # insert the connection times at index 0, then use the additional column of 1s for the cumsum operation
                        ack_time_counts[:, 0] = ack_times
                        conn_flags.plot(ack_time_counts[:, 0], np.cumsum(ack_time_counts[:, 1]), linestyle='-', color='yellow', label="ACK (" + str(len(ack_connections)) + ")")
                        ip_rec['received_ack'] = len(ack_connections)
                        ack_connections = None
                        ack_times = None
                        ack_time_counts = None

                    # SYN-ACK
                    synack_connections = dst_data[dst_data[COL_FLAGS] & FLAG_SYNACK == FLAG_SYNACK]
                    if len(synack_connections) > 0:
                        synack_times = np.array(synack_connections[COL_TIME])
                        # create a 2D array of 1s, the same length as the number of connections (times)
                        synack_time_counts = np.ones([len(synack_times), 2])
                        # insert the connection times at index 0, then use the additional column of 1s for the cumsum operation
                        synack_time_counts[:, 0] = synack_times
                        conn_flags.plot(synack_time_counts[:, 0], np.cumsum(synack_time_counts[:, 1]), linestyle='-', color='orange', label="SYN-ACK (" + str(len(synack_connections)) + ")")
                        ip_rec['received_synack'] = len(synack_connections)
                        synack_connections = None
                        synack_times = None
                        synack_time_counts = None

                    # RST not ACK
                    rst_connections = dst_data[(dst_data[COL_FLAGS] & FLAG_RST == FLAG_RST) & (dst_data[COL_FLAGS] & FLAG_ACK != FLAG_ACK)]
                    if len(rst_connections) > 0:
                        rst_times = np.array(rst_connections[COL_TIME])
                        # create a 2D array of 1s, the same length as the number of connections (times)
                        rst_time_counts = np.ones([len(rst_times), 2])
                        # insert the connection times at index 0, then use the additional column of 1s for the cumsum operation
                        rst_time_counts[:, 0] = rst_times
                        conn_flags.plot(rst_time_counts[:, 0], np.cumsum(rst_time_counts[:, 1]), linestyle='-', color='blue', label="RST (" + str(len(rst_connections)) + ")")
                        ip_rec['received_rst'] = len(rst_connections)
                        rst_connections = None
                        rst_times = None
                        rst_time_counts = None

                    # RST-ACK
                    rstack_connections = dst_data[dst_data[COL_FLAGS] & FLAG_RSTACK == FLAG_RSTACK]
                    if len(rstack_connections) > 0:
                        rstack_times = np.array(rstack_connections[COL_TIME])
                        # create a 2D array of 1s, the same length as the number of connections (times)
                        rstack_time_counts = np.ones([len(rstack_times), 2])
                        # insert the connection times at index 0, then use the additional column of 1s for the cumsum operation
                        rstack_time_counts[:, 0] = rstack_times
                        conn_flags.plot(rstack_time_counts[:, 0], np.cumsum(rstack_time_counts[:, 1]), linestyle='-', color='green', label="RST-ACK (" + str(len(rstack_connections)) + ")")
                        ip_rec['received_rstack'] = len(rstack_connections)
                        rstack_connections = None
                        rstack_times = None
                        rstack_time_counts = None

                    # add legend for the different types of flags in the connections
                    box = conn_flags.get_position()
                    conn_flags.set_position([box.x0, box.y0, box.width * 0.9, box.height])
                    conn_flags.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='x-small')
                    num_graphs += 1


                    # plot received #connections over time (cumulative sum of connections along the time-sorted array)
                    conn_types.set_ylabel("# by Type").set_fontsize('x-small')

                    # TCP
                    tcp_connections = dst_data[dst_data[COL_PROTOCOL] == TYPE_TCP]
                    if len(tcp_connections) > 0:
                        tcp_times = np.array(tcp_connections[COL_TIME])
                        # create a 2D array of 1s, the same length as the number of connections (times)
                        tcp_time_counts = np.ones([len(tcp_times), 2])
                        # insert the connection times at index 0, then use the additional column of 1s for the cumsum operation
                        tcp_time_counts[:, 0] = tcp_times
                        conn_types.plot(tcp_time_counts[:, 0], np.cumsum(tcp_time_counts[:, 1]), linestyle='-', color='r', label="TCP (" + str(len(tcp_connections)) + ")")

                        ip_rec['received_tcp'] = len(tcp_connections)
                        tcp_connections = None
                        tcp_times = None
                        tcp_time_counts = None

                    # ICMP
                    icmp_connections = dst_data[dst_data[COL_PROTOCOL] == TYPE_ICMP]
                    if len(icmp_connections) > 0:
                        icmp_times = np.array(icmp_connections[COL_TIME])
                        # create a 2D array of 1s, the same length as the number of connections (times)
                        icmp_time_counts = np.ones([len(icmp_times), 2])
                        # insert the connection times at index 0, then use the additional column of 1s for the cumsum operation
                        icmp_time_counts[:, 0] = icmp_times
                        conn_types.plot(icmp_time_counts[:, 0], np.cumsum(icmp_time_counts[:, 1]), linestyle='-', color='g', label="ICMP (" + str(len(icmp_connections)) + ")")

                        ip_rec['received_icmp'] = len(icmp_connections)
                        icmp_connections = None
                        icmp_times = None
                        icmp_time_counts = None

                    # UDP
                    udp_connections = dst_data[dst_data[COL_PROTOCOL] == TYPE_UDP]
                    if len(udp_connections) > 0:
                        udp_times = np.array(udp_connections[COL_TIME])
                        # create a 2D array of 1s, the same length as the number of connections (times)
                        udp_time_counts = np.ones([len(udp_times), 2])
                        # insert the connection times at index 0, then use the additional column of 1s for the cumsum operation
                        udp_time_counts[:, 0] = udp_times
                        conn_types.plot(udp_time_counts[:, 0], np.cumsum(udp_time_counts[:, 1]), linestyle='-', color='b', label="UDP (" + str(len(udp_connections)) + ")")

                        ip_rec['received_udp'] = len(udp_connections)
                        udp_connections = None
                        udp_times = None
                        udp_time_counts = None

                    # add legend for the different types of flags in the connections
                    box = conn_types.get_position()
                    conn_types.set_position([box.x0, box.y0, box.width * 0.9, box.height])
                    conn_types.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize='x-small')
                    num_graphs += 1


                    # plot bytes received over time (cumulative sum of packet lengths along the time-sorted array)
                    brecv.plot(dst_data[COL_TIME], np.cumsum(dst_data[COL_LENGTH]), linestyle='-', color='b')
                    brecv.set_ylabel("Bytes").set_fontsize('x-small')
                    box = brecv.get_position()
                    brecv.set_position([box.x0, box.y0, box.width * 0.9, box.height])
                    num_graphs += 1

                    # scale & save image to output dir
                    plt.autoscale(tight=False)
                    plt.savefig(os.path.join(dst_dir, 'time_series.png'))
                    plt.close()


                    # create Source summary graphs as subplots in a single figure
                    plt.clf()

                    # split into sub-arrays by unique Source IP
                    sorted_dst_srcs = np.sort(dst_data, order=[COL_SOURCE_IP])
                    dst_src_ips = np.split(sorted_dst_srcs, np.where(np.diff(sorted_dst_srcs[COL_SOURCE_IP]))[0] + 1)

                    # create 2D array of 0s, the same length as the number of Source IPs
                    dst_srcs = np.empty([len(dst_src_ips), 3], dtype='object')
                    ip_rec['received_sources'] = len(dst_srcs)
                    s = 0
                    for dst_src_data in dst_src_ips:
                        if len(dst_src_data) > 0:
                            # determine current Source IP, store with count of connections and sum of bytes transmitted
                            dst_srcs[s, 0] = _ipv4_int_to_dotted(dst_src_data[0][COL_SOURCE_IP])
                            dst_srcs[s, 1] = len(dst_src_data)
                            dst_srcs[s, 2] = np.sum(dst_src_data[COL_LENGTH])
                            s += 1

                    dst_src_ips = None
                    if len(dst_srcs) > 0:
                        f, (src_conns, src_bytes) = plt.subplots(2, sharex=True)

                        # set image title
                        f.suptitle(dst_str + " - Source Summary")

                        # x locations for the groups
                        ind = np.arange(len(dst_srcs))

                        # plot #connections from Source
                        src_conns.bar(ind, dst_srcs[:, 1], color='r', align='center')
                        src_conns.set_ylabel("#Connections").set_fontsize('x-small')

                        # plot #bytes from Source
                        src_bytes.bar(ind, dst_srcs[:, 2], color='y', align='center')
                        src_bytes.set_ylabel("#Bytes").set_fontsize('x-small')

                        # set x-axis labels
                        src_bytes.set_xticks(ind)
                        src_bytes.set_xticklabels(dst_srcs[:, 0], fontsize='x-small')
                        f.subplots_adjust(bottom=0.25)  # increase space for labels
                        plt.setp(src_bytes.get_xticklabels(), rotation=90)  # rotate labels to make readable

                        num_graphs += 1

                        # scale & save image to output dir
                        plt.autoscale(tight=False)
                        plt.savefig(os.path.join(dst_dir, 'sources_summary.png'))
                        plt.close()

                    dst_srcs = None

                num_ips += 1
            else:
                # logger.debug("Ignoring Destination data for %s due to filtering", dst_ip)
                num_ips = num_ips

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("IP analysis (%d), graphs (%d) (seconds): %f", num_ips, num_graphs, timer() - step_start)
        logger.debug("Destination Sources - Num: %d, Min: %d, Max: %d, Avg: %f", len(sources), min(sources), max(sources), sum(sources) / len(sources))
        sources = None

    # output stats for IPs
    stats_ips = {ip:rec for ip, rec in ips.items() if 'received_connections' in rec and rec['received_connections'] > 0}
    for ip, rec in stats_ips.items():
        logger.info("Destination statistics: IP=%s, %s", _ipv4_int_to_dotted(ip), {k:v for k, v in rec.items() if k.startswith('received_') or k.startswith('sent_')})
    stats_ips = None
    ips = None

def main(argv):
    '''Parse input args and run the PCAP data CSV parser on specified inputfile (-i)

    Args:
        argv (list):    List of command line arguments

    '''
    inputfile = ''
    outputdir = None
    num_records = None
    lower_bounds = DEFAULT_LOWER_BOUNDS
    draw_feature_graphs = False
    destination_ip = None

    try:
        opts, _ = getopt.getopt(argv, "hfi:o:n:l:d:")
    except getopt.GetoptError:
        _print_usage(1)

    for opt, arg in opts:
        if opt == '-h':
            _print_usage(0)
        elif opt == '-f':
            draw_feature_graphs = True
        elif opt == '-i':
            inputfile = arg
            if not os.path.isfile(inputfile):
                logger.error("Invalid input file (-i), file does not exist (%s)", inputfile)
                sys.exit(2)
        elif opt == '-o':
            outputdir = arg
            if not os.path.isdir(outputdir):
                logger.info("Output directory (-o) does not exist (%s), creating", outputdir)
                try:
                    os.makedirs(outputdir)
                except:
                    logger.exception("Could not create output directory (-o) (%s)", outputdir)
                    sys.exit(2)
        elif opt == '-n':
            try:
                num_records = int(arg)
                if num_records < 1:
                    logger.error("Number of records (-n) must be greater than 0, got (%d)", num_records)
                    sys.exit(3)
            except:
                logger.exception("Unable to parse number of records (-n), must be numeric, got (%s)", arg)
                sys.exit(4)
        elif opt == '-l':
            try:
                lower_bounds = int(arg)
                if lower_bounds < 1:
                    logger.error("Lower bounds (-l) must be greater than 0, got (%d)", lower_bounds)
                    sys.exit(5)
            except:
                logger.exception("Unable to parse lower bounds (-l), must be numeric, got (%s)", arg)
                sys.exit(6)
        elif opt == '-d':
            try:
                destination_ip = int(arg)
                if destination_ip < 1:
                    logger.error("Destination IP (-d) must be greater than 0, got (%d)", destination_ip)
                    sys.exit(7)
            except:
                logger.exception("Unable to parse Destination IP (-d), must be numeric, got (%s)", arg)
                sys.exit(8)

    logger.info('Input file: %s', inputfile)
    logger.info('Draw feature graphs? %s', draw_feature_graphs)
    if outputdir is None:
        outputdir = gettempdir()
    logger.info('Output directory: %s', outputdir)
    if not num_records is None:
        logger.info('Record limit: %d', num_records)
    if not lower_bounds is None:
        logger.info('Lower bounds: %d', lower_bounds)
    if not destination_ip is None:
        logger.info('Destination IP (filter): %d', destination_ip)

    start = timer()
    plot_csv_features(inputfile, lower_bounds, outputdir, num_records, draw_feature_graphs, destination_ip)

    end = timer()
    logger.info("Execution time (seconds): %f", end - start)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except:
        logger.exception('Problem executing program')
        raise
