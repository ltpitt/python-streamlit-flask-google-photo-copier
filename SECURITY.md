# Security Policy

## Supported Versions

Currently, security updates are provided for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Security Features

### Authentication & Authorization

- **OAuth 2.0**: All Google Photos API access uses OAuth 2.0 with appropriate scopes:
  - Source accounts: Read-only access (`photoslibrary.readonly`)
  - Target accounts: Append-only access (`photoslibrary.appendonly`)
- **Credential Encryption**: OAuth tokens are encrypted at rest using Fernet (AES-128-CBC with HMAC)
- **Token Refresh**: Automatic refresh of expired OAuth tokens
- **Secure Storage**: Credentials stored in user's home directory (`~/.google_photos_sync/credentials/`)

### Input Validation

All user inputs are validated and sanitized:

- **Email Addresses**: Validated using Pydantic EmailStr
- **File Paths**: Sanitized to prevent path traversal attacks
- **JSON Payloads**: Validated for required fields and structure
- **Account Types**: Restricted to allowed values (`source`, `target`)
- **Integer Parameters**: Validated for positive values within allowed ranges
- **Boolean Parameters**: Validated and normalized

### Rate Limiting

- **API Rate Limiting**: Flask API endpoints are rate-limited to prevent abuse
- **Conservative Concurrency**: Maximum 3 concurrent photo transfers by default
- **Exponential Backoff**: Automatic retry with exponential backoff on rate limit errors

### Data Protection

- **No Credential Logging**: Sensitive data (tokens, secrets, passwords) never logged
- **Sanitized Error Messages**: Error responses don't expose internal details or credentials
- **Memory Efficiency**: Photos streamed, not loaded into memory (prevents memory dumps)
- **Secure Defaults**: Debug mode disabled in production, secure session keys required

### CSRF Protection

- **State Parameter**: OAuth flow uses state parameter for CSRF protection
- **CORS Configuration**: CORS restricted to allowed origins only

### Dependencies

All dependencies are:
- Pinned to specific versions for reproducibility
- Regularly updated to latest secure versions
- Scanned for known vulnerabilities using:
  - `bandit` (Python security linter)
  - GitHub Dependabot alerts
  - `pip-audit` (optional)

## Reporting a Vulnerability

**Please DO NOT report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities by email to:

**davide.nastri@gmail.com**

Please include the following information:

1. **Description**: Clear description of the vulnerability
2. **Steps to Reproduce**: Detailed steps to reproduce the issue
3. **Impact**: What an attacker could achieve by exploiting this vulnerability
4. **Proof of Concept**: Example code or screenshots demonstrating the issue (if applicable)
5. **Suggested Fix**: Your ideas on how to fix the vulnerability (optional but appreciated)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt within 48 hours
- **Initial Assessment**: We will provide an initial assessment within 5 business days
- **Status Updates**: We will keep you informed of progress towards a fix
- **Public Disclosure**: We will coordinate with you on public disclosure timing
- **Credit**: We will credit you in the security advisory (unless you prefer to remain anonymous)

### Disclosure Policy

- Security issues will be fixed as quickly as possible
- A security advisory will be published after the fix is released
- Users will be notified of critical security updates
- We follow responsible disclosure principles

## Security Best Practices for Users

### Production Deployment

1. **Environment Variables**:
   ```bash
   # Generate strong encryption key
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   
   # Set in .env file
   CREDENTIAL_ENCRYPTION_KEY=your_generated_key_here
   FLASK_SECRET_KEY=your_strong_random_secret_key_here
   ```

2. **Secret Management**:
   - Never commit `.env` file to version control
   - Use environment variables or secret management service (AWS Secrets Manager, HashiCorp Vault)
   - Rotate credentials regularly

3. **Network Security**:
   - Use HTTPS for all production deployments
   - Configure firewall to restrict access to API endpoints
   - Use reverse proxy (nginx, Apache) for production

4. **Access Control**:
   - Restrict file permissions on credentials directory:
     ```bash
     chmod 700 ~/.google_photos_sync/credentials/
     chmod 600 ~/.google_photos_sync/credentials/*.json
     ```
   - Run application with least-privilege user account
   - Don't run as root

5. **Monitoring**:
   - Monitor application logs for suspicious activity
   - Set up alerts for authentication failures
   - Review OAuth scopes granted to application

### Development

1. **Dependencies**:
   ```bash
   # Check for security vulnerabilities
   pip install bandit pip-audit
   bandit -r src/
   pip-audit
   ```

2. **Code Quality**:
   ```bash
   # Run security-focused linters
   ruff check . --select S  # Security checks
   mypy src/ --strict      # Type safety
   ```

3. **Testing**:
   - Test with malicious inputs
   - Verify input validation
   - Check for information leakage in error messages

## Known Security Considerations

### OAuth Token Storage

- Tokens are encrypted at rest using Fernet
- Encryption key must be kept secure (see Production Deployment above)
- If encryption key is compromised, rotate it and re-authenticate all accounts

### API Rate Limits

- Google Photos API has rate limits
- Application uses conservative concurrency (3 simultaneous requests)
- Aggressive use may trigger temporary bans from Google

### Scope Permissions

- Source account requires read-only scope (cannot modify photos)
- Target account requires append-only scope (cannot delete/modify existing photos)
- Review granted scopes periodically

### Local Credential Storage

- Credentials stored locally in `~/.google_photos_sync/credentials/`
- If computer is compromised, attacker may access credentials
- Consider using OS-level encryption (FileVault, BitLocker)

## Security Checklist for Deployment

- [ ] Set `CREDENTIAL_ENCRYPTION_KEY` to strong random value
- [ ] Set `FLASK_SECRET_KEY` to strong random value  
- [ ] Set `FLASK_ENV=production`
- [ ] Disable debug mode (`FLASK_DEBUG=false`)
- [ ] Configure CORS for production domain
- [ ] Enable HTTPS/TLS
- [ ] Restrict file permissions on credentials directory
- [ ] Set up application monitoring and logging
- [ ] Configure firewall rules
- [ ] Review OAuth scopes granted
- [ ] Regular dependency updates
- [ ] Regular security audits

## Compliance

This application:
- Follows OWASP Top 10 security best practices
- Uses industry-standard encryption (AES-128-CBC, HMAC)
- Implements OAuth 2.0 per RFC 6749
- Follows principle of least privilege
- Validates all user inputs
- Sanitizes all outputs

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Google OAuth 2.0 Security](https://developers.google.com/identity/protocols/oauth2/production-readiness)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Flask Security Considerations](https://flask.palletsprojects.com/en/latest/security/)

## Contact

For security concerns, please contact: **davide.nastri@gmail.com**

For general issues, please use [GitHub Issues](https://github.com/ltpitt/python-streamlit-flask-google-photo-copier/issues).

---

**Last Updated**: January 2026  
**Version**: 0.1.0
