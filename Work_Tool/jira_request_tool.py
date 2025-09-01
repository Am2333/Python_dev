from collections import defaultdict
import json

import requests
import re
import os
#customfield_12306 type
#key jira id
#issuelinks key去重，name判断reject
#customfield_11705 huigui
#customfield_10211 ppl bag
#issuetype name属性test

def get_jira(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    pattern = r'^E2E-\d+$'  # 正则表达式：以E2E-开头，后面跟着一位或多位数字，然后结束
    urls = []
    # 修改正则表达式：匹配 E2E-后面跟着数字的模式（不要求整个字符串匹配）
    pattern = r'E2E-\d+'
    
    for line in lines:
        line = line.strip()
        
        # 在整行中搜索 E2E-数字 的模式
        match = re.search(pattern, line)
        if match:
            # 找到匹配的部分
            e2e_id = match.group()
            urls.append(e2e_id)
        else:
            # 如果没有找到E2E-数字，保留原来的逻辑
            if len(line) >= 48:
                urls.append(line[39:48])
            else:
                urls.append("")  # 或者选择其他处理方式
    
    return urls

def get_jira_link(url_row):
    base_url = "https://"
    if url_row.startswith("E"):  # 如果以 "E" 开头
        return base_url + url_row  # 拼接成完整 URL
    return url_row


# 递归提取 issuelinks 中的 key
def extract_issue_links(issue_links):
    keys = []
    for link in issue_links:
        # 每个 link 可能包含 inwardIssue 或 outwardIssue
        for side in ['inwardIssue', 'outwardIssue']:
            if side in link and 'key' in link[side]:
                keys.append(link[side]['key'])
        # 如果 link 本身有嵌套的 issuelinks，递归处理
        if 'issuelinks' in link:
            keys.extend(extract_issue_links(link['issuelinks']))
    return keys


def down_json(path):

    urls = get_jira(path)
    urlslink = [get_jira_link(u) for u in urls]
    #拼接

    headers = {
        "Authorization": "token",
        "Content-Type": "application/json"
    }
    jira_data = {}

    for url in urlslink:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            key = data.get("key", "")
            fields = data.get("fields", {})

            car_type = fields.get("customfield_12306", {}).get("value")  # 车型
            regression_status = fields.get("customfield_11705", {}).get("value")  # 回归测试入库状态
            ppl_package = fields.get("customfield_10211")  # ppl包地址
            issue_type = fields.get("issuetype", {}).get("name")  # issue类型
            issue_key = extract_issue_links(data.get("fields", {}).get("issuelinks", []))# 递归提取 issuelinks 
    

            jira_data[key] = {
                "car_type": car_type,
                "regression_status": regression_status,
                "ppl_package": ppl_package,
                "issue_type": issue_type,
                "issue_key":issue_key
            }
        else:
            print(f"Failed to get {url}: {response.status_code}")
    return jira_data
    # # 保存结果到 JSON 文件
    # with open("jira_summary.json", "w", encoding="utf-8") as f:
    #     json.dump(jira_data, f, indent=4, ensure_ascii=False)

def check_json(jira_data):

    # 1. 筛选车型为 Z10
    z10_items = {k:v for k,v in jira_data.items() if v.get("car_type") == "Z10"}

    # 2. 查找重复 key
    # 建立 key → 所有出现的 places 映射
    all_keys = defaultdict(list)  # key: list of parent keys where it appears

    for parent_key, info in jira_data.items():
        all_keys[parent_key].append(parent_key)  # 自身也算
        for ik in info.get("issue_key", []):
            all_keys[ik].append(parent_key)

    # 找出重复出现的 key
    duplicates = {k:v for k,v in all_keys.items() if len(v) > 1}

    # 3. 筛选回归状态为否
    regression_no = {k:v for k,v in jira_data.items() if v.get("regression_status") == "否"}

    # 输出结果
    print("===== 车型为 Z10 =====")
    for k, v in z10_items.items():
        print(k, v)

    print("\n===== 重复 key 及重复关系 =====")
    for k, v in duplicates.items():
        print(f"{k} 重复出现在: {v}")

    print("\n===== 回归状态为 否 =====")
    for k, v in regression_no.items():
        print(k, v)

def down_mcap_bash(jira_data):
    # 读取 JSON 文件
    data = jira_data

    commands = []

    for key, info in data.items():
        s3_path = info.get("ppl_package")
        if s3_path:
            # 从 s3 地址取出最后的文件名
            filename = s3_path.split('/')[-1]
            # 拼接成 ./key@filename
            local_path = f"./{key}@{filename}"
            # 构建 refile cp 命令
            cmd = f'refile cp {s3_path} {local_path} -g'
            commands.append(cmd)

    # 写入 shell 脚本
    with open("download.sh", "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n\n")
        f.write("commands=(\n")
        for cmd in commands:
            f.write(f'"{cmd}" \n')
        f.write(")\n\n")
        f.write("total=${#commands[@]}\n\n")
        f.write('for i in "${!commands[@]}"; do\n')
        f.write("  current=$((i + 1))\n")
        f.write('  path=$(echo "${commands[$i]}" | grep -oP \'\\.\\/\\K[^@]+\')\n')
        f.write('  echo "[$current/$total] ./$path"\n')
        f.write('  eval "${commands[$i]}"\n')
        f.write("done\n")

    print("Shell 脚本 download.sh 已生成")



# check_json(down_json("url.txt"))
down_mcap_bash(down_json("url.txt"))
