# -*- coding: utf-8 -*-
"""
Created on Fri Feb18  11:02:32 2022
V1.To create csv file from RegularEventLogsData.bin

@author: Niloofar
"""

import pandas as pd
import os
import datetime
import sys
#import pkg_resources.py2_warn  #pyinstaller --hidden-import pkg_resources.py2_warn example.py
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog



#-------------------------------
def remove_prefix(str):
    """
    :param str: To correct Tmin and Tmax format
    :return: '00' or '0x'
    """
    ""
    if len(str.lstrip('0x')) == 0:
        return ('00')   #to avoid empty string ''
    return str.lstrip('0x')



#
def s16(value):
    """
    get_8bit_signed_value, default is INT16 - Big Endian (AB)
    :param value: integer
    :return: decimal signed value
    """
    return -(value & 0x8000) | (value & 0x7fff)

RegularEventID = {
    0 : "EVENT_ID_POWER_ON = 0",
    1 : "EVENT_ID_POWER_OFF",
    2 : "EVENT_ID_SET_CLOCK",
    3 : "EVENT_ID_CHARGER_CONNECTED",
    4 : "EVENT_ID_CHARGE_START",
    5 : "EVENT_ID_CHARGE_END",
    6 : "EVENT_ID_CHARGER_DISCONNECTED",
    7 : "EVENT_ID_FIRMWARE_CHANGE",
    8 : "EVENT_ID_TEMPERATURE_OVER_40C",
    9 : "EVENT_ID_TEMPERATURE_OVER_45C",
    10 : "EVENT_ID_TEMPERATURE_BELOW_0C",
    11 : "EVENT_ID_TEMPERATURE_BELOW_MINUS_5C",
    12 : "EVENT_ID_VOLTAGE_BELOW_AOT"
}

def browseFiles(button_explore_sys):
    """
    to insert the data_dir inside the windows
    """
    file_name=filedialog.askdirectory()
    txt_sys.insert(20, file_name)


def clicked():
    #read directories
    data_directory = txt_sys.get()
    if "/" not in r"%r" % data_directory and "\\" not in r"%r" % data_directory:
        messagebox.showwarning('Message title', 'The data directory is blank')
    print (data_directory)
    os.chdir(data_directory)

    # Read and store the bin file in binary format
    big_byte = b''
    with open('RegularEventLogsData.bin', 'rb', buffering=10) as f:
        for line in f:
            big_byte += line  # fp.readline() has limited size and cannot store all bytes. For loop is required

    ##flat_list = [item for sublist in lst for item in sublist]  #all saved as decimal!!  lst = [[b'...'] , [b'']]

    # create a dictionary that stores RegularEvents
    dict = {}
    next_szEvent_location = 0
    lst_msg_size =[]
    while next_szEvent_location < len(big_byte):
        n = big_byte[next_szEvent_location + 1]  # the value of szEvent
        msg_size = 4 + n
        lst_msg_size.append(msg_size)
        next_szEvent_size = int((12 + 20 * (msg_size)))
        next_szEvent_location = int(next_szEvent_size + next_szEvent_location)
        print('start location: {} and size of the struct: {} '.format((next_szEvent_location - next_szEvent_size),
                                                                      next_szEvent_size))
        dict[next_szEvent_location] = big_byte[next_szEvent_location - next_szEvent_size: next_szEvent_location]

    update_dict = {}
    h = 0
    for a , b  in zip(list(dict.keys()) , lst_msg_size):
        event_id = RegularEventID[dict[a][0]]
        for j in range(0, 20): # event is always 20
            k = 12 + (j * b)
            # Convert epoch date
            m_str = hex(dict[a][k + 3]) + hex(dict[a][k + 2]) + hex(dict[a][k + 1]) + hex(dict[a][k])  # ok
            if len(m_str) != 16:  # to debug empty epoch and fix format 0x05 to "05" instead of "5" -> 05917359
                k3 = hex(dict[a][k + 3])
                k2 = hex(dict[a][k + 2])
                k1 = hex(dict[a][k + 1])
                k0 = hex(dict[a][k])
                if len(k3) != 4: k3 = hex(dict[a][k + 3]).replace("0x", "0x0")
                if len(k2) != 4: k2 = hex(dict[a][k + 2]).replace("0x", "0x0")
                if len(k1) != 4: k1 = hex(dict[a][k + 1]).replace("0x", "0x0")
                if len(k0) != 4: k0 = hex(dict[a][k]).replace("0x", "0x0")
                m_str = k3 + k2 + k1 + k0

            GMT_added = datetime.timedelta(hours=5)  # convert from GMT-5 to GMT
            epoch_time_inhex = ''
            for i in range(2, len(m_str), 4):
                epoch_time_inhex = epoch_time_inhex + m_str[i:i + 2]

            date_time = datetime.datetime.fromtimestamp(int(epoch_time_inhex, 16)) + GMT_added

            # Convert SOC and HMI
            if b - 4 >= 2:
                SOC = dict[a][k + 4]
                HMI_Error = dict[a][k + 5]

            if b - 4 >= 6:
                # Convert Tmax and Tmin. apply s16 to obtain signed value such as -41
                d = remove_prefix(hex(dict[a][k + 7])) + remove_prefix(hex(dict[a][k + 6]))
                T_min = s16(int(d, 16))
                d = remove_prefix(hex(dict[a][k + 9])) + remove_prefix(hex(dict[a][k + 8]))
                T_max = s16(int(d, 16))
            else:
                T_min = ''
                T_max = ''

            if b - 4 >= 8 and b - 4 < 12:
                d = remove_prefix(hex(dict[a][k + 11])) + remove_prefix(hex(dict[a][k + 10]))
                Current = s16(int(d, 16)) * 10
            else:
                Current = ''
            if b - 4 >= 10 and b - 4 < 12:
                d = remove_prefix(hex(dict[a][k + 13])) + remove_prefix(hex(dict[a][k + 12]))
                Capacity = s16(int(d, 16))
            else:
                Capacity = ''

            if b - 4 >= 12:
                V_min = ((dict[a][k + 11]) * 256 + (dict[a][k + 10])) / 1000
                V_max = ((dict[a][k + 13]) * 256 + (dict[a][k + 12])) / 1000
                V_avg = ((dict[a][k + 15]) * 256 + (dict[a][k + 14])) / 1000
            else:
                V_min = ''
                V_max = ''
                V_avg = ''
            update_dict[h] = {'TimeStamp': date_time, 'Event': event_id, 'SOC': SOC, 'HMI_Error': HMI_Error,
                              'MinTemp': T_min, 'MaxTemp': T_max, 'Current': Current, 'Capacity': Capacity,
                              'Min Volt': V_min, 'Max Volt': V_max, 'Avg Volt': V_avg}
            h += 1

    df = pd.DataFrame.from_dict(update_dict, orient='index')
    df.drop_duplicates(inplace=True)
    df.index = df['TimeStamp']
    del df['TimeStamp']
    df.sort_index(ascending=True, inplace=True)
    start_remove = pd.to_datetime('2030-01-01')  # to remove empty epoch and wrong data
    end_remove = pd.to_datetime('1980-01-01')
    df = df.loc[(df.index < start_remove) & (df.index > end_remove)]
    df.to_csv('RegularEventLogsData' + '.csv')


