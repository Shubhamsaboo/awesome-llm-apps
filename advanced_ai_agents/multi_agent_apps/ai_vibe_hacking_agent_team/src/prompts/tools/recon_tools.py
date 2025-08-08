"""
Reconnaissance 에이전트의 도구 프롬프트

이 파일은 Reconnaissance 에이전트가 사용할 도구에 대한 프롬프트를 정의합니다.
"""

RECON_TOOLS_PROMPT = """
<reconnaissance_tools>
## Available Reconnaissance Tools:

### nmap - Network Discovery & Port Scanning
**When to use**: Discover live hosts, identify open ports, enumerate services
**Examples**:
- Host discovery: `nmap("192.168.1.0/24", ["-sn"])`
- Service scan: `nmap("target.com", ["-sV", "-sC"])`
- Stealth scan: `nmap("target.com", ["-sS", "-T2"])`

### dig - DNS Information Gathering  
**When to use**: Gather DNS records, discover subdomains, map infrastructure
**Examples**:
- Basic lookup: `dig("target.com", "A")`
- All records: `dig("target.com", "ANY")`
- Zone transfer: `dig("@ns1.target.com target.com", "AXFR")`

### whois - Domain Registration Intelligence
**When to use**: Get domain ownership, registration details, administrative contacts
**Examples**:
- Domain info: `whois("target.com")`
- IP ownership: `whois("192.168.1.1")`

### curl - Web Service Analysis
**When to use**: Analyze web applications, gather headers, test connectivity
**Examples**:
- Headers only: `curl("https://target.com", "-I")`
- Follow redirects: `curl("https://target.com", "-L")`
- Ignore SSL: `curl("https://target.com", "-k")`

## Tool Selection Guide:
- Start with **nmap** for network mapping
- Use **dig** for DNS reconnaissance
- Apply **whois** for organizational intelligence  
- Employ **curl** for web application analysis

Remember: These tools are your eyes and ears. Use them systematically to build a complete picture of the target environment.
</reconnaissance_tools>
"""
