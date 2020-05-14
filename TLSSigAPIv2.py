#! /usr/bin/python
# coding:utf-8


import hmac
import hashlib
import base64
import zlib
import json
import time


def base64_encode_url(data):
    """ base url encode 实现"""
    base64_data = base64.b64encode(data)
    base64_data_str = bytes.decode(base64_data)
    base64_data_str = base64_data_str.replace('+', '*')
    base64_data_str = base64_data_str.replace('/', '-')
    base64_data_str = base64_data_str.replace('=', '_')
    return base64_data_str


def base64_decode_url(base64_data):
    """ base url decode 实现"""
    base64_data_str = bytes.decode(base64_data)
    base64_data_str = base64_data_str.replace('*', '+')
    base64_data_str = base64_data_str.replace('-', '/')
    base64_data_str = base64_data_str.replace('_', '=')
    raw_data = base64.b64decode(base64_data_str)
    return raw_data


class TLSSigAPIv2:
    __sdkappid = 0
    __version = '2.0'
    __key = ""

    def __init__(self, sdkappid, key):
        self.__sdkappid = sdkappid
        self.__key = key
    ##用于生成实时音视频(TRTC)业务进房权限加密串,具体用途用法参考TRTC文档：https://cloud.tencent.com/document/product/647/32240 
    # TRTC业务进房权限加密串需使用用户定义的userbuf
    # @brief 生成 userbuf
    # @param account 用户名
    # @param dwSdkappid sdkappid
    # @param dwAuthID  数字房间号
    # @param dwExpTime 过期时间：该权限加密串的过期时间，实际过期时间：当前时间+dwExpTime
    # @param dwPrivilegeMap 用户权限，255表示所有权限
    # @param dwAccountType 用户类型,默认为0
    # @return userbuf  {string}  返回的userbuf
    #/
    def _gen_userbuf(self,account, dwAuthID, dwExpTime,
               dwPrivilegeMap, dwAccountType):
        userBuf = b''

        userBuf += bytearray([
            0,
            ((len(account) & 0xFF00) >> 8),
            (len(account) & 0x00FF),
        ])
        userBuf += bytearray(map(ord, account))

        # dwSdkAppid
        userBuf += bytearray([
            ((self.__sdkappid & 0xFF000000) >> 24),
            ((self.__sdkappid & 0x00FF0000) >> 16),
            ((self.__sdkappid & 0x0000FF00) >> 8),
            (self.__sdkappid & 0x000000FF),
        ])

        # dwAuthId
        userBuf += bytearray([
            ((dwAuthID & 0xFF000000) >> 24),
            ((dwAuthID & 0x00FF0000) >> 16),
            ((dwAuthID & 0x0000FF00) >> 8),
            (dwAuthID & 0x000000FF),
        ])

        #  dwExpTime = now + 300;
        expire = dwExpTime +int(time.time())
        userBuf += bytearray([
            ((expire & 0xFF000000) >> 24),
            ((expire & 0x00FF0000) >> 16),
            ((expire & 0x0000FF00) >> 8),
            (expire & 0x000000FF),
        ])

        # dwPrivilegeMap
        userBuf += bytearray([
            ((dwPrivilegeMap & 0xFF000000) >> 24),
            ((dwPrivilegeMap & 0x00FF0000) >> 16),
            ((dwPrivilegeMap & 0x0000FF00) >> 8),
            (dwPrivilegeMap & 0x000000FF),
        ])

        # dwAccountType
        userBuf += bytearray([
            ((dwAccountType & 0xFF000000) >> 24),
            ((dwAccountType & 0x00FF0000) >> 16),
            ((dwAccountType & 0x0000FF00) >> 8),
            (dwAccountType & 0x000000FF),
        ])
        return userBuf
    def __hmacsha256(self, identifier, curr_time, expire, base64_userbuf=None):
        """ 通过固定串进行 hmac 然后 base64 得的 sig 字段的值"""
        raw_content_to_be_signed = "TLS.identifier:" + str(identifier) + "\n"\
                                   + "TLS.sdkappid:" + str(self.__sdkappid) + "\n"\
                                   + "TLS.time:" + str(curr_time) + "\n"\
                                   + "TLS.expire:" + str(expire) + "\n"
        if None != base64_userbuf:
            raw_content_to_be_signed += "TLS.userbuf:" + base64_userbuf + "\n"
        return base64.b64encode(hmac.new(self.__key.encode('utf-8'),
                                         raw_content_to_be_signed.encode('utf-8'),
                                         hashlib.sha256).digest())

    def __gen_sig(self, identifier, expire=180*86400, userbuf=None):
        """ 用户可以采用默认的有效期生成 sig """
        curr_time = int(time.time())
        m = dict()
        m["TLS.ver"] = self.__version
        m["TLS.identifier"] = str(identifier)
        m["TLS.sdkappid"] = int(self.__sdkappid)
        m["TLS.expire"] = int(expire)
        m["TLS.time"] = int(curr_time)
        base64_userbuf = None
        if None != userbuf:
            base64_userbuf = bytes.decode(base64.b64encode(userbuf))
            m["TLS.userbuf"] = base64_userbuf

        m["TLS.sig"] = bytes.decode(self.__hmacsha256(
            identifier, curr_time, expire, base64_userbuf))

        raw_sig = json.dumps(m)
        sig_cmpressed = zlib.compress(raw_sig.encode('utf-8'))
        base64_sig = base64_encode_url(sig_cmpressed)
        return base64_sig

    def gen_sig(self, identifier, expire=180*86400):
        """ 用户可以采用默认的有效期生成 sig """
        return self.__gen_sig(identifier, expire, None)
    # @brief 生成带userbuf的sig
    # @param identifier 用户名
    # @param roomnum  数字房间号
    # @param expire 过期时间：该权限加密串的过期时间，实际过期时间：当前时间+expire
    # @param privilege 用户权限，255表示所有权限
    def gen_sig_with_userbuf(self, identifier, expire, roomnum, privilege):
        """ 带 userbuf 生成签名 """
        userbuf = self._gen_userbuf("xiaojun",roomnum,expire,privilege,0)
        print(userbuf)
        return self.__gen_sig(identifier, expire, userbuf)


def main():
    api = TLSSigAPIv2(1400000000, '5bd2850fff3ecb11d7c805251c51ee463a25727bddc2385f3fa8bfee1bb93b5e')
    sig = api.gen_sig("xiaojun")
    print(sig)
    sig = api.gen_sig_with_userbuf("xiaojun", 86400*180,10000,255)
    print(sig)


if __name__ == "__main__":
    main()
