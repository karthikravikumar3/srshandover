#!/usr/bin/env python
import os
import geni.portal as portal
import geni.rspec.pg as rspec
import geni.rspec.igext as IG
import geni.rspec.emulab.pnext as PN
import geni.urn as URN


tourDescription = """
### srsRAN S1 Handover w/ Open5GS

This profile allocates resources in a controlled RF environment for
experimenting with LTE handover. It deploys srsRAN on three nodes, each
consisting of a NUC5300 compute node and a B210 SDR, in our RF attenuator
matrix. One node serves as the UE, while the other two serve as "neighboring"
eNBs. Since the srsRAN EPC does not support S1 handover, the profile deploys
Open5GS on a node outside of the controlled RF environment and sets up LAN
connections between this node and both eNB nodes. A command line tool is
provided that allows you to change the amount of attenuation on the paths
between the UE and both eNBs in order to simulate mobility and trigger S1
handover events."""

tourInstructions = """

Note: this profile includes startup scripts that download, install, and
configure the required software stacks. After the experiment becomes ready, wait
until the "Startup" column on the "List View" tab indicates that the startup
scripts have finished on all of the nodes before proceeding.

#### Overview

In the following example, the `ue` will start out camped on `enb1`, with the
matrix path corresponding to the downlink between `enb1` and `ue` being
unattenuated. `enb2` will also be running, but we'll attenuate the downlink to
simulate the `ue` being out of range for the cell it provides. Then we'll
introduce some attentuation for the `enb1` downlink, simulating the UE being
closer to the edge of that cell. Finally, we'll incrementally reduce the
attenuation for the `enb2` downlink, simulating the `ue` moving closer to
`enb2`. At some point, the `ue` will start reporting better downlink signal
quality for `enb2` than for `enb1`, as indicated by RSRP measurements in srsRAN,
and eventually a handover from `enb1` to `enb2` will be triggered.

#### Instructions

After all startup scripts have finished, the Open5GS EPC will be running as a
set of services on the `cn` node. Create an SSH session on this node and start
monitoring the log for the MME service:

```
tail -f /var/log/open5gs/mme.log
```

This will allow you to verify the S1 connections between the eNBs and the EPC,
and monitor other changes.

Next, create SSH sessions on `enb1` and `enb2` and start the srsRAN eNBs:

```
# on enb1
sudo srsenb /etc/srsran/enb1.conf
```

```
# on enb2
sudo srsenb /etc/srsran/enb2.conf
```

You should see indications of S1 connection establishment for each eNB in the
MME log.

Next, use the provided command line tool identify the attenuator IDs for the eNB
downlinks, and attenuate the downlink path between `enb2` and `ue`. This tool
can be used on any node in your experiment. Here's the help output for the tool
for reference:

```
$ /local/repository/bin/atten -h
usage:
    atten -h
        show this help message
    atten -l
        list the attenuator paths under control of this experiment; each
        path is described by a line like:
            10,11:node123/node456
        indicating that attenuator IDs 10 and 11 affect the path between
        node123 and node456
    atten <id> <val>
        set the attenuation over path <id> to <val> dB
```

Use the `-l` flag to produce a list of node pairs and corresponding attenuator
IDs. Here's the output for an example experiment:

```
$ /local/repository/bin/atten -l
2,33:nuc1/nuc2
4,35:nuc1/nuc4
```

In this case, nuc1, nuc2, and nuc4 are the nodes corresponding to `ue`,
`enb1`, and `enb2` respectively. The mapping between the nodes and their IDs in
your experiment may differ from this example, but the rest of the instructions
will use this mapping. Adjust as necessary for your experiment.

Looking at the second row of the output above, the first index (4) represents
the path from the first node (nuc1,`ue`) to the second (nuc4,`enb2`), while the
second index (35) represents the path from the second node (nuc4,`enb2`) to the
first (nuc1,`ue`). In our example, this path corresponds to the LTE downlink
between `enb2` and `ue`. Attenuate this path by 40 dB initially:

```
/local/repository/bin/atten 35 40
```

Ensure that the dowlink path for `enb1` is set to 0:

```
/local/repository/bin/atten 33 0
```

Now open an SSH session on `ue` and start the srsRAN UE:

```
sudo srsue
```

The UE should immediately sync with `enb1`. Pressing `t` and `<return>` will
cause `srsue` to begin printing various metrics to `stdout`:

```
---------Signal----------|-----------------DL-----------------|-----------UL-----------
 cc  pci  rsrp  pl   cfo | mcs  snr  iter  brate  bler  ta_us | mcs   buff  brate  bler
  0    1   -72  72   401 |  14   37   0.5   1.6k    0%    0.5 |  24    0.0   8.5k    0%
  0    1   -72  72   402 |  14   36   0.5   1.6k    0%    0.5 |  24    0.0   8.5k    0%
  0    1   -72  72   403 |  14   37   0.5   1.6k    0%    0.5 |  24    0.0   8.5k    0%
  0    1   -72  72   402 |  14   37   0.5   1.6k    0%    0.5 |  24    0.0   8.5k    0%
```

The physical cell identifier (PCI) and reference signal received power (RSRP)
columns in the "Signal" section will be of interest. The PCI indicates which
cell the UE is currently attached to. This profile configures `enb1` and `enb2`
to have PCIs 1 and 2, respectively. RSRP represents the average power of
resource elements containing reference signals on the downlink. The UE reports
RSRP values for the current and neighboring cells back to the the current cell,
which decides if/when handover should occur.

In another SSH session on `ue`, start a ping process pointed at the EPC:

```
ping 10.45.0.1
```

This will keep the UE from going idle while you are adjusting gains, and allow
you to verify that the packet data connection remains intact across handover
events.

Next, add some attenuation to the downlink for `enb1`:

```
/local/repository/bin/atten 33 10
```

Observe the changes in the metrics reported by the UE. The RSRP measurements
for the current cell will drop by around 10 dB, and the UE may start reporting
measurements for the "neighbor" cell `enb2`, e.g.:

```
---------Signal----------|-Neighbour-|-----------------DL-----------------|-----------UL-----------
 cc  pci  rsrp  pl   cfo | pci  rsrp | mcs  snr  iter  brate  bler  ta_us | mcs   buff  brate  bler
  0    1   -82  82   403 |   2  -103 |  14   29   0.5   1.6k    0%    0.5 |  24    0.0   8.5k    0%
  0    1   -82  82   399 |   2  -103 |  14   30   0.5   1.6k    0%    0.5 |  24    0.0   8.5k    0%
  0    1   -82  82   402 |   2  -103 |  14   29   0.5   1.6k    0%    0.5 |  24    0.0   8.5k    0%
  0    1   -82  82   399 |   2  -103 |  14   30   0.5   1.6k    0%    0.5 |  24    0.0   8.5k    0%
```

Add some more attenuation to the `enb1` downlink:

```
/local/repository/bin/atten 33 20
```

Again, the RSRP will degrade by around 10 dB, and the UE is almost certain to
start reporting measurements for `enb2`:

```
# srsue output
---------Signal----------|-Neighbour-|-----------------DL-----------------|-----------UL-----------
 cc  pci  rsrp  pl   cfo | pci  rsrp | mcs  snr  iter  brate  bler  ta_us | mcs   buff  brate  bler
  0    1   -92  92   411 |   2  -103 |  14   20   0.5   1.6k    0%    0.5 |  24    2.0   8.5k    0%
  0    1   -92  92   409 |   2  -103 |  14   20   0.5   1.6k    0%    0.5 |  24    2.0   8.5k    0%
  0    1   -92  92   414 |   2  -103 |  14   20   0.5   1.6k    0%    0.5 |  24    2.0   8.5k    0%
  0    1   -92  92   413 |   2  -103 |  14   20   0.5   1.6k    0%    0.5 |  24    2.0   8.5k    0%
```

Next, start incrementally decreasing the attenuation for the `enb2` downlink.
Steps of 5 or 10 dB work well. Larger steps may result in a failed handover.
When you get to 20 dB attenuation for the `enb2` downlink. The RSRP measurements
will be similar for both cells:

```
/local/repository/bin/atten 35 20
```

```
# srsue output
---------Signal----------|-Neighbour-|-----------------DL-----------------|-----------UL-----------
 cc  pci  rsrp  pl   cfo | pci  rsrp | mcs  snr  iter  brate  bler  ta_us | mcs   buff  brate  bler
  0    1   -91  91   418 |   2   -91 |   5    7   0.5   1.6k    0%    0.5 |  24    0.0   8.5k    0%
  0    1   -91  91   416 |   2   -91 |   4    7   0.5   1.7k    0%    0.5 |  24    0.0   8.5k    0%
  0    1   -91  91   419 |   2   -92 |   5    7   0.5   1.6k    0%    0.5 |  24    0.0   8.5k    0%
  0    1   -91  91   422 |   2   -92 |   5    7   0.5   1.6k    0%    0.5 |  24    0.0   8.5k    0%
```

At this point, another 10 dB reduction in attenuation for the `enb2` downlink
should trigger a handover. `enb1` will indicate that it is starting an S1
handover and the UE will indicate that it has received a handover command and
attach to `enb2`:

```
# srsue output
Received HO command to target PCell=2, NCC=2
Random Access Transmission: seq=49, tti=691, ra-rnti=0x2
Random Access Complete.     c-rnti=0x48, ta=1
HO successful
  0    2   -92  92    42 |   1  -101 |   0   11   0.8    322    0%    0.5 |  12    0.0    931    0%
  0    2   -85  85  -470 |   1   -95 |   0   23   0.5     56    0%    0.5 |  24    0.0   4.3k    0%
  0    2   -81  81  -469 |   1   -93 |   7   23   0.5   1.6k    0%    0.5 |  24    0.0   8.5k    0%
---------Signal----------|-Neighbour-|-----------------DL-----------------|-----------UL-----------
 cc  pci  rsrp  pl   cfo | pci  rsrp | mcs  snr  iter  brate  bler  ta_us | mcs   buff  brate  bler
  0    2   -81  81  -471 |   1   -93 |  14   23   0.5   1.6k    0%    0.5 |  24    0.0   8.5k    0%
```

Notice that the UE now indicates that it is attached to `enb2` (PCI 2) and is
reporting measurements for `enb1` (PCI 1) as a neigbor cell. You can continue to
adjust downlink attenuation levels to trigger more handover events.

"""