#-------------------------------


window = Tk()
window.title("Electrovaya decoding RegularEventLogsData")
window.geometry('500x50')


lbl = Label(window, text="Enter the RegularEventLogsData.bin Directory:")
lbl.grid(column=0, row=0)

button_explore_sys = Button(window,text="Browse Files", command =lambda: browseFiles(True))
button_explore_sys.grid(column=1, row=1)
txt_sys = Entry(window, width=50)
txt_sys.grid(column=0, row=1)


btn = Button(window, text="ClickMe", command=clicked)
btn.grid(column=3, row=1)



window.mainloop()



#-------------------------------------------------------------

##Pyboard Version without datetime and pandas 
import os
import time
import sys


#-------------------------------
def remove_prefix(str):
    """
    :param str: To correct Tmin and Tmax format
    :return: '00' or '0x'
    """
    ""
    if len(str.lstrip('0x')) == 0:
        return ('00')   #to avoid empty string ''
    return str.lstrip('0x')



#
def s16(value):
    """
    get_8bit_signed_value, default is INT16 - Big Endian (AB)
    :param value: integer
    :return: decimal signed value
    """
    return -(value & 0x8000) | (value & 0x7fff)

RegularEventID = {
    0 : "EVENT_ID_POWER_ON = 0",
    1 : "EVENT_ID_POWER_OFF",
    2 : "EVENT_ID_SET_CLOCK",
    3 : "EVENT_ID_CHARGER_CONNECTED",
    4 : "EVENT_ID_CHARGE_START",
    5 : "EVENT_ID_CHARGE_END",
    6 : "EVENT_ID_CHARGER_DISCONNECTED",
    7 : "EVENT_ID_FIRMWARE_CHANGE",
    8 : "EVENT_ID_TEMPERATURE_OVER_40C",
    9 : "EVENT_ID_TEMPERATURE_OVER_45C",
    10 : "EVENT_ID_TEMPERATURE_BELOW_0C",
    11 : "EVENT_ID_TEMPERATURE_BELOW_MINUS_5C",
    12 : "EVENT_ID_VOLTAGE_BELOW_AOT"
}



