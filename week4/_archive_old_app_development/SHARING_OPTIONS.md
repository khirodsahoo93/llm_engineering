# 🔐 Guide: Share Your App with Limited Access

## Quick Comparison

| Method | Setup | Security | User Experience | Cost |
|--------|-------|----------|-----------------|------|
| **Private HF Space** | ⭐ Easy | 🔒🔒🔒 High | Requires HF login | Free |
| **Single Password** | ⭐⭐ Medium | 🔒🔒 Medium | No account needed | Free |
| **Multiple Passwords** | ⭐⭐⭐ Hard | 🔒🔒🔒 High | No account needed | Free |
| **Gradio Share** | ⭐ Very Easy | 🔒 Low | No account needed | Free |

---

## Method 1: Private Hugging Face Space ✅ RECOMMENDED

### When to Use:
- Sharing with 2-10 colleagues
- Everyone has (or can create) a Hugging Face account
- You want the most secure option

### Setup Steps:

1. **Create Your Space:**
   ```
   Go to: https://huggingface.co/new-space
   Space name: python-cpp-optimizer
   SDK: Gradio
   Visibility: Private ← IMPORTANT!
   ```

2. **Upload Files:**
   - app.py
   - requirements.txt
   - README.md

3. **Add API Keys as Secrets:**
   - Settings → Repository secrets
   - Add: OPENAI_API_KEY
   - Add: ANTHROPIC_API_KEY

4. **Invite Your Team:**
   ```
   Settings → Member Management → Add member
   Enter their HF username
   Choose role: "read" (view only)
   ```

5. **Share the URL:**
   ```
   https://huggingface.co/spaces/YOUR-USERNAME/python-cpp-optimizer
   ```

### Pros:
- ✅ Most secure option
- ✅ Free forever
- ✅ Easy to add/remove people
- ✅ Full activity logs
- ✅ No password sharing

