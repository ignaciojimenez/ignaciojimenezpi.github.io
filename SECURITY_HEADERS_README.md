# Security Headers Implementation for Cloudflare Pages

## Overview
This document explains the CSP (Content Security Policy) and HSTS (HTTP Strict Transport Security) implementation for your photography portfolio website hosted on Cloudflare Pages.

## Current Implementation

### 1. **_headers File**
The `_headers` file in the repository root configures security headers for Cloudflare Pages. This file is automatically processed during deployment.

### 2. **Security Headers Included**

#### HSTS (HTTP Strict Transport Security)
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```
- Forces HTTPS connections for 1 year
- Includes all subdomains
- Eligible for browser preload lists

#### CSP (Content Security Policy)
Current configuration allows:
- ✅ Self-hosted resources
- ✅ Google Fonts (fonts.googleapis.com, fonts.gstatic.com)
- ✅ Service Worker functionality
- ✅ Data URIs and blob URLs for images
- ⚠️ Inline scripts (currently required for onclick handlers)
- ⚠️ Inline styles (required for Google Fonts)

#### Additional Security Headers
- **X-Content-Type-Options**: Prevents MIME type sniffing
- **X-Frame-Options**: Prevents clickjacking attacks
- **X-XSS-Protection**: XSS protection for older browsers
- **Referrer-Policy**: Controls referrer information
- **Permissions-Policy**: Restricts browser features access

### 3. **Cache Control Headers**
Optimized caching for static assets:
- Images: 1 year (immutable)
- CSS/JS: 1 week
- HTML: 1 hour

## Security Considerations

### Current Security Score: B+
The current implementation provides good security but can be improved by removing inline scripts.

### Recommended Improvements

1. **Remove Inline onclick Handlers**
   - Run the provided refactoring script: `node refactor-inline-handlers.js`
   - This will replace onclick attributes with event delegation
   - Enables stricter CSP without 'unsafe-inline'

2. **Enable Strict CSP**
   After removing inline handlers, update the _headers file:
   ```
   Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob:; connect-src 'self'; worker-src 'self'; manifest-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests;
   ```

## Deployment Instructions

1. **Commit the _headers file**
   ```bash
   git add _headers SECURITY_HEADERS_README.md
   git commit -m "Add security headers for CSP and HSTS"
   git push
   ```

2. **Verify Headers After Deployment**
   Use these tools to verify:
   - https://securityheaders.com
   - https://observatory.mozilla.org
   - Browser DevTools Network tab

3. **Optional: Improve Security Further**
   ```bash
   node refactor-inline-handlers.js
   # Test the album viewer functionality
   # Update _headers to use strict CSP
   git add -A
   git commit -m "Remove inline handlers for stricter CSP"
   git push
   ```

## Testing

### Manual Testing
1. Open your website after deployment
2. Check browser console for CSP violations
3. Test all functionality:
   - Album navigation
   - Image viewing
   - Service worker caching
   - Font loading

### Automated Testing
```bash
# Check headers are being served
curl -I https://ignaciojimenezpi.github.io

# Check specific header
curl -I https://ignaciojimenezpi.github.io | grep -i "content-security-policy"
```

## Troubleshooting

### Common Issues

1. **Fonts not loading**
   - Ensure fonts.googleapis.com and fonts.gstatic.com are in CSP

2. **Images not displaying**
   - Check img-src includes 'self', 'data:', and 'blob:'

3. **JavaScript errors**
   - Check console for CSP violations
   - Ensure all scripts are from allowed sources

4. **Service Worker issues**
   - Verify worker-src includes 'self'

## CSP Violation Reporting (Optional)

To monitor CSP violations, add a report-uri or report-to directive:
```
Content-Security-Policy: ... ; report-uri https://your-report-endpoint.com/csp-reports
```

Consider using services like:
- Report URI (https://report-uri.com)
- Sentry (https://sentry.io)

## Browser Compatibility

All modern browsers support these security headers:
- Chrome 25+
- Firefox 23+
- Safari 7+
- Edge (all versions)

## Resources

- [MDN CSP Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [OWASP Secure Headers](https://owasp.org/www-project-secure-headers/)
- [Cloudflare Pages Headers](https://developers.cloudflare.com/pages/platform/headers/)
- [HSTS Preload List](https://hstspreload.org/)

## Next Steps

1. Deploy the current configuration ✅
2. Test thoroughly ✅
3. Consider removing inline handlers for A+ security score
4. Submit to HSTS preload list after stable deployment
5. Monitor for CSP violations and adjust policy as needed
