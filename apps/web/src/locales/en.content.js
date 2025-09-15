export default {
  ssl_certificate_installation: `
# Installing the Security Certificate

To ensure secure access to our platform, please follow the steps below for your specific device or browser.

---

## For Android Devices

1. **Download the Certificate**
    - Tap the link below to download the certificate:
        [Download Certificate]({download_certificate_link})

2. **Install the Certificate**
    - Open **Settings** → **Security** → **Encryption & credentials** (or **Security & location**).
    - Tap **Install a certificate** → **CA certificate** → **Install anyway**.
    - Select the downloaded 'selfsigned.crt' from your **Downloads** folder.

3. **Confirm Installation**
    - If prompted, set a screen lock.
    - A confirmation message will appear once installed.

4. **Restart Your Device**
    - Restart your device to apply the changes.

---

## For iPhone and iPad (iOS)

1. **Download the Certificate**
    - Open **Safari** on your device.
    - Tap the link below to download the certificate:
        [Download Certificate]({download_certificate_link})

2. **Install the Profile**
    - When prompted, tap **Allow**.
    - A message will confirm: *"Profile Downloaded."*

3. **Install the Certificate**
    - Go to **Settings** → **Profile Downloaded** (or **Settings** → **General** → **VPN & Device Management**).
    - Tap the profile and tap **Install**.
    - Enter your passcode if prompted, then tap **Install** again.

4. **Trust the Certificate**
    - Go to **Settings** → **General** → **About** → **Certificate Trust Settings**.
    - Under **Enable Full Trust for Root Certificates**, toggle the certificate to **On** and confirm.

5. **Restart Your Device**
    - Restart your device to apply the changes.

---

## For Windows Computers

1. **Download the Certificate**
    - Click the link below to download the certificate:
        [Download Certificate]({download_certificate_link})

2. **Install the Certificate**
    - Double-click 'selfsigned.crt'.
    - Click **Install Certificate**.
    - Choose **Local Machine** and click **Next**.
    - If prompted, click **Yes** to allow changes.
    - Select **Place all certificates in the following store**, click **Browse**, choose **Trusted Root Certification Authorities**, then click **Next** and **Finish**.

3. **Confirm Installation**
    - If a security warning appears, click **Yes**.

4. **Restart Your Browser**
    - Close all browser windows and reopen your browser.

---

## For macOS Computers

1. **Download the Certificate**
    - Click the link below to download the certificate:
        [Download Certificate]({download_certificate_link})

2. **Add the Certificate to Keychain**
    - In **Finder**, double-click the downloaded 'selfsigned.crt' file.
    - It will open in **Keychain Access**.

3. **Trust the Certificate**
    - In **Keychain Access**, locate the certificate (usually in the **System** or **login** keychain).
    - Double-click the certificate, expand **Trust**.
    - Set **When using this certificate** to **Always Trust**.
    - Enter your administrator password if prompted.

4. **Restart Your Browser**
    - Close all browser windows and reopen your browser.

---

## For Google Chrome (Linux)

1. **Download the Certificate**
    - Click the link below to download the certificate:
        [Download Certificate]({download_certificate_link})

2. **Open the Certificate Manager**
    - Open Chrome and navigate to chrome://settings/certificates.

3. **Import the Certificate**
    - Go to the **Authorities** tab and click **Import**.
    - Select the downloaded certificate file ('selfsigned.crt').
    - In the dialog, check:
    - "Trust this certificate for identifying websites."
    - "Trust this certificate for identifying email users."
    - Click **OK** to confirm.

4. **Restart Chrome**
    - Close and reopen Chrome to apply the changes.

---

## Troubleshooting Tips
- **Certificate Not Trusted**: Ensure the certificate is installed in the correct certificate store (e.g., **Trusted Root Certification Authorities** on Windows).
- **Security Warnings Still Appear**: Clear your browser cache and restart your device.
`,
}