### Cons:
- ⚠️ Everyone needs a Hugging Face account (but it's free!)

---

## Method 2: Single Password Protection

### When to Use:
- Quick demos for clients
- Sharing with non-technical people
- Don't want to require account creation

### Setup Steps:

1. **Use the password-protected app:**
   ```bash
   cd /path/to/your/llm_engineering/week4
   # The file app_with_password.py is already created!
   ```

2. **Deploy to Hugging Face:**
   - Rename: `app_with_password.py` → `app.py`
   - Upload to HF Space (can be PUBLIC)
   - Add API keys as usual

3. **Add Password Secret:**
   ```
   Settings → Repository secrets
   Name: APP_PASSWORD
   Value: YourSecurePassword123
   ```

4. **Share with friends:**
   ```
   URL: https://huggingface.co/spaces/YOUR-USERNAME/python-cpp-optimizer
   Username: user
   Password: YourSecurePassword123
   ```

### Pros:
- ✅ No account needed
- ✅ Space can be public (discoverable)
- ✅ Simple for users

### Cons:
- ⚠️ Everyone shares the same password
- ⚠️ If password leaks, everyone has access
- ⚠️ Can't track who uses it

---

## Method 3: Multiple User Accounts

### When to Use:
- Need to know who accesses what
- Different permissions for different users
- Professional/enterprise use

### Implementation:

```python
# Add this to your app.py
USERS = {
    "alice": "password123",
    "bob": "securepass456",
    "charlie": "demo789",
}

# Store USERS as JSON in HF Secret: AUTHORIZED_USERS
import json
USERS = json.loads(os.environ.get("AUTHORIZED_USERS", "{}"))

# Use in launch:
app.launch(
    auth=lambda u, p: USERS.get(u) == p,
    auth_message="Enter your credentials"
)
```

### Setup on HF:
```
Settings → Repository secrets
Name: AUTHORIZED_USERS
Value: {"alice":"pass1","bob":"pass2","charlie":"pass3"}
```

### Pros:
- ✅ Individual credentials
- ✅ Can add/remove users anytime
- ✅ Better accountability

### Cons:
- ⚠️ More complex to manage
- ⚠️ Still shared passwords

---

## Method 4: Gradio Share Link (Temporary)

### When to Use:
- Quick demo during a call
- Testing before deploying
- One-time presentation

### How It Works:

1. **Run locally with share enabled:**
   ```python
   app.launch(share=True)
   ```

2. **Get temporary URL:**
   ```
   Running on local URL:  http://127.0.0.1:7860
   Running on public URL: https://abc123xyz.gradio.live ← Share this!
   ```

3. **Share the public URL** (valid for 72 hours)

### Pros:
- ✅ Instant sharing
- ✅ No deployment
- ✅ Perfect for demos

### Cons:
- ⚠️ Requires your computer to be on
- ⚠️ Expires in 72 hours
- ⚠️ Less secure (tunnels through Gradio servers)

---

## Recommended Setup for Your Use Case

### Scenario 1: Sharing with 2-3 Close Friends
**Use:** Private HF Space + Member invitations
```
Everyone creates free HF account → You invite them → They access anytime
```

### Scenario 2: Demo for Clients/Stakeholders  
**Use:** Password-protected public Space
```
Deploy app_with_password.py → Share URL + password → They access without signup
```

### Scenario 3: Quick Testing with 1 Person
**Use:** Gradio Share link
```
Run locally with share=True → Send them the link → Delete after demo
```

### Scenario 4: Personal Use Only
**Use:** Keep localhost or make Private with only you
```
No sharing needed → Just deploy privately
```

---

## Security Best Practices

### 1. For Password Protection:
- ✅ Use strong passwords (12+ chars, mixed case, numbers, symbols)
- ✅ Change password if someone leaves
- ✅ Don't share password in public channels
- ✅ Set API budget limits

### 2. For Private Spaces:
- ✅ Only invite people you trust
- ✅ Review member list regularly
- ✅ Use "read" permission unless they need to edit
- ✅ Remove members when they leave

### 3. For All Methods:
- ✅ Monitor API usage dashboards
- ✅ Set spending limits on OpenAI/Anthropic
- ✅ Check HF Space logs regularly
- ✅ Keep security warnings visible in UI

---

## Cost Monitoring

Even with limited sharing, monitor costs:

### OpenAI Dashboard:
```
https://platform.openai.com/usage
Set monthly limit: Settings → Billing → Usage limits
```

### Anthropic Dashboard:
```
https://console.anthropic.com/settings/limits
Set budget alerts
```

### Hugging Face:
```
Space Settings → Analytics
See usage patterns
```

---

## Quick Commands

### Switch to Password Protected Version:
```bash
cd /path/to/your/llm_engineering/week4
cp app.py app_original.py  # Backup
cp app_with_password.py app.py  # Use password version
```

### Switch Back to No Password:
```bash
cp app_original.py app.py
```

### Test Password Locally:
```bash
python app.py
# You'll be prompted for username (user) and password
```

---

## FAQ

**Q: Can I have both public and private versions?**
A: Yes! Create two separate Spaces:
- `python-cpp-optimizer-public` (password protected)
- `python-cpp-optimizer-private` (private space)

**Q: How do I change the password?**
A: Update the `APP_PASSWORD` secret in HF Settings → Factory reboot

**Q: Can users see each other's activity?**
A: No, Gradio sessions are isolated. Each user has their own session.

**Q: What if I forget to add the password secret?**
A: App will use default "demo123" - you'll see it in logs

**Q: Can I use OAuth (Google/GitHub login)?**
A: Gradio doesn't support OAuth natively. Use HF Private Space for that.

**Q: How many people can use it simultaneously?**
A: Depends on hardware:
- CPU Basic: 2-5 concurrent users
- CPU Upgrade: 10-20 concurrent users
- GPU: 20+ concurrent users

---

## Next Steps

1. **Decide your method** based on your needs
2. **Test locally** first
3. **Deploy to Hugging Face**
4. **Share with one person** first to test
5. **Then share with everyone**

Need help choosing? Consider:
- 🤝 **Trust level**: High → Private Space | Low → Password
- 👥 **Number of users**: <10 → Private | >10 → Password
- ⏰ **Duration**: Permanent → HF Space | Temporary → Share link
- 💼 **Professionalism**: High → Private Space | Demo → Password

---

**You're ready to share securely!** 🚀

