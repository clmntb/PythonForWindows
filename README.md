# PythonForWindows

PythonForWindows is a base of code aimed to make interaction with `Windows` (on X86/X64) easier (for both 32 and 64 bits Python).
Its goal is to offer abstractions around some of the OS features in a (I hope) pythonic way.
It also tries to make the barrier between python and native execution thinner in both ways.
There is no external dependencies but it relies heavily on the `ctypes` module.


Some of this code is clean (IMHO) and some parts are just a wreck that works for now.
Let's say that the codebase evolves with my needs and my curiosity.

Complete online documentation is available [here][ONLINE_DOC]
You can find some examples of code in the [samples directory][SAMPLE_DIR] or [online][ONLINE_SAMPLE].

Parts of PythonForWindows are used in the [LKD project][LKD_GITHUB].

If you have any issue, question, suggestion do not hesitate to contact me.
I am always glad to have feedbacks from people using this project.

## Installation

You can install PythonForWindows using the ``setup.py`` script:

``
python setup.py install
``

Note that PythonForWindows only support Python2 at the moment.

## Overview

### Processes / Threads

PythonForWindows offers objects around processes and allows you to:

- Retrieve basic process informations (pid, name, ppid, bitness, ...)
- Perform basic interprocess operation (allocation, create thread, read/write memory)
- Explore the PEB (Process Environment Block)
- Execute `native` and `Python` code in the context of a process.

I try my best to make those features available for every cross-bitness processes (`32 <-> 64` in both ways).
This involves relying on non-documented `Windows` functions/behaviours and also injecting code in the 64bits world of a `Syswow64` process.
All those operations are also available for the `current_process`.

You can also make some operation on threads (suspend/resume/wait/get(or set) context/ kill)

```python
>>> import windows
>>> windows.current_process.bitness
32
>>> windows.current_process.token.integrity
SECURITY_MANDATORY_MEDIUM_RID(0x2000L)
>>> calc = [p for p in windows.system.processes if p.name == "calc.exe"][0]
>>> calc
<WinProcess "calc.exe" pid 6960 at 0x37391f0>
>>> calc.bitness
64
>>> calc.peb.modules[:3]
[<RemoteLoadedModule64 "calc.exe" at 0x3671e90>, <RemoteLoadedModule64 "ntdll.dll" at 0x3671030>, <RemoteLoadedModule64 "kernel32.dll" at 0x3671080>]
>>> k32 = calc.peb.modules[2]
>>> hex(k32.pe.exports["CreateFileW"])
'0x7ffee6761550L'
>>> calc.threads[0]
<WinThread 3932 owner "calc.exe" at 0x3646350>
>>> hex(calc.threads[0].context.Rip)
'0x7ffee68b54b0L'
>>> calc.execute_python("import os")
True
>>> calc.execute_python("exit(os.getpid() + 1)")
# execute_python raise if process died
Traceback (most recent call last):
...
WindowsError: <WinProcess "calc.exe" pid 6960 (DEAD) at 0x37391f0> died during execution of python command
>>> calc
<WinProcess "calc.exe" pid 6960 (DEAD) at 0x37391f0>
>>> calc.exit_code
6961L
```

### System information

Information about the Windows computer running the script are available through the `windows.system` object.

```python
>>> windows.system
<windows.winobject.system.System object at 0x03FEED10>
>>> windows.system.bitness
64
>>> windows.system.computer_name
'DESKTOP-VKUGISR'
>>> windows.system.product_type
VER_NT_WORKSTATION(0x1L)
>>> windows.system.version
(10, 0)
>>> windows.system.version_name
'Windows 10'
>>> windows.system.build_number
'10.0.15063.608'

# windows.system also contains dynamic lists about processes / threads / handles / ...
>>> windows.system.handles[-2:]
[<Handle value=<0x5cc> in process pid=14360>, <Handle value=<0x28e4> in process pid=14360>]
>>> windows.system.processes[:2]
[<WinProcess "[System Process]" pid 0 at 0x433f7d0>, <WinProcess "System" pid 4 at 0x433fd30>]
>>> windows.system.logicaldrives[0]
<LogicalDrive "C:\" (DRIVE_FIXED)>
>>> windows.system.services[23]
<ServiceA "Appinfo" SERVICE_RUNNING(0x4L)>

```

