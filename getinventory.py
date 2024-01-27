#! /usr/bin/python3
# Author: Ramazan Ozbilen
# All rights belong to Michael Jackson, please get in contact with him directly.
import requests,json,getopt,sys
from datetime import datetime
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def usage():
    print("\nOptions: \n-h: help \n-l: device list \n-u: username \n-p: password \n-c: command list \n\nUsage: getinventory.py -u ramazan -p password -l device-list.txt -c command-list.txt\n")
    return

now = datetime.now()
dt = now.strftime("%d/%m/%Y %H:%M:%S")
rf = "/redfish/v1/"

try:
    opts, args = getopt.getopt(sys.argv[1:], "hl:u:p:c:d:")
except getopt.GetoptError as err:
    print(str(err))
    usage()
    sys.exit(2)

for o, a in opts:
    if o == "-l":
        devicefile = a
    elif o in ("-h"):
        usage()
        sys.exit()
    elif o in ("-u"):
        username = a
    elif o in ("-p"):
        password = a
    elif o in ("-c"):
        commandfile = a
    elif o in ("-d"):
        debug = a
    else:
        assert False, "unhandled option! Consider using -h option"
        

f1 = open(devicefile,"r")
f2 = open(commandfile,"r")

devs = f1.readlines()
cmds = f2.readlines()

try:
    isDebugEnabled = True if debug == "yes" else False
    print("Debug enabled: ", isDebugEnabled)
except (RuntimeError, TypeError, NameError):
    isDebugEnabled = False

def parser(ba,ha,r):
    output = open(ba + ".out", "a")
    output.write("\n\nDateTime: "+dt+"\n"+'-'*60+"\nCommand: "+r.replace(',','-')+"\n"+'-'*60+"\n")
    output.writelines(ha)
    output.write("\n"+'#'*60)
    if isDebugEnabled:
        print("Success! written to: ", ba+".out")
        print('#'*60) 

def debugger(a):
    if isDebugEnabled:
        for i in a:
            if "\n" in i:
                print(i.replace('\n', ''))
            else:
                print(i)        
        
        
def makerequest(x,y):
    try:
        system = requests.get('https://'+x+y,verify=False,auth=(username,password))
    except requests.exceptions.RequestException as e:
        print ("\nCONNECTION ERROR!",x,"is not reachable. Please check the following error log the details:\n\n")
        raise SystemExit(e)
        
    return system.json()    

