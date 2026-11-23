#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安徽电信 udpxy 代理可用性检测
用法：python check_ah_telecom.py
说明：必须在能访问安徽电信城域网的环境下运行（如安徽电信宽带/手机卡）。
      若用了代理/VPN，请先关闭，否则会误判。
"""
import urllib.request
import socket
import ssl

# 关键：禁用系统代理，避免代理干扰导致误判
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
urllib.request.install_opener(opener)

BASE = "124.112.240.224:4022"
STATUS_URL = f"http://{BASE}/status"
# 安徽卫视组播流（来自模板第一个频道）
STREAM_URL = f"http://{BASE}/rtp/238.1.79.27:4328"

HEADERS = {"User-Agent": "Mozilla/5.0"}


def check_status():
    """第一层：检测 udpxy 服务是否存活"""
    print("【1/2】检测 udpxy 服务状态页 ...")
    print(f"      {STATUS_URL}")
    try:
        req = urllib.request.Request(STATUS_URL, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as r:
            body = r.read(2048).decode("utf-8", "ignore")
            if "udpxy status" in body.lower() or "multi stream daemon" in body.lower():
                print("      [通过] 服务存活，返回标准 udpxy 状态页\n")
                return True
            else:
                print(f"      [异常] 有响应但非 udpxy 页面：{body[:80]!r}\n")
                return False
    except Exception as e:
        print(f"      [失败] {type(e).__name__}: {e}")
        print("      -> 可能是网络不通、IP 失效，或当前网络不在安徽电信网内\n")
        return False


def check_stream():
    """第二层：检测能否真正拉到组播流，并粗略测速"""
    print("【2/2】检测实际频道流（安徽卫视，抓 5 秒数据）...")
    print(f"      {STREAM_URL}")
    try:
        req = urllib.request.Request(STREAM_URL, headers=HEADERS)
        import time
        start = time.time()
        total = 0
        with urllib.request.urlopen(req, timeout=8) as r:
            while time.time() - start < 5:
                chunk = r.read(65536)
                if not chunk:
                    break
                total += len(chunk)
        elapsed = time.time() - start
        if total > 0:
            speed = total / elapsed / 1024  # KB/s
            print(f"      [通过] 拉流成功：{total/1024/1024:.2f} MB / {elapsed:.1f}s "
                  f"(约 {speed:.0f} KB/s)\n")
            return True
        else:
            print("      [失败] 连接成功但无数据传输\n")
            return False
    except Exception as e:
        print(f"      [失败] {type(e).__name__}: {e}")
        print("      -> 服务可能存活但组播源异常，或该频道已下线\n")
        return False


def main():
    print("=" * 60)
    print("安徽电信 udpxy 代理可用性检测")
    print("=" * 60)
    s_ok = check_status()
    m_ok = check_stream()
    print("=" * 60)
    if s_ok and m_ok:
        print("结论：完全可用（服务正常 + 拉流正常）")
    elif s_ok:
        print("结论：服务存活但拉流异常，可能是组播源问题或频道下线")
    elif m_ok:
        print("结论：能拉流但状态页异常，仍可正常观看")
    else:
        print("结论：不可用。请确认：")
        print("  1. 当前是否连接安徽电信网络（电信宽带/电信手机卡）")
        print("  2. 是否关闭了代理/VPN")
        print("  3. 若以上都满足仍不可用，则该 IP 可能已失效，")
        print("     需在 GitHub Actions 上重新扫描获取新 IP")
    print("=" * 60)


if __name__ == "__main__":
    main()
