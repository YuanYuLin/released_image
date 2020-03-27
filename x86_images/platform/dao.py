#!/bin/python2.7

import struct
import pprint
import sys
import ConfigParser
import binascii
import json

'''
[Boot disk layout]
'''

def create_buffer():
    record_count, record_size, _, _, _ = get_record_info()
    buff=[]
    for idx in range(0, record_count):
        buff.append(bytearray('\0' * record_size))

    return buff

def convert_kv_to_bytes(key, val):
    _, record_size, record_head_size, _, _ = get_record_info()
    data_size = record_size - record_head_size
    pad = bytearray(str.encode('\0' *  data_size))
    idx = 0
    for ch in bytearray(key):
        pad[idx]=ch
        idx+=1

    for ch in bytearray(val):
        pad[idx]=ch
        idx+=1
    return pad

def dao_to_buffer(dao, buff):
    record_count, record_size, record_head_size, record_format, _ = get_record_info()
    data_size = record_size - record_head_size
    for rec_idx in range(0, record_count):
        idx = 0
        pad = convert_kv_to_bytes("", "")
        data = struct.pack(record_format, '[*REC*]', rec_idx, 0, 0, 0, record_head_size, record_size, 0, 0, 0, 0, 0, 0, str(pad))
        for ch in bytearray(data):
            buff[rec_idx][idx] = ch
            idx += 1

    g_index=0
    for key in dao.keys():
        pad = convert_kv_to_bytes(key, dao[key])

        v_maj = 0
        v_min = 0
        rec_type = 0x81 # 0x80: DAOTYPE_ENABLED | DAOTYPE_JSON
        hdr_len = record_head_size
        rec_len = record_size
        key_len = len(key)
        val_len = len(dao[key])
        resv = 0
        crc32 = 0
        data = struct.pack(record_format, '[*REC*]', (0x8000 | g_index), v_maj, v_min, rec_type, hdr_len, rec_len, val_len, key_len, resv, resv, resv, crc32, str(pad))
        #crc32 = binascii.crc32(bytearray(data))
        #data = struct.pack(record_format, '[*REC*]', crc32, rec_type, key_len, val_len, resv, resv, resv, resv, str(pad))

        #data = struct.pack(record_format, 0, rec_type, key_len, val_len, resv, str(pad))

        idx=0
        for ch in bytearray(data):
            buff[g_index][idx] = ch
            idx+=1
        g_index+=1

    return buff

def out_to_binary(buff, dao_bin_path):
    fd=open(dao_bin_path, 'wb')
    for rec in buff:
        fd.write(rec)
    fd.close()

def get_record_info():
    record_count = 128
    record_size = 512
    record_head_size = 32
    record_data_size = record_size - record_head_size
    #record_format="IBBHI" + str(data_size) + "s"
    record_format="8sHBBBBHHBBIII" + str(record_data_size) + "s"
    text = ''
    text += '#define BOOT_INFO_OFFSET   (%d)\n' % 0x100000
    text += '#define END_INFO_OFFSET    (BOOT_INFO_OFFSET + %d)\n' % 0x10000
    text += '#define DAO_INFO_OFFSET    (END_INFO_OFFSET)\n'
    text += '#define DAO_DATA_OFFSET    (DAO_INFO_OFFSET + %d)\n' % record_size

    text += '#define DAO_KV_MAX             %d\n' % record_count
    text += '#define DAO_DATALEN            %d\n' % (record_size - record_head_size)
    text += '#define RECORD_ENABLED_MASK    0x8000\n'

    text += 'struct dao_hdr_t {\n'
    text += '    uint8_t tag[8];//[*REC*]\n'
    text += '    uint16_t index;\n' 
    text += '    uint8_t ver_major;\n'
    text += '    uint8_t ver_minor;\n'
    text += '    uint8_t type;\n'
    text += '    uint8_t hdr_len;\n'
    text += '    uint16_t rec_len;\n'
    text += '    uint16_t val_len;\n'
    text += '    uint8_t key_len;\n'
    text += '    uint8_t rsv;\n'
    text += '    uint32_t rsv1;\n'
    text += '    uint32_t rsv2;\n'
    text += '    uint32_t chksum;\n'
    text += '} __attribute__((packed));\n'

    text += 'struct dao_kv_t {\n'
    text += '    struct dao_hdr_t hdr;\n'
    text += '    uint8_t data[DAO_DATALEN];\n'
    text += '};\n'

    return record_count, record_size, record_head_size, record_format, text