BIN_PATH = "/local/repository/bin"
DEPLOY_SRS = os.path.join(BIN_PATH, "deploy-srs.sh")
DEPLOY_OPEN5GS = os.path.join(BIN_PATH, "deploy-open5gs.sh")
TUNE_CPU = os.path.join(BIN_PATH, "tune-cpu.sh")
NUC_HWTYPE = "nuc5300"
UBUNTU_1804_IMG = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU18-64-STD"
SRSLTE_IMG = "urn:publicid:IDN+emulab.net+image+PowderProfiles:U18LL-SRSLTE"


pc = portal.Context()
node_type = [
    ("d740",
     "Emulab, d740"),
    ("d430",
     "Emulab, d430")
]

pc.defineParameter("cn_node_type",
                   "Type of compute node for Open5GS CN",
                   portal.ParameterType.STRING,
                   node_type[0],
                   node_type)

pc.defineParameter("enb1_node", "PhantomNet NUC+B210 for first eNodeB",
                   portal.ParameterType.STRING, "nuc2", advanced=True,
                   longDescription="Specific eNodeB node to bind to.")

pc.defineParameter("enb2_node", "PhantomNet NUC+B210 for second eNodeB",
                   portal.ParameterType.STRING, "nuc4", advanced=True,
                   longDescription="Specific eNodeB node to bind to.")