# Read and store the bin file in binary format


big_byte=b''
with open('log/RegularEventLogsData.bin','rb') as f:
    for line in f:
        big_byte +=line  # fp.readline() has limited size and cannot store all bytes. For loop is required
print(len(big_byte))




# create a dictionary that stores RegularEvents
dict={}
next_szEvent_location=0
lst_msg_size =[]
while next_szEvent_location < len(big_byte):
    n = big_byte[next_szEvent_location+1]  #the value of szEvent
    msg_size = 4 + n
    lst_msg_size.append(msg_size)
    next_szEvent_size=int((12+20*(msg_size)))
    next_szEvent_location= int(next_szEvent_size + next_szEvent_location)
    print('start location: {} and size of the struct: {} '.format((next_szEvent_location - next_szEvent_size), next_szEvent_size))
    dict[next_szEvent_location] = big_byte[next_szEvent_location - next_szEvent_size : next_szEvent_location ]


wf = open('log/RegularEventLogsData.txt', 'w')  

for a , b  in zip(sorted(list(dict.keys())) , lst_msg_size):  # sort the dictionary since it is NOT stored in order!!
    event_id = RegularEventID[dict[a][0]]
    for j in range(0, 20):
         k = 12+(j*b)
         
         # Convert epoch data

         m_str = hex(dict[a][k+3]) + hex(dict[a][k+2]) + hex(dict[a][k+1]) + hex(dict[a][k])  # ok
         
         if len(m_str) != 16:  #to debug empty epoch and fix format 0x05 to "05" instead of "5" -> 05917359
             k3 = hex(dict[a][k + 3])
             k2 = hex(dict[a][k + 2])
             k1 = hex(dict[a][k + 1])
             k0 = hex(dict[a][k])
             if len(k3) != 4: k3 = hex(dict[a][k + 3]).replace("0x", "0x0")
             if len(k2) != 4: k2 = hex(dict[a][k + 2]).replace("0x", "0x0")
             if len(k1) != 4: k1 = hex(dict[a][k + 1]).replace("0x", "0x0")
             if len(k0) != 4: k0 = hex(dict[a][k]).replace("0x", "0x0")
             m_str = k3 + k2 + k1+ k0

         #GMT_added = datetime.timedelta(hours=5)  #convert from GMT-5 to GMT
         epoch_time_inhex = ''
         for i in range(2, len(m_str), 4):
             epoch_time_inhex = epoch_time_inhex + m_str[i:i + 2]

         if epoch_time_inhex == '00000000': continue  # to remove empty epoch
         e_date= int(epoch_time_inhex,16) - 946684800  # calibrate the date minus 30 years
         date_time = time.localtime(e_date)
    

         # Convert SOC and HMI
         if b-4 >=2:
             SOC =  dict[a][k+4]
             HMI_Error = dict[a][k+5]

         if b - 4 >= 6:
             # Convert Tmax and Tmin. apply s16 to obtain signed value such as -41
             d = remove_prefix(hex(dict[a][k+7])) + remove_prefix(hex(dict[a][k+6]))
             T_min = s16(int(d, 16))
             d= remove_prefix(hex(dict[a][k + 9])) + remove_prefix(hex(dict[a][k + 8]))
             T_max = s16(int(d, 16))
         else:
             T_min = ''
             T_max = ''

         if b - 4 >= 8 and b - 4 < 12:
             d = remove_prefix(hex(dict[a][k+11])) + remove_prefix(hex(dict[a][k+10]))
             Current = s16(int(d, 16))*10
         else:
             Current = ''
         if b - 4 >= 10 and b - 4 < 12:
             d = remove_prefix(hex(dict[a][k+13])) + remove_prefix(hex(dict[a][k+12]))
             Capacity = s16(int(d, 16))
         else:
             Capacity = ''

         if b - 4 >= 12:
             V_min = ((dict[a][k+11])*256 + (dict[a][k+10]))/1000
             V_max = ((dict[a][k + 13]) * 256 + (dict[a][k + 12])) / 1000
             V_avg = ((dict[a][k + 15]) * 256 + (dict[a][k + 14])) / 1000
         else:
             V_min = ''
             V_max = ''
             V_avg = ''


         wf.write('TimeStamp: {}; Event: {}; SOC: {}; HMI_Error: {}; MinTemp: {}; MaxTemp: {}; Current: {}; Capacity: {}; Min Volt: {}; Max Volt: {}; Avg Volt: {}\n'.format(
         date_time , event_id, SOC, HMI_Error, T_min, T_max, Current, Capacity, V_min, V_max, V_avg))

   

wf.close()