def out_to_c(buff):
    ft=open('db_init.inc', 'w')
    record_count, record_size, record_head_size, record_format, text = get_record_info()
    ft.write(text)
    ft.write('static struct dao_info_t g_di = {')
    ft.write("    .tag = {'[', '*', 'D', 'A', 'O', '*', ']'},")
    ft.write("    .version_major = 0,")
    ft.write("    .version_minor = 0,")
    ft.write("    .size_of_record = %d," % record_size)
    ft.write("    .count_of_records = %d," % record_count)
    ft.write("    .head_size_of_record = %d," % record_head_size)
    ft.write('};')
    ft.write('static struct dao_kv_t g_dao_kv_list[DAO_KV_MAX]={')
    idx=0
    for rec in buff:
        tag, rec_idx, v_maj, v_min, tp, hdr_len, rec_len, vl, kl, rsv, rsv1, rsv2, csum, data = struct.unpack(record_format, rec)
        ft.write('\n' + '{')
        ft.write('.hdr = {')
        ft.write('.tag = {')
        for ch in bytearray(tag):
            ft.write(str(int(ch)))
            ft.write(',')
        ft.write('},')
        #[', '*', 'R', 'E', 'C', '*', ']'")
        ft.write('.index = %s,' % str(int(rec_idx)))
        ft.write('.ver_major = %s,' % str(int(v_maj)))
        ft.write('.ver_minor = %s,' % str(int(v_min)))
        ft.write('.type = %s,' % str(int(tp)))
        ft.write('.hdr_len = %s,' % str(int(hdr_len)))
        ft.write('.rec_len = %s,' % str(int(rec_len)))
        ft.write('.val_len = %s,' % str(int(vl)))
        ft.write('.key_len = %s,' % str(int(kl)))
        ft.write('.rsv = %s,' % str(int(rsv)))
        ft.write('.rsv1 = %s,' % str(int(rsv1)))
        ft.write('.rsv2 = %s,' % str(int(rsv2)))
        ft.write('.chksum = %s,' % str(int(csum)))
        ft.write('},')
        ft.write('.data = {')
        for ch in bytearray(data):
            ft.write(str(int(ch)))
            ft.write(',')
        ft.write('}')
        ft.write('},')
    ft.write('};')
    ft.close()

def head_to_binary(pack):
    data = bytearray('\0' * 64)
    idx = 0
    for ch in bytearray(pack):
        data[idx] = ch
        idx += 1
    return data

def size_to_bytes(size_str):
    val = 0
    if size_str[-1:] == 'B':
        val = int(size_str[0:-1])
    elif size_str[-1:] == '%':
        val = 0xFFFFFFFF
    return val

def create_header(layout_obj):
    header = bytearray('\0' * (64 *1024))
    buffers = []
    version = 1
    table_type = str(layout_obj["table_type"])
    platform = str(layout_obj["platform"])
    platform_id = layout_obj["platform_id"]
    print table_type, platform, platform_id
    pack = struct.pack("12sI20sI12s", "$[IOPCHEAD]$".ljust(12), version, platform.ljust(20), platform_id, table_type.ljust(12))
    buffers.append(head_to_binary(pack))
    for part in layout_obj["parts"]:
        obj = layout_obj[part]
        part_name = str(part)
        boot=obj["boot"]
        fstype = str(obj["fstype"])
        start = size_to_bytes(obj["start"])
        end = size_to_bytes(obj["end"])

        bin_file = obj["bin_files"]
        pack = struct.pack("12s10s10sQQB", "$[IOPCREC]$".ljust(12), part_name.ljust(10), fstype.ljust(10), start, end, boot)
        buffers.append(head_to_binary(pack))

    pack = struct.pack("12sI20sI12s", "$[IOPCEND]$".ljust(12), version, platform.ljust(20), platform_id, table_type.ljust(12))
    buffers.append(head_to_binary(pack))
    idx = 0
    for sec in buffers:
        for ch in sec:
            header[idx]=ch
            idx+=1

    return header

def help():
    print "usage: dao.py <dao.ini> <dao.bin>"
    sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        help()
    dao={}
    cfg_ini = sys.argv[1]
    dao_bin_path = sys.argv[2]
    config = ConfigParser.RawConfigParser()
    config.read(cfg_ini)
    single_section = config.items("CFG_DAO")
    for item in single_section:
        print "key = %s, valule = %s" % (item[0], item[1])
        key = item[0]
        val = item[1]
        dao[key] = val

    #record_count, record_size, record_head_size, _, _ = get_record_info()

    buf=create_buffer()
    buf=dao_to_buffer(dao, buf)
    out_to_binary(buf, dao_bin_path)
    out_to_c(buf)

    layout = config.get('CFG_IMAGE', 'layout')
    layout_obj  = json.loads(layout)
    '''
    header_bin = create_header(layout_obj)
    hdr_path = dao_bin_path + ".hdr"
    fd=open(hdr_path, 'wb')
    fd.write(header_bin)
    fd.close()
    '''
