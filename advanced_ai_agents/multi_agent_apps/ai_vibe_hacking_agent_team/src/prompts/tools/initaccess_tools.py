"""
Initial Access 에이전트의 도구 프롬프트

이 파일은 Initial Access 에이전트가 사용할 도구에 대한 프롬프트를 정의합니다.
"""

INITACCESS_TOOLS_PROMPT = """
<exploitation_tools>
## Available Exploitation Tools:

### searchsploit - Vulnerability Database Search
**When to use**: Find exploits for discovered services and software versions
**Examples**:
- Service search: `searchsploit("Apache 2.4.29", ["-t"])`
- CVE lookup: `searchsploit("--cve", "CVE-2021-44228")`
- Exact match: `searchsploit("OpenSSH 7.4", ["-e"])`

### hydra - Credential Attacks
**When to use**: Brute force authentication when weak credentials suspected
**Available wordlists**: 
- Users: `root/data/wordlist/user.txt`
- Passwords: `root/data/wordlist/password.txt`


## Attack Approach:
1. **Research First**: Use `searchsploit` to find known vulnerabilities
2. **Exploit Second**: Try direct vulnerability exploitation
3. **Credentials Third**: Use `hydra` for authentication attacks
4. **Verify Access**: Always confirm successful exploitation

## Success Indicators:
- Command execution capability
- Valid authentication credentials
- System access confirmation
- Network pivot opportunities

Focus on reliable, stable access over complex exploits. Document everything for reproduction and handoff to privilege escalation phases.
</exploitation_tools>
"""
