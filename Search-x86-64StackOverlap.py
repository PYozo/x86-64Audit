#查找危险函数，并让其高亮

from idaapi import *

DEBUG=True

#set all dangerous_functions and backdoor function
dangerous_functions=[
    "strcpy",
    "strcat",
    "sprintf",
    "read",
    "getenv"
]

attention_functions=[
    "memcpy",
    "strncpy",
    "sscanf",
    "strncat",
    "snprintf",
    "vprintf",
    "printf"
]

command_execution_functions=[
    "system",
    "execve",
    "popen",
    "unlink"
]

#describe arg num of function

one_arg_function=[
    "getenv",
    "system",
    "unlink"
]

two_arg_function=[
    "strcpy",
    "strcat",
    "popen"
]

three_arg_function = [
    "strncpy",
    "strncat", 
    "memcpy",
    "execve",
    "read"
]

format_function_offset_dict = {
    "sprintf":1,
    "sscanf":1,
    "snprintf":2,
    "vprintf":0,
    "printf":0
}

def getFuncAddr(func_name):
    addr=LocByName(func_name)
    if addr!=BADADDR:
        return addr
    return False

#查找参数地址，并添加注释
def getArgAddr(func_addr):
    args=[]
    for i in idaapi.get_arg_addrs(func_addr):
        idc.set_cmt(i,"addr: 0x%x" % (func_addr),0)#设置注释
        idc.set_color(i,CIC_ITEM,0x00ff00)
        args.append(i)
    return args
 
#获得函数的参数地址
def getArgs(addr):
    x86mov=['mov','lea']
    args=[]
    #如果是参数不是寄存器传值(寄存器传值的返回值为1)
    if idc.get_operand_type(addr,1) !=1:
        arg=idc.print_operand(addr,1)
        if "offset" in arg:
            return arg[7:]
        else:
            return arg
    #如果是寄存器的话,一直找到其来源
    func_start=idaapi.get_func(addr).start_ea
    arg_addr=addr
    target=idc.print_operand(addr,1)
    while arg_addr<=start_ea:
        arg_addr=idc.get_first_cref_to(arg_addr)
        if idc.idc.print_insn_mnem(arg_addr) in x86mov and idc.print_operand(arg_addr,0)==target:
            args.append(idc.print_operand(arg_addr,1))
    
    return args



#获取格式化字符串，并判断其是否有异常
def formatString(func_addr,argName):
    s=''
    format_arg_addr=idc.LocByName(argName)
    #查看对应位置是否为字符串
    if idc.GetStringType(format)==0:
        s+=hex(format_arg_addr)
    else:
        s+='This function maybe dangous!'
    return [s]

def GetFormatArgs(func_addr,index):
    #获取普通的
    arg=getArgs(func_addr)
    return arg+formatString(func_addr,arg[index],index)

def auditFormat(func_addr,func_name,arg_num):
    #local buf size
    local_buf_size=idc.get_func_attr(func_addr,FUNCATTR_FRSIZE)
    if local_buf_size==BADADDR:
        local_buf_size="get fail"
    else:
        local_buf_size="0x%x"%local_buf_size
        
    table_head=["func_name","addr"]
    for num in xrange(0,arg_num):
        table_head.append("arg"+str(num+1))
    if func_name in format_function_offset_dict:
        table_head.append("format&value[string_addr, num of '%', fmt_arg...]")
    table_head.append("local_buf_size")
    table=PrettyTable(table_head)
    
    index=format_function_offset_dict[func_name]
    #get all args addr
    args=getFuncAddr(func_addr)
    xrefs=CodeRefsTo(func_addr,0)
    for xref in xrefs:
        set_color(xref,CIC_ITEM,0x00ff00)
        table.add_row([hex(xref)]+GetFormatArgs(func_addr,index)+[hex(local_buf_size)])
    pass
    
#审计普通函数参数的地址
def auditAddr(func_addr,func_name):
    #local buf size
    local_buf_size=idc.get_func_attr(func_addr,FUNCATTR_FRSIZE)
    if local_buf_size==BADADDR:
        local_buf_size="get fail"
    else:
        local_buf_size="0x%x"%local_buf_size
    
    table_head=["func_name","addr"]
    for num in xrange(0,arg_num):
        table_head.append("arg"+str(num+1))
    if func_name in format_function_offset_dict:
        table_head.append("format&value[string_addr, num of '%', fmt_arg...]")
    table_head.append("local_buf_size")
    table=PrettyTable(table_head)
    
    if idc.SegName(func_addr)=='extern':
        addrs=list(idauntils.CodeRefsTo(func_addr))
    
    for i in addrs:
        temp_args=getArgAddr(i)
        args=[func_name,i]
        for i in xrange(temp_args):
            args.append(getArgs(i))
        args.append(local_buf_size)
        table.add_row(args)
    
       
def audit(func_name):
    func_addr=getFuncAddr(func_name)
    if func_name in one_arg_function:
        arg_num = 1
    elif func_name in two_arg_function:
        arg_num = 2
    elif func_name in three_arg_function:
        arg_num = 3
    elif func_name in format_function_offset_dict:
        arg_num = format_function_offset_dict[func_name] + 1
    else:
        print("The %s function didn't write in the describe arg num of function array,please add it to,such as add to `two_arg_function` arary" % func_name)
        return
        
    if idc.SegName(func_addr)=='extern':
        addrs=list(idauntils.CodeRefsTo(func_addr))
    
    for i in range(addrs):
        if func_name in format_function_offset_dict:
            auditFormat(i,func_name,arg_num)
        else:
            auditAddr(i,func_name,argnum)
        
        #----------------
    print(table)
        
def main_Audit():
    print('Auditing dangerous functions ......')
    for i in dangerous_functions:
        audit(i)
    print('Auditing attention function ......')
    for i in attention_functions:
        audit(i)
    print('Auditing attention function ......')
    for i in command_execution_functions:
        audit(i)