### IAT Hook

This codebase is born from my need to have IAT hooks implemented in Python.
So the features is present (See [online documentation][ONLINE_IATHOOK] about IAT hooks).


### Winproxy

A wrapper around some Windows functions. Arguments name and order are the same,
but some have default values and the functions raise exception on call error (I don't like `if` around all my call).

```python
>>> import windows
>>> help(windows.winproxy.VirtualAlloc)
# Help on function VirtualAlloc in module windows.winproxy:
# VirtualAlloc(lpAddress=0, dwSize=NeededParameter, flAllocationType=MEM_COMMIT(0x1000L), flProtect=PAGE_EXECUTE_READWRITE(0x40L))
#     Errcheck:
#     raise Kernel32Error if result is 0

# Positional arguments
>>> windows.winproxy.VirtualAlloc(0, 0x1000)
34537472

# Keyword arguments
>>> windows.winproxy.VirtualAlloc(dwSize=0x1000)
34603008

# NeededParameter must be provided
>>> windows.winproxy.VirtualAlloc()
"""
Traceback (most recent call last):
File "<stdin>", line 1, in <module>
File "windows\winproxy.py", line 264, in VirtualAlloc
    return VirtualAlloc.ctypes_function(lpAddress, dwSize, flAllocationType, flProtect)
File "windows\winproxy.py", line 130, in perform_call
    raise TypeError("{0}: Missing Mandatory parameter <{1}>".format(self.func_name, param_name))
TypeError: VirtualAlloc: Missing Mandatory parameter <dwSize>
"""

# Error raises exception
>>> windows.winproxy.VirtualAlloc(dwSize=0xffffffff)
"""
Traceback (most recent call last):
File "<stdin>", line 1, in <module>
File "windows\winproxy.py", line 264, in VirtualAlloc
    return VirtualAlloc.ctypes_function(lpAddress, dwSize, flAllocationType, flProtect)
File "windows\winproxy.py", line 133, in perform_call
    return self._cprototyped(*args)
File "windows\winproxy.py", line 59, in kernel32_error_check
    raise Kernel32Error(func_name)
windows.winproxy.Kernel32Error: VirtualAlloc: [Error 8] Not enough storage is available to process this command.
"""
```


### Native execution

To make the barrier between `native` and `Python` code thinner,
PythonForWindows allows you to create native function callable from Python (thanks to `ctypes`) and also embed
a simple x86/x64 assembler.

```python
>>> import windows.native_exec.simple_x86 as x86
>>> code = x86.MultipleInstr()
>>> code += x86.Mov("EAX", 41)
>>> code += x86.Inc("EAX")
>>> code += x86.Ret()
>>> code.get_code()
'\xc7\xc0)\x00\x00\x00@\xc3'
# Create a function that takes no parameters and return an uint
>>> f = windows.native_exec.create_function(code.get_code(), [ctypes.c_uint])
>>> f()
42L
# Assemblers can also be used in a more standard way
>>> x86.assemble("cmp edi, 0; jnz :end; mov eax, 1; label :end; ret")
'\x81\xff\x00\x00\x00\x00u\x06\xc7\xc0\x01\x00\x00\x00\xc3'
```

### Wintrust

To easily script some signature check script, PythonForWindows implements some wrapper functions around ``wintrust.dll``

```python
>>> import windows.wintrust
>>> windows.wintrust.is_signed(r"C:\Windows\system32\ntdll.dll")
True
>>> windows.wintrust.is_signed(r"C:\Windows\system32\python27.dll")
False
>>> windows.wintrust.full_signature_information(r"C:\Windows\system32\ntdll.dll")
SignatureData(signed=True,
    catalog=u'C:\\Windows\\system32\\CatRoot\\{F750E6C3-38EE-11D1-85E5-00C04FC295EE}\\Package_35_for_KB3128650~31bf3856ad364e35~amd64~~6.3.1.2.cat',
    catalogsigned=True, additionalinfo=0L)
>>> windows.wintrust.full_signature_information(r"C:\Windows\system32\python27.dll")
SignatureData(signed=False, catalog=None, catalogsigned=False, additionalinfo=TRUST_E_NOSIGNATURE(0x800b0100L))
```

### WMI

To extract/play with even more information about the system, PythonForWindows is able to perform WMI request.

```python
>>> import windows
>>> windows.system.wmi.select
<bound method WmiRequester.select of <windows.winobject.wmi.WmiRequester object at 0x036BA590>>
>>> windows.system.wmi.select("Win32_Process", ["Name", "Handle"])[:4]
[{'Handle': u'0', 'Name': u'System Idle Process'}, {'Handle': u'4', 'Name': u'System'}, {'Handle': u'412', 'Name': u'smss.exe'}, {'Handle': u'528', 'Name': u'csrss.exe'}]
# Get WMI data for current process
>>> wmi_cp = [p for p in windows.system.wmi.select("Win32_Process") if int(p["Handle"]) == windows.current_process.pid][0]
>>> wmi_cp["CommandLine"], wmi_cp["HandleCount"]
(u'"C:\\Python27\\python.exe"', 227)
```

### Registry

The project also contains some wrapping classes around `_winreg` for simpler use.

```python
>>> import windows
>>> from windows.generated_def import KEY_WRITE, KEY_READ, REG_QWORD
>>> registry = windows.system.registry
>>> cuuser_software = registry(r'HKEY_CURRENT_USER\Software')
>>> cuuser_software
<PyHKey "HKEY_CURRENT_USER\Software">
>>> cuuser_software.sam
KEY_READ(0x20019L)
# Explore subkeys
>>> cuuser_software.subkeys[:3]
[<PyHKey "HKEY_CURRENT_USER\Software\7-Zip">, <PyHKey "HKEY_CURRENT_USER\Software\AppDataLow">, <PyHKey "HKEY_CURRENT_USER\Software\Audacity">]
>>> tstkey = registry('HKEY_CURRENT_USER\TestKey',  KEY_WRITE | KEY_READ)
# Get / Set individual value
>>> tstkey["VALUE"] = 'a_value_for_my_key'
>>> tstkey["VALUE"]
KeyValue(name='VALUE', value=u'a_value_for_my_key', type=1)
>>> tstkey["MYQWORD"] = (123456789987654321, REG_QWORD)  # Default is REG_DWORD for int/long
>>> tstkey["MYQWORD"]
KeyValue(name='MYQWORD', value=123456789987654321L, type=11)
# Explore Values
>>> tstkey.values
[KeyValue(name='MYQWORD', value=123456789987654321L, type=11), KeyValue(name='VALUE', value=u'a_value_for_my_key', type=1)]
```

### Object manager

PythonForWindows uses the native Windows NT API to display some information about the object in the Object Manager's name space.
Just like the well-known tools ``winobj.exe``

```python
>>> windows.system.object_manager.root
<KernelObject "\" (type="Directory")>
# The objects of type "Directory" can be acceded just like a dict
>>> list(windows.system.object_manager.root)[:3]
[u'PendingRenameMutex', u'ObjectTypes', u'storqosfltport']
# Find an object by its path
>>> windows.system.object_manager["KnownDLLs\\kernel32.dll"]
<KernelObject "\KnownDLLs\kernel32.dll" (type="Section")>
>>> k32 = windows.system.object_manager["KnownDLLs\\kernel32.dll"]
>>> k32.name, k32.fullname, k32.type
('kernel32.dll', '\\KnownDLLs\\kernel32.dll', u'Section')
# Follow SymbolicLink object
>>> windows.system.object_manager["\\KnownDLLs\\KnownDLLPath"]
<KernelObject "\KnownDLLs\KnownDLLPath" (type="SymbolicLink")>
>>> windows.system.object_manager["\\KnownDLLs\\KnownDLLPath"].target
u'C:\\WINDOWS\\System32'
```

### Scheduled Task

The ``windows.system.task_scheduler`` object allows to query and create scheduled task.

**This part is still in developpement and the API may evolve**

```python
>>> windows.system.task_scheduler
<TaskService at 0x4774670>
>>> windows.system.task_scheduler.root
<TaskFolder "\" at 0x4774710>
>>> task = windows.system.task_scheduler.root.tasks[2]
>>> task
<Task "DemoTask" at 0x47748f0>
>>> task.name
u'DemoTask'
# Explore task actions
>>> task.definition.actions[1]
<ExecAction at 0x4774800>
>>> task.definition.actions[1].path
u'c:\\windows\\python\\python.exe'
>>> task.definition.actions[1].arguments
u'yolo.py --test'
```

### Event logs

The ``windows.system.event_log`` object allows to query event logs.

**This part is still in developpement and the API may evolve**

```python
>>> windows.system.event_log
<windows.winobject.event_log.EvtlogManager object at 0x04A78270>
# Find a channel by its name
>>> chan = windows.system.event_log["Microsoft-Windows-Windows Firewall With Advanced Security/Firewall"]
>>> chan
<EvtChannel "Microsoft-Windows-Windows Firewall With Advanced Security/Firewall">
# Open .evtx files
>>> windows.system.event_log["test.evtx"]
<EvtFile "test.evtx">
# Query a channel for all events
>>> chan.query().all()[:2]
[<EvtEvent id="2004" time="2018-07-12 07:44:08.081504">, <EvtEvent id="2006" time="2018-07-12 07:57:59.806938">]
# Query a channel for some ids
>>> chan.query(ids=2004).all()[:2]
[<EvtEvent id="2004" time="2018-07-12 07:44:08.081504">, <EvtEvent id="2004" time="2018-07-12 07:57:59.815156">]
# Query a channel via XPATH
>>> evt = chan.query("Event/EventData[Data='Netflix']").all()[0]
# Explore event information
>>> evt
<EvtEvent id="2006" time="2018-07-17 10:32:39.160423">
>>> evt.data
{u'ModifyingUser': 69828304, u'RuleName': u'Netflix', u'ModifyingApplication': ...}
```

### ALPC-RPC

#### ALPC

Classes around **A**dvanced **L**ocal **P**rocedure **C**all (**ALPC**) syscalls allows to simply
write client and server able to send **ALPC** messages.

```python
>>> import windows.alpc
# Test server juste reply to each message with "REQUEST '{msg_data}' RECEIVED"
>>> client = windows.alpc.AlpcClient(r"\RPC Control\PythonForWindowsTESTPORT")
>>> response = client.send_receive("Hello world !")
>>> response
<windows.alpc.AlpcMessage object at 0x04C0D5D0>
>>> response.data
"REQUEST 'Hello world !' RECEIVED"
```

Full client/server code for this example is available is the [ALPC samples][ONLINE_SAMPLE_ALPC] along with a more complex example.


#### RPC

An RPC-Client based using **ALPC** communication is also integred

```python
# Server (port ALPC '\RPC Control\HelloRpc') offers:
# Interface '41414141-4242-4343-4444-45464748494a' version 1.0
#   Method 1 -> int Add(int a, int b) -> return a + b
# This Test server is a real RPC Server using rpcrt4.dll and compiled with VS2015.

>>> import windows.rpc
>>> from windows.rpc import ndr
>>> client = windows.rpc.RPCClient(r"\RPC Control\HelloRpc")
>>> client
<windows.rpc.client.RPCClient object at 0x0411E130>
>>> iid = client.bind("41414141-4242-4343-4444-45464748494a")
>>> ndr_params = ndr.make_parameters([ndr.NdrLong] * 2)
# NDR pack + Make RPC call to method 1.
>>> resp = client.call(iid, 1, ndr_params.pack([41414141, 1010101]))
# Unpack the NDR response
>>> result = ndr.NdrLong.unpack(ndr.NdrStream(resp))
>>> result
42424242
```

A sample with the **U**ser **A**ccount **C**ontrol (**UAC**) and one with `lsasrv.dll` are available in the [RPC samples][ONLINE_SAMPLE_RPC].


### Debugger

PythonForWindows provides a standard debugger to debug other processes.

```python
import windows
import windows.debug
import windows.test
import windows.native_exec.simple_x86 as x86

from windows.test import pop_calc_32
from windows.generated_def import EXCEPTION_ACCESS_VIOLATION

class MyDebugger(windows.debug.Debugger):
    def on_exception(self, exception):
        code = exception.ExceptionRecord.ExceptionCode
        addr = exception.ExceptionRecord.ExceptionAddress
        print("Got exception {0} at 0x{1:x}".format(code, addr))
        if code == EXCEPTION_ACCESS_VIOLATION:
            print("Access Violation: kill target process")
            self.current_process.exit()

calc = windows.test.pop_calc_32(dwCreationFlags=DEBUG_PROCESS)
d = MyDebugger(calc)
calc.execute(x86.assemble("int3; mov [0x42424242], EAX; ret"))
d.loop()

## Ouput ##
Got exception EXCEPTION_BREAKPOINT(0x80000003L) at 0x77e13c7d
Got exception EXCEPTION_BREAKPOINT(0x80000003L) at 0x230000
Got exception EXCEPTION_ACCESS_VIOLATION(0xc0000005L) at 0x230001
Access Violation: kill target process
```

The debugger handles

* Standard breakpoint ``int3``
* Hardware Execution breakpoint ``DrX``
* Memory breakpoint ``virtual protect``


#### LocalDebugger

You can also debug your own process (or debug a process by injection) via the LocalDebugger.

The LocalDebugger is an abstraction around Vectored Exception Handler (VEH)

```python
import windows
from windows.generated_def.winstructs import *
import windows.native_exec.simple_x86 as x86

class SingleSteppingDebugger(windows.debug.LocalDebugger):
    SINGLE_STEP_COUNT = 4
    def on_exception(self, exc):
        code = self.get_exception_code()
        context = self.get_exception_context()
        print("EXCEPTION !!!! Got a {0} at 0x{1:x}".format(code, context.pc))
        self.SINGLE_STEP_COUNT -= 1
        if self.SINGLE_STEP_COUNT:
            return self.single_step()
        return EXCEPTION_CONTINUE_EXECUTION

class RewriteBreakpoint(windows.debug.HXBreakpoint):
    def trigger(self, dbg, exc):
        context = dbg.get_exception_context()
        print("GOT AN HXBP at 0x{0:x}".format(context.pc))
        # Rewrite the infinite loop with 2 nop
        windows.current_process.write_memory(self.addr, "\x90\x90")
        # Ask for a single stepping
        return dbg.single_step()


d = SingleSteppingDebugger()
# Infinite loop + nop + ret
code = x86.assemble("label :begin; jmp :begin; nop; ret")
func = windows.native_exec.create_function(code, [PVOID])
print("Code addr = 0x{0:x}".format(func.code_addr))
# Create a thread that will infinite loop
t = windows.current_process.create_thread(func.code_addr, 0)
# Add a breakpoint on the infinite loop
d.add_bp(RewriteBreakpoint(func.code_addr))
t.wait()
print("Done!")

## Output ##

Code addr = 0x6a0002
GOT AN HXBP at 0x6a0002
EXCEPTION !!!! Got a EXCEPTION_SINGLE_STEP(0x80000004L) at 0x6a0003
EXCEPTION !!!! Got a EXCEPTION_SINGLE_STEP(0x80000004L) at 0x6a0004
EXCEPTION !!!! Got a EXCEPTION_SINGLE_STEP(0x80000004L) at 0x6a0005
EXCEPTION !!!! Got a EXCEPTION_SINGLE_STEP(0x80000004L) at 0x770c7c04
Done!

```

The local debugger handles

* Standard breakpoint ``int3``
* Hardware Execution breakpoint ``DrX``


### Security

You can access security information about Windows securable objects with the help of the security module.

```python
import windows.winproxy as winproxy
import windows.security as security
from windows.generated_def import *

# The main object you want to manipulate is security.EPSECURITY_DESCRIPTOR
# It can be instanciated from several objects

## SDDL Strings https://docs.microsoft.com/en-us/windows/desktop/secauthz/security-descriptor-string-format
SDDL = "O:LAG:S-1-5-32-544D:AI(A;OICIID;FA;;;SY)(A;OICIID;FA;;;BA)S:AI(AU;OICISA;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;LA)(AU;OICIFA;DCLCRPCR;;;LA)"
print "# Instanciating of the security descriptor from the SDDL"
pSecurityDescriptor = security.EPSECURITY_DESCRIPTOR.from_string(SDDL)
print "Security descriptor is valid: ", pSecurityDescriptor.valid
print "pSecurityDescriptor.owner: ", pSecurityDescriptor.owner
print

## HANDLES
## The object type enum is defined here : https://docs.microsoft.com/fr-fr/windows/desktop/api/accctrl/ne-accctrl-_se_object_type
print "# Instanciating of the security descriptor from a handle to the lsass.exe file" 
handle = winproxy.CreateFileA('C:\\Windows\\System32\\lsass.exe', GENERIC_READ, FILE_SHARE_READ, None, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL)
pSecurityDescriptor = security.EPSECURITY_DESCRIPTOR.from_handle(handle, object_type=SE_FILE_OBJECT) # You need to provide the object type behind the handle
winproxy.CloseHandle(handle)
print "pSecurityDescriptor.owner: ", pSecurityDescriptor.owner.lookup() # This should be owner by 'NT SERVICE\TrustedInstaller' 
print

## NAME
## The object type enum is defined here : https://docs.microsoft.com/fr-fr/windows/desktop/api/accctrl/ne-accctrl-_se_object_type
print "# Instanciating of the security descriptor from the name of a registry key"
pSecurityDescriptor = security.EPSECURITY_DESCRIPTOR.from_name('CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run', object_type=SE_REGISTRY_KEY)
print "pSecurityDescriptor.owner: ", pSecurityDescriptor.owner # This should be owner by 'S-1-5-18' 
print

## ACCESS RIGHT
## If you instanciate the security descriptor from a windows object, you might want to access the SACL
## You must have the 'SeSecurityPrivilege' privilege on you process, either you already have it or you can enable the privilege
from windows.utils import enable_privilege
print "# Enabling SeSecurityPrivilege privilege"
enable_privilege("SeSecurityPrivilege", True) # You need admin access for this to work
print "# Instanciating of the security from a service name"
pSecurityDescriptor = security.EPSECURITY_DESCRIPTOR.from_name('Spooler', object_type=SE_SERVICE, desired_access=SACL_SECURITY_INFORMATION) 
print "len(pSecurityDescriptor.sacl) : ", len(pSecurityDescriptor.sacl) 
print "repr(pSecurityDescriptor.sacl[0]) : "
print repr(pSecurityDescriptor.sacl[0]) # SACLs and DACLs act like lists, are iterable and indexable


## OUTPUT ##


# Instanciating of the security descriptor from the SDDL
Security descriptor is valid:  True
pSecurityDescriptor.owner:  S-1-5-21-2339421519-2002173573-4286560122-500

# Instanciating of the security descriptor from a handle to the lsass.exe file
pSecurityDescriptor.owner:  NT SERVICE\TrustedInstaller

# Instanciating of the security descriptor from the name of a registry key
pSecurityDescriptor.owner:  S-1-5-18

# Enabling SeSecurityPrivilege privilege
# Instanciating of the security from a service name
len(pSecurityDescriptor.sacl) :  1
repr(pSecurityDescriptor.sacl[0]) :
<ACE AceType: SYSTEM_AUDIT_ACE_TYPE(0x2L) - AceFlags: [FAILED_ACCESS_ACE_FLAG(0x80L)]
        Mask: [ADS_RIGHT_DS_CREATE_CHILD(0x1L), ADS_RIGHT_DS_DELETE_CHILD(0x2L), ADS_RIGHT_ACTRL_DS_LIST(0x4L), ADS_RIGHT_DS_SELF(0x8L), ADS_RIGHT_DS_READ_PROP(0x10L), ADS_RIGHT_DS_WRITE_PROP(0x20L), ADS_RIGHT_DS_DELETE_TREE(0x40L), ADS_RIGHT_DS_LIST_OBJECT(0x80L), ADS_RIGHT_DS_CONTROL_ACCESS(0x100L), ADS_RIGHT_DELETE(0x10000L), ADS_RIGHT_READ_CONTROL(0x20000L), ADS_RIGHT_WRITE_DAC(0x40000L), ADS_RIGHT_WRITE_OWNER(0x80000L)]
        Sid: S-1-1-0
>
```

### LDAP

You can access ldap services with PythonForWindows.

```python
import getpass
from windows.generated_def import *
from windows.ldap.ldap_connection import EPLDAP


LDAP_SERVER = 'my.domain.local'
LDAP_USERNAME = 'user'
LDAP_PASSWORD = getpass.getpass('Password: ')
LDAP_DOMAIN = 'DOMAIN'

# LDAP connections are context managers to help with cleanup when the access is not needed anymore
with EPLDAP.get_connection(LDAP_SERVER) as conn
    conn.bind(LDAP_USERNAME, LDAP_PASSWORD, LDAP_DOMAIN) # LDAP bind with negociate authentication technique 
                                                         # You can use simple authentication which does not use
                                                         # sasl for easy debugging
    # Setup the list of attributes you want to get from the LDAP.
    # Set to None for all attributes.
    attributes = ['cn', 'objectClass']
    
    # Simple search that uses the kwargs to build an AND filter
    user = conn.find_one(sAMAccountName='user2', returned_attributes=attributes)
    print "dict(user): ", dict(user) # LDAP Entries behave like python dicts
    print "user.cn: ", user.cn       # LDAP Entries attributes can also be accessed directly
    
    attributes = ['nTSecurityDescriptor']
    # This time we will use the paged search
    # The conn object holds reference to a schema attribute that has a cache to several 
    # information from the Active Directory. The cache is stored in the ".cache" directory
    # by default so that it is loaded once per Domain.
    user = conn.search_s_paged(
        base_dn=conn.schema.root_dse['rootNamingContext'], 
        filter='(cn=user2)', 
        scope=LDAP_SCOPE_SUBTREE, 
        returned_attributes=attributes
    )
    
    # The nTSecurityDescriptor is cast to a EPSECURITY_DESCRIPTOR (see the security chapter) 
    print "type(user.nTSecurityDescriptor): ", type(user.nTSecurityDescriptor)
    print "user.nTSecurityDescriptor.control: ", user.nTSecurityDescriptor.control 
    

## OUTPUT ##
Password: 
dict(user):  {'objectClass': [u'top', u'person', u'organizationalPerson', u'user'], 'distinguishedName': 'CN=user2,OU=Users,DC=my,DC=domain,DC=local', 'cn': u'user2'}
user.cn:  user2
type(user.nTSecurityDescriptor):  <class 'windows.security.interfaces.EPSECURITY_DESCRIPTOR'>
user.nTSecurityDescriptor.control:  <SECURITY_DESCRIPTOR_CONTROL "[SE_DACL_PRESENT(0x4L), SE_DACL_AUTO_INHERITED(0x400L), SE_SACL_AUTO_INHERITED(0x800L), SE_SELF_RELATIVE(0x8000L)]">
```


### Other stuff (see doc / samples)

- Network
- COM


[LKD_GITHUB]: https://github.com/sogeti-esec-lab/LKD/
[SAMPLE_DIR]: https://github.com/hakril/PythonForWindows/tree/master/samples
[ONLINE_DOC]: http://hakril.github.io/PythonForWindows/
[ONLINE_SAMPLE]: http://hakril.github.io/PythonForWindows/build/html/sample.html
[ONLINE_SAMPLE_ALPC]: http://hakril.github.io/PythonForWindows/build/html/sample.html#windows-alpc
[ONLINE_SAMPLE_RPC]: http://hakril.github.io/PythonForWindows/build/html/sample.html#windows-rpc
[ONLINE_IATHOOK]: http://hakril.github.io/PythonForWindows/build/html/iat_hook.html