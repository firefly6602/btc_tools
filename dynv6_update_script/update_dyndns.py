import socket
import requests
import datetime
import smtplib
import subprocess
import netifaces
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_ipv6_address():
    # Check if the specific interface exists
    if "enp4s0" not in netifaces.interfaces():
        return None

    addrs = netifaces.ifaddresses("enp4s0")

    # Check if the interface has an IPv6 address
    if netifaces.AF_INET6 in addrs:
        for ipv6_info in addrs[netifaces.AF_INET6]:
            ipv6 = ipv6_info.get('addr')
            
            # Ensuring global scope and not a link-local address (starting with fe80)
            if not ipv6.startswith('fe80'):
                return ipv6

    return None

def get_external_ipv4_address():
    try:
        return requests.get('https://api.ipify.org').text
    except requests.exceptions.RequestException:
        return None


def get_ipv4(domain, dns_server):
    command = ["dig", "A", f"@{dns_server}", "+short", domain]
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        ipv4_addresses = result.stdout.strip().split("\n")
    else:
        ipv4_addresses = ['127.0.0.1']
    
    return ipv4_addresses[0]


def get_ipv6(domain, dns_server):
    command = ["dig", "AAAA", f"@{dns_server}", "+short", domain]
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        ipv6_addresses = result.stdout.strip().split("\n")
    else:
        ipv6_addresses = ['::1']
    
    return ipv6_addresses[0]


def main():
    domain = 'firefly3301.dynv6.net'
    token = 'J-X5PRoJxtSnA779P-AMw244bTYTL3'
    notify_email = 'dyndns@rcane.eu'
    timestamp = datetime.datetime.now()
    ipv6_prefix_length = "/64"

    ipv4_address_host = get_external_ipv4_address()
    ipv6_address_host = get_ipv6_address()
    ipv4_address_domain = get_ipv4(domain, '8.8.8.8')
    ipv6_address_domain = get_ipv6(domain, '2001:4860:4860::8888')

    important_update = False
    body = f"Address update:\n"
    body += f'Domain:                {domain}\n'
    body += f'Timestamp (UTC):       {timestamp}\n'
    
    if ipv4_address_host == None or ipv6_address_host == None:
        body += f'\nERROR: Could not host address!\n\n'
        important_update = True

    body += f'IPv4 address (Domain): {ipv4_address_domain}\n'
    body += f'IPv4 address (Host):   {ipv4_address_host}\n'
   
    result = 'no update'
    if ipv4_address_domain and ipv4_address_host and ipv4_address_domain != ipv4_address_host:
        result = requests.get(f'https://dynv6.com/api/update?hostname={domain}&token={token}&ipv4={ipv4_address_host}').text
        if result == 'invalid authentication token':
            body += f'\nERROR: invalid authentication token\n\n'
            important_update = True
        elif result == 'addresses unchanged' and important_update == False:
            important_update = False
        else: # Default setting for address updates
            important_update = True

    body += f'IPv4 status:           {result}\n'

    body += f'IPv6 address (Domain): {ipv6_address_domain}\n'
    body += f'IPv6 address (Host):   {ipv6_address_host+ipv6_prefix_length}\n'

    result = 'no update'
    if ipv6_address_domain and ipv6_address_host and ipv6_address_domain != ipv6_address_host:
        result = requests.get(f'https://dynv6.com/api/update?hostname={domain}&token={token}&ipv6={ipv6_address_host+ipv6_prefix_length}').text
        if result == 'invalid authentication token':
            body += f'\nERROR: invalid authentication token\n\n'
            important_update = True
        elif result == 'addresses unchanged' and important_update == False:
            important_update = False
        else: # Default setting for address updates
            important_update = True

    body += f'IPv6 status:           {result}'

    if important_update == True:
        # set up the SMTP server
        smtp_server = "smtp.strato.de"
        port = 587  # for TLS
        sender_email = "mail@rcane.eu"  # enter your address
        password = "ivNcoRHfLFid29f"  # enter your email password

        # set up the message parameters
        subject = f"DynDNS Update"

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = notify_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # send the email
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, notify_email, message.as_string())

        body += f'\nEmail sent!'

    print(body)

if __name__ == "__main__":
    main()