def getinventory(iq):
    for ip in iq:
        ip = ip.rstrip()
        for cmd in cmds:
            cmd = cmd.rstrip()
            cmdType = cmd.split(',')[0]
            if cmdType == "POWERCONTROL":
                api = rf+'Chassis/System.Embedded.1/Power/PowerControl'
                systemData = makerequest(ip,api)
                stdOut = "Consumed power:      {}".format(systemData[u'PowerConsumedWatts']),\
				       "\nAverage reading:     {}".format(systemData[u'PowerMetrics'][u'AverageConsumedWatts']),\
				       "\nMax reading:         {}".format(systemData[u'PowerMetrics'][u'MaxConsumedWatts']),\
				       "\nMin reading:         {}".format(systemData[u'PowerMetrics'][u'MinConsumedWatts'])
                debugger(stdOut)
                parser(ip,stdOut,cmd)
            
            elif cmdType == "PSU":
                psuSlot = cmd.split(',')[1]
                api = rf+'Chassis/System.Embedded.1/Power#/PowerSupplies/'+str(psuSlot)
                systemData = makerequest(ip,api)
                stdOut = "PartNumber:          {}".format(systemData[u'PowerSupplies'][int(psuSlot)][u'PartNumber']),\
                       "\nSerialNumber:        {}".format(systemData[u'PowerSupplies'][int(psuSlot)][u'SerialNumber']),\
                       "\nModel:               {}".format(systemData[u'PowerSupplies'][int(psuSlot)][u'Model']),\
                       "\nHealth:              {}".format(systemData[u'PowerSupplies'][int(psuSlot)][u'Status'][u'Health'])
                debugger(stdOut)
                parser(ip,stdOut,cmd)
            
            elif cmdType == "DISK":
                diskBay = cmd.split(',')[1]
                api = rf+'Systems/System.Embedded.1/Storage/RAID.Slot.6-1/Drives/Disk.Bay.'+str(diskBay)+':Enclosure.Internal.0-1:RAID.Slot.6-1'
                systemData = makerequest(ip,api)
                stdOut = "PartNumber:          {}".format(systemData[u'PartNumber']),\
                       "\nSerialNumber:        {}".format(systemData[u'SerialNumber']),\
                       "\nModel:               {}".format(systemData[u'Model']),\
                       "\nHealth:              {}".format(systemData[u'Status'][u'Health'])
                debugger(stdOut)
                parser(ip,stdOut,cmd)
            
            elif cmdType == "NIC":
                nicSlot = cmd.split(',')[1]
                nicPort = cmd.split(',')[2]
                api = rf+'Chassis/System.Embedded.1/NetworkAdapters/NIC.Slot.'+str(nicSlot)+'/NetworkPorts/NIC.Slot.'+str(nicSlot)+'-'+str(nicPort)
                systemData = makerequest(ip,api)
                linkState = systemData[u'LinkStatus']
                api = systemData[u'NetDevFuncMaxBWAlloc'][0][u'NetworkDeviceFunction'][u'@odata.id']
                systemData = makerequest(ip,api)
                stdOut = "PartNumber:          {}".format(systemData[u'Oem'][u'Dell'][u'DellNIC'][u'PartNumber']),\
                       "\nSerialNumber:        {}".format(systemData[u'Oem'][u'Dell'][u'DellNIC'][u'SerialNumber']),\
                       "\nProductName:         {}".format(systemData[u'Oem'][u'Dell'][u'DellNIC'][u'ProductName']),\
                       "\nModel:               {}".format(systemData[u'Oem'][u'Dell'][u'DellNIC'][u'IdentifierType']),\
                       "\nLinkStatus:          {}".format(linkState)
                debugger(stdOut)
                parser(ip,stdOut,cmd)
            
            elif cmdType == "CPU":
                api = rf+'Systems/System.Embedded.1/Bios'
                systemData = makerequest(ip,api) 
                stdOut = "CPU1:                {}".format(systemData[u'Attributes'][u'Proc1Brand']),\
                       "\n#ofCPU1Cores:        {}".format(systemData[u'Attributes'][u'Proc1NumCores']),\
                       "\nCPU2:                {}".format(systemData[u'Attributes'][u'Proc2Brand']),\
                       "\n#ofCPU2Cores:        {}".format(systemData[u'Attributes'][u'Proc1NumCores']),\
                       "\nCPUCoreSpeed:        {}".format(systemData[u'Attributes'][u'ProcCoreSpeed']),\
                       "\nTurboMode:           {}".format(systemData[u'Attributes'][u'ProcTurboMode']),\
                       "\nCState:              {}".format(systemData[u'Attributes'][u'ProcCStates']),\
                       "\nC1E:                 {}".format(systemData[u'Attributes'][u'ProcC1E']),\
                       "\nUncoreFrequency      {}".format(systemData[u'Attributes'][u'UncoreFrequency']),\
                       "\nCPUPowerPerf         {}".format(systemData[u'Attributes'][u'ProcPwrPerf']),\
                       "\nCpuInterBusLinkPower {}".format(systemData[u'Attributes'][u'CpuInterconnectBusLinkPower'])
                debugger(stdOut)
                parser(ip,stdOut,cmd)
                
            elif cmdType == "MEMORY":
                api = rf+'Systems/System.Embedded.1/Bios'
                systemData = makerequest(ip,api)
                stdOut = "MemorySize:          {}".format(systemData[u'Attributes'][u'SysMemSize']),\
                       "\nMemoryType:          {}".format(systemData[u'Attributes'][u'SysMemType']),\
                       "\nMemorySpeed:         {}".format(systemData[u'Attributes'][u'SysMemSpeed']),\
                       "\nMemoryFrequency:     {}".format(systemData[u'Attributes'][u'MemFrequency'])
                debugger(stdOut)
                parser(ip,stdOut,cmd)

            elif cmdType == "BIOS":
                api = rf+'Systems/System.Embedded.1/Bios'
                systemData = makerequest(ip,api)
                stdOut = "ServiceTag:          {}".format(systemData[u'Attributes'][u'SystemServiceTag']),\
                       "\nBiosVersion:         {}".format(systemData[u'Attributes'][u'SystemBiosVersion']),\
                       "\nMeVersion:           {}".format(systemData[u'Attributes'][u'SystemMeVersion']),\
                       "\nEnergy/PerfBias:     {}".format(systemData[u'Attributes'][u'EnergyPerformanceBias']),\
                       "\nPCIeASPM:            {}".format(systemData[u'Attributes'][u'PcieAspmL1'])
                debugger(stdOut)                      
                parser(ip,stdOut,cmd)                                


          


        
        
getinventory(devs)
f1.close()
f2.close()



