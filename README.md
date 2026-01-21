# GhostPairing Attack Lab with Browser Automation

A complete GhostPairing attack simulation lab with **real browser automation** that demonstrates actual WhatsApp account hijacking techniques.

## 🎯 What This Lab Does

This lab simulates a **real GhostPairing attack** using browser automation:

1. **Victim** enters phone number on phishing page
2. **Firefox automation** opens to real web.whatsapp.com
3. **Automation** enters victim's phone number in WhatsApp Web
4. **WhatsApp** sends REAL verification code to victim's phone
5. **Victim** enters code on phishing page
6. **Automation** captures code and enters it in WhatsApp Web
7. **Account hijacked** - Attacker's browser is now paired with victim's WhatsApp

## ⚠️ CRITICAL LEGAL & ETHICAL WARNINGS

**FOR AUTHORIZED SECURITY RESEARCH AND EDUCATION ONLY**

- **ONLY** test with phone numbers **YOU OWN**
- **NEVER** use against non-consenting individuals
- This performs **REAL WhatsApp pairing** - actual account access
- Violation of computer fraud laws is a serious crime
- Use only in controlled, authorized environments

## 🚀 Quick Start

### 1. Installation
```bash
# Clone repository
git clone https://www.github.com/valITino/ghostpairing-lab

# go to the cloned directory
cd ghostpairing-lab

# Make scripts executable
chmod +x *.sh

# Run setup (installs Firefox, Playwright, dependencies)
./setup.sh
# Wait for installation
```

### 2. Run the Lab
```bash
./run.sh
```

Choose mode:
- **Local Only**: Test on localhost:8000
- **Public Tunnel**: Expose via cloudflared (for authorized testing only)

## 📊 Monitoring

Access the admin dashboard at `http://localhost:8000/admin` to see real-time attack monitoring.

---

**Remember**: This is a live attack tool. Use responsibly and only on systems you own.
