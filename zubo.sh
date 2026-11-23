#!/usr/bin/env bash
# 安徽电信组播源测速：读取 ip/安徽电信_ip.txt，探测可用性后取最快 3 个 IP
# 生成 txt/安徽电信.txt（3 组播分组）
set -u

city="安徽电信"
stream="rtp/238.1.79.27:4328"

time=$(date +%m%d%H%M)
ipfile="ip/${city}_ip.txt"
good_ip="ip/good_${city}_ip.txt"
result_ip="ip/result_${city}_ip.txt"

echo "======== 开始检索 ${city} ========"
if [ ! -f "$ipfile" ]; then
  echo "缺少 ${ipfile}"
  exit 1
fi

sort "$ipfile" | uniq | sed '/^\s*$/d' > "${ipfile}.tmp" && mv "${ipfile}.tmp" "$ipfile"
: > "$good_ip"

while IFS= read -r ip; do
  tmp_ip=$(echo -n "$ip" | sed 's/:/ /')
  output=$(nc -w 1 -v -z $tmp_ip 2>&1)
  if [[ $output == *"succeeded"* ]]; then
    echo "$output" | grep "succeeded" | awk -v ip="$ip" '{print ip}' >> "$good_ip"
  fi
done < "$ipfile"

lines=$(wc -l < "$good_ip")
echo "连接成功 $lines 个，开始测速······"
i=0
: > "speedtest_${city}_${time}.log"
while IFS= read -r ip; do
  i=$((i + 1))
  url="http://$ip/$stream"
  curl "$url" --connect-timeout 5 --max-time 40 -o /dev/null > zubo.tmp 2>&1
  a=$(head -n 3 zubo.tmp | awk '{print $NF}' | tail -n 1)
  echo "第$i/$lines个：$ip    $a"
  echo "$ip    $a" >> "speedtest_${city}_${time}.log"
done < "$good_ip"

echo "测速结果排序"
awk '/M|k/{print $2"  "$1}' "speedtest_${city}_${time}.log" | sort -n -r > "$result_ip"
cat "$result_ip"
ip1=$(awk 'NR==1{print $2}' "$result_ip")
ip2=$(awk 'NR==2{print $2}' "$result_ip")
ip3=$(awk 'NR==3{print $2}' "$result_ip")
rm -f zubo.tmp "$good_ip" "speedtest_${city}_${time}.log" "$result_ip"

if [ -z "${ip1:-}" ]; then
  echo "未获取到可用 IP，保留原有 txt/${city}.txt"
  exit 0
fi

program="template/template_${city}.txt"
sed "s/ipipip/$ip1/g" "$program" > tmp_1.txt
[ -n "${ip2:-}" ] && sed "s/ipipip/$ip2/g" "$program" > tmp_2.txt || : > tmp_2.txt
[ -n "${ip3:-}" ] && sed "s/ipipip/$ip3/g" "$program" > tmp_3.txt || : > tmp_3.txt

{
  echo "${city}-组播1,#genre#"; cat tmp_1.txt
  echo "${city}-组播2,#genre#"; cat tmp_2.txt
  echo "${city}-组播3,#genre#"; cat tmp_3.txt
} | grep -vE '/{3}' > "txt/${city}.txt"

rm -f tmp_1.txt tmp_2.txt tmp_3.txt
echo "${city} 测试完成，生成可用文件：txt/${city}.txt"