pc.defineParameter("ue_node", "PhantomNet NUC+B210 for UE",
                   portal.ParameterType.STRING, "nuc1", advanced=True,
                   longDescription="Specific UE node to bind to.")

params = pc.bindParameters()
pc.verifyParameters()
request = pc.makeRequestRSpec()

cn = request.RawPC("cn")
cn.hardware_type = params.cn_node_type
cn.disk_image = UBUNTU_1804_IMG
cn.addService(rspec.Execute(shell="bash", command=DEPLOY_OPEN5GS))
cn_s1_if = cn.addInterface("cn_s1_if")
cn_s1_if.addAddress(rspec.IPv4Address("192.168.1.1", "255.255.255.0"))

ue = request.RawPC("ue")
ue.hardware_type = NUC_HWTYPE
ue.component_id = params.ue_node

ue.disk_image = SRSLTE_IMG
ue.Desire("rf-controlled", 1)
ue_enb1_rf = ue.addInterface("ue_enb1_rf")
ue_enb2_rf = ue.addInterface("ue_enb2_rf")
ue.addService(rspec.Execute(shell="bash", command=DEPLOY_SRS))
ue.addService(rspec.Execute(shell="bash", command=TUNE_CPU))

enb1 = request.RawPC("enb1")
enb1.hardware_type = NUC_HWTYPE
enb1.component_id = params.enb1_node

