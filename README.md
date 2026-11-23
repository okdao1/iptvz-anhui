# iptvz - 安徽电信组播源

从 [q1017673817/iptvz](https://github.com/q1017673817/iptvz) fork 并精简：仅保留**安徽电信**组播源，删除其他省份与酒店源。

## 原理

1. `zubo.py` 读取 `ip/安徽电信_config.txt` 中的网段/端口/扫描模式，多线程探测可用的 udpxy 代理地址；
2. 将 `template/template_安徽电信.txt` 中的 `ipipip` 占位符替换为可用代理 IP，生成 `组播_安徽电信.txt`；
3. 汇总为 `安徽电信.txt`（m3u 风格）与 `安徽电信.m3u`，可直接导入播放器。

`zubo.sh` 为另一条测速路线：用 `nc` + `curl` 对 `ip/安徽电信_ip.txt` 中的节点测速，取最快 3 个 IP 生成 `txt/安徽电信.txt`。

## 文件说明

| 路径 | 作用 |
| --- | --- |
| `ip/安徽电信_config.txt` | 扫描配置（IP 段、端口、扫描模式） |
| `ip/安徽电信_ip.txt` | 当前有效 udpxy 代理 |
| `ip/存档_安徽电信_ip.txt` | 历史代理 IP 存档 |
| `template/template_安徽电信.txt` | 频道模板，`ipipip` 为占位符 |
| `组播_安徽电信.txt` | zubo.py 生成的组播源 |
| `安徽电信.txt` / `安徽电信.m3u` | 最终播放列表 |
| `txt/安徽电信.txt` | zubo.sh 测速生成的三节点版本 |
| `check_ah_telecom.py` | 检测单个 IP 是否可用（状态页 + 拉流两层） |
| `scan_ah_ips.py` | 批量扫描存档所有网段，找出可用节点并按测速排序 |

## 使用

GitHub Actions 每天 UTC 06:00 / 23:00（北京时间 14:00 / 07:00）自动更新，也可在 Actions 页面手动触发。

本地运行：

```bash
pip install -r requirements.txt
python zubo.py          # 扫描并生成组播源
bash zubo.sh            # 可选：测速生成 txt/安徽电信.txt（需 nc、curl）
```

## 检测 IP 是否可用

**前提**：必须在安徽电信网络内（电信宽带/电信手机卡），并关闭代理/VPN，否则会误判。

```bash
# 检测单个 IP（如当前节点）
python check_ah_telecom.py

# 批量扫描存档全部网段（29 个网段展开为 7366 个目标，约 2-5 分钟）
python scan_ah_ips.py
```

`scan_ah_ips.py` 会把每个存档网段（如 `124.112.240.1:4022`）展开为 `.1-.254` 全扫描，
对有效节点拉流测速后按速度排序，结果输出到 `ip/检测报告_安徽电信.txt` 和 `ip/可用节点_安徽电信.txt`。
把最快节点的 IP 替换到播放列表里即可。

## 注意

- 组播源依赖运营商内网 udpxy 代理，通常仅在安徽电信网络内可用；
- Fork 后如需自动提交，请在仓库 **Settings → Actions → General → Workflow permissions** 中开启 **Read and write permissions**；
- 本项目仅做技术整理，请遵守当地法律法规与运营商服务条款。
