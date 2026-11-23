#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安徽电信 udpxy 节点批量扫描与测速
原理：存档里存的是网段代表地址（如 124.112.240.1:4022），
      本脚本把每个网段展开为 1-254，并发探测 /status 找出真实有效节点，
      再对有效节点拉流测速，输出按速率排序的可用清单。

用法：python scan_ah_ips.py
      python scan_ah_ips.py --quick   # 快速模式：只测存档里的 .1 地址（通常测不到）

运行环境要求：必须在安徽电信网络内（电信宽带/电信手机卡），关闭代理/VPN。
"""
import os
import sys
import time
import socket
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

# 禁用系统代理，避免误判
for k in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"]:
    os.environ.pop(k, None)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
urllib.request.install_opener(opener)

ARCHIVE = "ip/存档_安徽电信_ip.txt"
CURRENT = "ip/安徽电信_ip.txt"
RESULT_TXT = "ip/检测报告_安徽电信.txt"
RESULT_M3U = "ip/可用节点_安徽电信.txt"

# 拉流测试用的频道（安徽卫视）
TEST_STREAM_PATH = "/rtp/238.1.79.27:4328"
HEADERS = {"User-Agent": "Mozilla/5.0"}
STATUS_TIMEOUT = 2
STREAM_SECONDS = 3

QUICK = "--quick" in sys.argv


def load_segments():
    """读取存档网段，返回 [(网段前缀, 端口)]，如 ('124.112.240', 4022)"""
    paths = [ARCHIVE, CURRENT]
    segs = set()
    for p in paths:
        if not os.path.exists(p):
            continue
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                ip, port = line.split(":", 1)
                parts = ip.split(".")
                if len(parts) != 4:
                    continue
                prefix = ".".join(parts[:3])
                try:
                    segs.add((prefix, int(port)))
                except ValueError:
                    continue
    return sorted(segs)


def check_status(ip_port):
    """检测单个 IP:端口是否为有效 udpxy 节点"""
    url = f"http://{ip_port}/status"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=STATUS_TIMEOUT) as r:
            body = r.read(1024).decode("utf-8", "ignore").lower()
            if "udpxy status" in body or "multi stream daemon" in body:
                return ip_port
    except Exception:
        pass
    return None


def measure_speed(ip_port):
    """对有效节点拉流测速，返回 KB/s；失败返回 0"""
    url = f"http://{ip_port}{TEST_STREAM_PATH}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        start = time.time()
        total = 0
        with urllib.request.urlopen(req, timeout=5) as r:
            while time.time() - start < STREAM_SECONDS:
                chunk = r.read(65536)
                if not chunk:
                    break
                total += len(chunk)
        elapsed = time.time() - start
        return total / elapsed / 1024 if elapsed > 0 and total > 0 else 0
    except Exception:
        return 0


def main():
    print("=" * 64)
    print("安徽电信 udpxy 节点批量扫描与测速")
    print("=" * 64)
    print("运行环境要求：安徽电信网络内 + 关闭代理/VPN")
    if QUICK:
        print("模式：快速（仅测存档 .1 地址）")
    else:
        print("模式：完整（展开每个网段的 1-254）")

    segs = load_segments()
    print(f"存档网段：{len(segs)} 个")
    for prefix, port in segs:
        print(f"  - {prefix}.x:{port}")
    print()

    # 生成待扫描目标
    targets = []
    for prefix, port in segs:
        if QUICK:
            targets.append(f"{prefix}.1:{port}")
        else:
            for last in range(1, 255):
                targets.append(f"{prefix}.{last}:{port}")
    print(f"待检测目标：{len(targets)} 个，开始扫描（约 2-5 分钟）...\n")

    start_time = time.time()
    valid = []
    done = 0
    with ThreadPoolExecutor(max_workers=120) as ex:
        futures = {ex.submit(check_status, t): t for t in targets}
        for fut in as_completed(futures):
            done += 1
            r = fut.result()
            if r:
                valid.append(r)
                print(f"  [发现] {r}")
            if done % 500 == 0:
                print(f"  进度 {done}/{len(targets)}，已发现 {len(valid)} 个有效节点")

    print(f"\n扫描完成，耗时 {time.time()-start_time:.0f}s，发现 {len(valid)} 个有效节点")

    if not valid:
        print("\n未发现有效节点。请确认：")
        print("  1. 是否连接安徽电信网络")
        print("  2. 是否关闭代理/VPN")
        print("  3. 若都满足，说明这些网段已全部失效，需在 Actions 上重新扫描")
        return

    # 测速排序
    print("\n开始拉流测速（安徽卫视，每节点 3 秒）...")
    results = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(measure_speed, ip): ip for ip in valid}
        for fut in as_completed(futures):
            ip = futures[fut]
            speed = fut.result()
            results.append((ip, speed))
            print(f"  {ip:28s} {speed:7.0f} KB/s")

    results.sort(key=lambda x: -x[1])

    # 写出报告
    now = time.strftime("%Y/%m/%d %H:%M")
    with open(RESULT_TXT, "w", encoding="utf-8") as f:
        f.write(f"# 安徽电信 udpxy 节点检测报告\n# 检测时间：{now}\n")
        f.write(f"# 网络环境：安徽电信网内（需人工确认）\n")
        f.write(f"# 有效节点：{len(results)} 个\n\n")
        f.write("排名\t节点\t拉流速度\n")
        for i, (ip, speed) in enumerate(results, 1):
            f.write(f"{i}\t{ip}\t{speed:.0f} KB/s\n")

    with open(RESULT_M3U, "w", encoding="utf-8") as f:
        for ip, _ in results:
            f.write(ip + "\n")

    print("\n" + "=" * 64)
    print(f"按速度排序，可用节点共 {len(results)} 个：")
    for i, (ip, speed) in enumerate(results[:20], 1):
        mark = " <== 最快" if i == 1 else ""
        print(f"  {i:2d}. {ip:28s} {speed:7.0f} KB/s{mark}")
    if len(results) > 20:
        print(f"  ... 另有 {len(results)-20} 个节点，详见报告文件")
    print("=" * 64)
    print(f"\n报告已保存：{RESULT_TXT}")
    print(f"节点清单：  {RESULT_M3U}")
    print(f"\n使用方法：将最快节点的 IP 替换 组播_安徽电信.txt 中旧 IP 即可。")


if __name__ == "__main__":
    main()