enb1.disk_image = SRSLTE_IMG
enb1_s1_if = enb1.addInterface("enb1_s1_if")
enb1_s1_if.addAddress(rspec.IPv4Address("192.168.1.2", "255.255.255.0"))
enb1_x2_if = enb1.addInterface("enb1_x2_if")
enb1_x2_if.addAddress(rspec.IPv4Address("192.168.1.20", "255.255.255.0"))
enb1.Desire("rf-controlled", 1)
enb1_ue_rf = enb1.addInterface("enb1_ue_rf")
enb1.addService(rspec.Execute(shell="bash", command=DEPLOY_SRS))
enb1.addService(rspec.Execute(shell="bash", command=TUNE_CPU))

enb2 = request.RawPC("enb2")
enb2.hardware_type = NUC_HWTYPE
enb2.component_id = params.enb2_node

enb2.disk_image = SRSLTE_IMG
enb2_s1_if = enb2.addInterface("enb2_s1_if")
enb2_s1_if.addAddress(rspec.IPv4Address("192.168.1.3", "255.255.255.0"))
enb2_x2_if = enb2.addInterface("enb2_x2_if")
enb2_x2_if.addAddress(rspec.IPv4Address("192.168.1.30", "255.255.255.0"))
enb2.Desire("rf-controlled", 1)
enb2_ue_rf = enb2.addInterface("enb2_ue_rf")
enb2.addService(rspec.Execute(shell="bash", command=DEPLOY_SRS))
enb2.addService(rspec.Execute(shell="bash", command=TUNE_CPU))

# Create S1 links between eNodeBs and CN
link = request.LAN("lan")
link.addInterface(cn_s1_if)
link.addInterface(enb1_s1_if)
link.addInterface(enb2_s1_if)
link.link_multiplexing = True
link.vlan_tagging = True
link.best_effort = True
link1 = request.LAN("lan1")
link1.addInterface(enb1_x2_if)
link1.addInterface(enb2_x2_if)
link1.link_multiplexing = True
link1.vlan_tagging = True
link1.best_effort = True

# Create RF links between the UE and eNodeBs
rflink1 = request.RFLink("rflink1")
rflink1.addInterface(enb1_ue_rf)
rflink1.addInterface(ue_enb1_rf)

rflink2 = request.RFLink("rflink2")
rflink2.addInterface(enb2_ue_rf)
rflink2.addInterface(ue_enb2_rf)

tour = IG.Tour()
tour.Description(IG.Tour.MARKDOWN, tourDescription)
tour.Instructions(IG.Tour.MARKDOWN, tourInstructions)
request.addTour(tour)

pc.printRequestRSpec(request)
